"""The declarative document spec. Adding a bank means writing a spec, not code.

A spec names the locale, the currency, the columns, the invariants that apply, how much
budget each tier may spend, and what the acceptance policy is. Nothing in the spec is
executable: the invariant ids map onto the fixed, audited implementations in
:mod:`probity.invariants`, so a spec can never smuggle in arbitrary code.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

import yaml

from .money import Locale, get_locale, minor_units


@dataclass(frozen=True)
class ColumnSpec:
    """Which columns the layout has, which decides which invariants are even possible."""

    # "debit_credit"     two columns, the column decides the direction
    # "signed_amount"    one column, the sign or marker decides the direction
    # "amount_direction" one amount column plus a separate Cr/Dr indicator column
    mode: str = "debit_credit"
    has_running_balance: bool = True
    has_page_carry_forward: bool = False
    sort_order: str = "ascending"   # "ascending" | "descending"

    MODES = ("debit_credit", "signed_amount", "amount_direction")

    def __post_init__(self) -> None:
        if self.mode not in self.MODES:
            raise ValueError(f"columns.mode must be one of {self.MODES}, got {self.mode!r}")
        if self.sort_order not in {"ascending", "descending"}:
            raise ValueError(f"columns.sort_order must be ascending or descending, got {self.sort_order!r}")


@dataclass(frozen=True)
class AcceptancePolicy:
    """What ACCEPT means. Tightening this is how the risk-coverage curve is swept."""

    require_all_invariants: bool = True
    require_grounding_on: tuple[str, ...] = ("amount", "date")   # field classes
    min_grounded_fraction: float = 1.0
    allow_inferred_fields: bool = False
    max_unverified_rows: int = 0
    # Header fields that must be present and readable before a document is accepted.
    # Without this, a reading that simply failed to find the period could be accepted:
    # the grounding engine skips values that are missing, and DATE_ORDER treats absent
    # period boundaries as "nothing to check". Absence has to be a refusal, not a pass.
    require_header_fields: tuple[str, ...] = (
        "opening_balance", "closing_balance", "period_start", "period_end")


@dataclass(frozen=True)
class TierBudget:
    """Cheapest method first (P7), with a hard stop per tier (P5)."""

    tier: str
    max_calls: int = 0
    max_regions: int = 0


@dataclass
class DocumentSpec:
    doc_type: str
    locale_name: str
    currency_default: str
    invariant_ids: tuple[str, ...]
    columns: ColumnSpec = dc_field(default_factory=ColumnSpec)
    acceptance: AcceptancePolicy = dc_field(default_factory=AcceptancePolicy)
    tier_order: tuple[str, ...] = ("text_layer", "template", "ocr", "llm_small", "llm_large")
    budgets: dict[str, TierBudget] = dc_field(default_factory=dict)
    repair_budget_per_region: int = 2
    max_repair_regions: int = 8
    grounding_iou_min: float = 0.25
    date_format: str | None = None
    # Real statements print the period in the header one way and date their rows
    # another ("From 01 Jan 2024" above a table of "01-01-2024"). One format for both
    # makes the header unreadable, and a parser that guesses would produce a plausible
    # wrong date, so the two are declared separately.
    header_date_format: str | None = None
    template_id: str | None = None
    layout_hints: dict[str, Any] = dc_field(default_factory=dict)
    version: str = "0"

    @property
    def locale(self) -> Locale:
        return get_locale(self.locale_name)

    @property
    def date_fmt(self) -> str:
        return self.date_format or self.locale.date_format

    @property
    def header_date_fmt(self) -> str:
        return self.header_date_format or self.date_fmt

    @property
    def exponent(self) -> int:
        return minor_units(self.currency_default)

    def fingerprint(self) -> str:
        """A hash of the spec, stamped into every certificate so a result is tied to
        the exact rules that produced it."""
        payload = json.dumps(self.to_json(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def to_json(self) -> dict[str, Any]:
        return {
            "doc_type": self.doc_type,
            "locale": self.locale_name,
            "currency_default": self.currency_default,
            "invariants": list(self.invariant_ids),
            "columns": vars(self.columns),
            "acceptance": {
                **vars(self.acceptance),
                "require_grounding_on": list(self.acceptance.require_grounding_on),
                "require_header_fields": list(self.acceptance.require_header_fields)},
            "tier_order": list(self.tier_order),
            "budgets": {k: vars(v) for k, v in sorted(self.budgets.items())},
            "repair_budget_per_region": self.repair_budget_per_region,
            "max_repair_regions": self.max_repair_regions,
            "grounding_iou_min": self.grounding_iou_min,
            "date_format": self.date_fmt,
            "header_date_format": self.header_date_fmt,
            "template_id": self.template_id,
            "layout_hints": self.layout_hints,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentSpec":
        from .invariants import REGISTRY as INVARIANT_REGISTRY

        unknown = set(data) - {
            "doc_type", "locale", "currency_default", "invariants", "columns", "acceptance",
            "tier_order", "budgets", "repair_budget_per_region", "max_repair_regions",
            "grounding_iou_min", "date_format", "header_date_format", "template_id",
            "layout_hints", "version",
        }
        if unknown:
            raise ValueError(f"unknown keys in spec: {sorted(unknown)}")

        ids = tuple(data.get("invariants", ()))
        bad = [i for i in ids if i not in INVARIANT_REGISTRY]
        if bad:
            raise ValueError(f"unknown invariant ids {bad}; known: {sorted(INVARIANT_REGISTRY)}")

        acc = dict(data.get("acceptance", {}) or {})
        for k in ("require_grounding_on", "require_header_fields"):
            if k in acc:
                acc[k] = tuple(acc[k])

        budgets = {
            k: TierBudget(tier=k, **v) for k, v in (data.get("budgets", {}) or {}).items()
        }
        spec = cls(
            doc_type=data["doc_type"],
            locale_name=data["locale"],
            currency_default=data["currency_default"],
            invariant_ids=ids,
            columns=ColumnSpec(**(data.get("columns", {}) or {})),
            acceptance=AcceptancePolicy(**acc),
            tier_order=tuple(data.get("tier_order", DocumentSpec.tier_order)),
            budgets=budgets,
            repair_budget_per_region=data.get("repair_budget_per_region", 2),
            max_repair_regions=data.get("max_repair_regions", 8),
            grounding_iou_min=data.get("grounding_iou_min", 0.25),
            date_format=data.get("date_format"),
            header_date_format=data.get("header_date_format"),
            template_id=data.get("template_id"),
            layout_hints=data.get("layout_hints", {}) or {},
            version=str(data.get("version", "0")),
        )
        spec.validate()
        return spec

    @classmethod
    def load(cls, path: str | Path) -> "DocumentSpec":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def validate(self) -> None:
        """Refuse a spec that promises checks its own layout cannot support.

        A statement without a running balance column simply cannot be verified row by
        row. Saying so at load time is better than discovering it as a document that
        quietly passes with the weakest possible evidence.
        """
        if not self.columns.has_running_balance and "ROW_BAL" in self.invariant_ids:
            raise ValueError(
                "ROW_BAL requires columns.has_running_balance: true. Without a running "
                "balance the strongest available check is GLOBAL_BAL; declare that "
                "instead and expect a lower verification level."
            )
        if self.columns.mode == "signed_amount" and "ROW_BAL" in self.invariant_ids:
            # Allowed, but the sign comes from the single column, so the derivation
            # policy must be explicit about it.
            pass
        if self.columns.has_page_carry_forward is False and "PAGE_SUBTOTAL" in self.invariant_ids:
            raise ValueError("PAGE_SUBTOTAL requires columns.has_page_carry_forward: true")
        if not (0.0 <= self.acceptance.min_grounded_fraction <= 1.0):
            raise ValueError("acceptance.min_grounded_fraction must be in [0, 1]")
        for tier in self.tier_order:
            if tier not in {"text_layer", "template", "ocr", "llm_small", "llm_large"}:
                raise ValueError(f"unknown tier {tier!r}")

    def verification_level(self) -> str:
        """How strong the guarantee can be for this layout, before any document is read.

        Printed in the certificate so a consumer is never told "verified" without
        knowing what the layout allowed us to verify.
        """
        if "ROW_BAL" in self.invariant_ids and self.columns.has_running_balance:
            return "ROW_LEVEL"
        if "PAGE_SUBTOTAL" in self.invariant_ids:
            return "PAGE_LEVEL"
        if "GLOBAL_BAL" in self.invariant_ids:
            return "DOCUMENT_LEVEL"
        return "GROUNDING_ONLY"
