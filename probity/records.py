"""The typed records a proposer fills in and a verifier judges.

Every value carries three things that the rest of the framework routes on:

``provenance``   how the value was obtained (text layer, OCR, a named model)
``bbox``         where on the page it was read, in PDF points
``verified_by``  which independent checks have confirmed it

Principle P3 lives here: ``verified_by`` may never contain the same invariant that
``provenance`` says produced the value. :meth:`Field.status` enforces it, which is why a
value inferred from a balance difference can reach ``INFERRED`` but never ``VERIFIED``.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field as dc_field
from datetime import date
from typing import Any

from .money import Money


class Status(enum.StrEnum):
    VERIFIED = "VERIFIED"      # grounded on the page and confirmed by an independent check
    INFERRED = "INFERRED"      # derived from other values; cannot be its own witness
    UNVERIFIED = "UNVERIFIED"  # read but not confirmed by anything
    FAILED = "FAILED"          # could not be read at all


class Provenance(enum.StrEnum):
    TEXT_LAYER = "text_layer"
    TEMPLATE = "template"
    OCR = "ocr"
    LLM = "llm"
    DERIVED = "derived"         # produced by an invariant, not read from the page
    MISSING = "missing"


@dataclass(frozen=True)
class BBox:
    """A rectangle in PDF points, origin at the top-left of the page."""

    page: int
    x0: float
    y0: float
    x1: float
    y1: float

    def area(self) -> float:
        return max(0.0, self.x1 - self.x0) * max(0.0, self.y1 - self.y0)

    def intersection(self, other: "BBox") -> float:
        if other.page != self.page:
            return 0.0
        dx = min(self.x1, other.x1) - max(self.x0, other.x0)
        dy = min(self.y1, other.y1) - max(self.y0, other.y0)
        return dx * dy if dx > 0 and dy > 0 else 0.0

    def iou(self, other: "BBox") -> float:
        inter = self.intersection(other)
        union = self.area() + other.area() - inter
        return inter / union if union > 0 else 0.0

    def contains_centre_of(self, other: "BBox") -> bool:
        if other.page != self.page:
            return False
        cx, cy = (other.x0 + other.x1) / 2, (other.y0 + other.y1) / 2
        return self.x0 <= cx <= self.x1 and self.y0 <= cy <= self.y1

    def to_json(self) -> dict[str, Any]:
        return {"page": self.page, "x0": round(self.x0, 2), "y0": round(self.y0, 2),
                "x1": round(self.x1, 2), "y1": round(self.y1, 2)}


@dataclass
class Field:
    """One extracted value plus everything known about where it came from."""

    name: str
    raw: str | None = None                      # the characters as read from the source
    value: Money | date | str | int | None = None
    provenance: Provenance = Provenance.MISSING
    bbox: BBox | None = None
    source_model: str | None = None             # e.g. "llm:google/gemini-3.1-flash-lite"
    verified_by: list[str] = dc_field(default_factory=list)
    grounded: bool | None = None
    grounding_detail: dict[str, Any] = dc_field(default_factory=dict)
    error_code: str | None = None               # parse failure reason, if any
    model_confidence: float | None = None       # logged, never used as a gate (P4)

    @property
    def status(self) -> Status:
        if self.value is None:
            return Status.FAILED
        if self.provenance is Provenance.DERIVED:
            # P3: a derived value cannot be verified by the invariant that derived it,
            # and we have nothing else, so it stays INFERRED whatever else passed.
            return Status.INFERRED
        if self.grounded and self.verified_by:
            return Status.VERIFIED
        return Status.UNVERIFIED

    def to_json(self) -> dict[str, Any]:
        v = self.value
        return {
            "name": self.name,
            "raw": self.raw,
            "value": (v.minor if isinstance(v, Money) else v.isoformat() if isinstance(v, date) else v),
            "currency": v.currency if isinstance(v, Money) else None,
            "display": str(v) if v is not None else None,
            "status": str(self.status),
            "provenance": str(self.provenance),
            "source_model": self.source_model,
            "bbox": self.bbox.to_json() if self.bbox else None,
            "grounded": self.grounded,
            "grounding_detail": self.grounding_detail or None,
            "verified_by": list(self.verified_by),
            "error_code": self.error_code,
            "model_confidence": self.model_confidence,
        }


@dataclass
class Row:
    """One transaction line."""

    index: int
    page: int = 1
    date: Field = dc_field(default_factory=lambda: Field("date"))
    description: Field = dc_field(default_factory=lambda: Field("description"))
    debit: Field = dc_field(default_factory=lambda: Field("debit"))
    credit: Field = dc_field(default_factory=lambda: Field("credit"))
    balance: Field = dc_field(default_factory=lambda: Field("balance"))

    def fields(self) -> list[Field]:
        return [self.date, self.description, self.debit, self.credit, self.balance]

    def signed_amount(self, currency: str) -> Money | None:
        """credit - debit, as an exact Money, or None if the movement is not readable.

        An *empty* amount cell is not an unreadable one, and the difference decides
        whether a row can be checked at all.

        Every ordinary row already relies on this: a row with a debit has a blank credit
        cell, and that blank is read as zero, which is the only way the row check can run.
        Treating a row whose *both* cells are blank as unreadable was therefore
        inconsistent with the line above it -- the same absence of ink meaning zero in one
        place and unknown in the other. Such rows are real: 277 of the 32,349 rows in the
        external corpus print a date, a description and a balance with no amount at all,
        and they appear in 150 of its 200 documents.

        So blank on both sides reads as no movement. This is not a weakening: if the
        reading were wrong, ``ROW_BAL`` fails on that row with a MISMATCH and localises
        it, which is the whole mechanism. What stays unreadable is a cell with **ink that
        did not parse** -- there the characters are present and their value is genuinely
        unknown, and refusing is the only safe answer.
        """
        c = self.credit.value if isinstance(self.credit.value, Money) else None
        d = self.debit.value if isinstance(self.debit.value, Money) else None
        if c is None and d is None:
            printed = [f for f in (self.debit, self.credit)
                       if (f.raw or "").strip() or f.error_code]
            if printed:
                return None
            return Money.zero(currency)
        total = Money.zero(currency)
        if c is not None:
            total = total + c
        if d is not None:
            total = total - d
        return total

    def to_json(self) -> dict[str, Any]:
        return {"index": self.index, "page": self.page,
                **{f.name: f.to_json() for f in self.fields()}}


@dataclass
class Header:
    account_id: Field = dc_field(default_factory=lambda: Field("account_id"))
    period_start: Field = dc_field(default_factory=lambda: Field("period_start"))
    period_end: Field = dc_field(default_factory=lambda: Field("period_end"))
    opening_balance: Field = dc_field(default_factory=lambda: Field("opening_balance"))
    closing_balance: Field = dc_field(default_factory=lambda: Field("closing_balance"))
    currency: Field = dc_field(default_factory=lambda: Field("currency"))
    tx_count: Field = dc_field(default_factory=lambda: Field("tx_count"))

    def fields(self) -> list[Field]:
        return [self.account_id, self.period_start, self.period_end, self.opening_balance,
                self.closing_balance, self.currency, self.tx_count]

    def to_json(self) -> dict[str, Any]:
        return {f.name: f.to_json() for f in self.fields()}


@dataclass
class Statement:
    """A candidate reading of one document. Proposers produce these; verifiers judge them."""

    doc_id: str
    currency: str
    header: Header = dc_field(default_factory=Header)
    rows: list[Row] = dc_field(default_factory=list)
    page_count: int = 1
    carried_forward: dict[int, Field] = dc_field(default_factory=dict)
    notes: list[str] = dc_field(default_factory=list)

    def all_fields(self) -> list[Field]:
        out = list(self.header.fields())
        for row in self.rows:
            out.extend(row.fields())
        out.extend(self.carried_forward.values())
        return out

    def rows_on_page(self, page: int) -> list[Row]:
        return [r for r in self.rows if r.page == page]

    def copy(self) -> "Statement":
        import copy as _copy
        return _copy.deepcopy(self)

    def to_json(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "currency": self.currency,
            "page_count": self.page_count,
            "header": self.header.to_json(),
            "rows": [r.to_json() for r in self.rows],
            "carried_forward": {str(k): v.to_json() for k, v in self.carried_forward.items()},
            "notes": list(self.notes),
        }

    def to_simple(self) -> dict[str, Any]:
        """The flat shape used for comparison against ground truth and for exports."""
        def val(f: Field):
            v = f.value
            if isinstance(v, Money):
                return v.minor
            if isinstance(v, date):
                return v.isoformat()
            return v
        return {
            "account_id": val(self.header.account_id),
            "period_start": val(self.header.period_start),
            "period_end": val(self.header.period_end),
            "opening_balance": val(self.header.opening_balance),
            "closing_balance": val(self.header.closing_balance),
            "tx_count": val(self.header.tx_count),
            "rows": [
                {"date": val(r.date), "description": val(r.description),
                 "debit": val(r.debit), "credit": val(r.credit), "balance": val(r.balance)}
                for r in self.rows
            ],
        }
