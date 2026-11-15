"""The verification certificate: what a lender or auditor actually consumes.

A certificate is not a confidence score. It is a statement of what was checked, what
each check concluded, and where every accepted value is printed, with a
``verification_level`` that says how strong the guarantee could be *for this layout* —
so a card statement with no running balance is never presented with the same authority
as one that checks itself row by row.

It also records what is *not* claimed. ``undetectable_classes`` names the error families
no invariant and no grounding check can catch, because a certificate that implies
otherwise is worse than no certificate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timezone
from typing import Any

from .machine import TERMINAL_MEANING, State
from .records import Field, Statement, Status

UNDETECTABLE = [
    {"class": "balanced_tamper",
     "description": "an amount altered together with every later balance, so the "
                    "document remains internally exact and every value is printed on "
                    "the page",
     "why": "the invariants check internal consistency and grounding checks presence; "
            "neither has access to the transactions that really happened"},
    {"class": "omitted_rows_netting_to_zero",
     "description": "a set of transactions removed from the reading whose amounts "
                    "cancel, leaving every remaining balance consistent",
     "why": "the checks run over the rows that were returned; nothing audits the page "
            "for rows that were never read. COUNT catches this only when the statement "
            "declares a transaction count"},
    {"class": "coherent_ocr_misreading",
     "description": "on a scanned page, a transcription that is internally consistent "
                    "but wrong",
     "why": "grounding confirms a value against the evidence available for that page, "
            "which for a scan is the OCR transcription itself; without a second, "
            "independent source it is a consistency check rather than a presence check"},
    {"class": "wholesale_forgery",
     "description": "a statement fabricated in full from a consistent ledger",
     "why": "only an out-of-band check against the bank can detect this"},
]


@dataclass
class Certificate:
    doc_id: str
    doc_sha256: str
    spec_fingerprint: str
    spec_doc_type: str
    framework_version: str
    final_state: str
    verification_level: str
    accepted: bool
    issued_at: str
    invariants: dict[str, Any] = dc_field(default_factory=dict)
    grounding: dict[str, Any] = dc_field(default_factory=dict)
    fields: list[dict[str, Any]] = dc_field(default_factory=list)
    rows: list[dict[str, Any]] = dc_field(default_factory=list)
    flags: list[dict[str, Any]] = dc_field(default_factory=list)
    tiers_used: list[str] = dc_field(default_factory=list)
    model_calls: list[dict[str, Any]] = dc_field(default_factory=list)
    cost_usd: float = 0.0
    transition_path: list[str] = dc_field(default_factory=list)
    replay_hash: str = ""
    review_targets: list[dict[str, Any]] = dc_field(default_factory=list)
    conclusion: str = "UNRESOLVED"
    conclusion_reason: str = ""
    inconsistent_rows: list[int] = dc_field(default_factory=list)
    corrections: list[dict[str, Any]] = dc_field(default_factory=list)
    opinions: list[dict[str, Any]] = dc_field(default_factory=list)
    undetectable_classes: list[dict[str, Any]] = dc_field(default_factory=lambda: list(UNDETECTABLE))

    def to_json(self) -> dict[str, Any]:
        return {
            "protocol": "probity/certificate-v1",
            "document": {"doc_id": self.doc_id, "sha256": self.doc_sha256},
            "spec": {"fingerprint": self.spec_fingerprint, "doc_type": self.spec_doc_type},
            "framework_version": self.framework_version,
            "issued_at": self.issued_at,
            "outcome": {
                "final_state": self.final_state,
                "accepted": self.accepted,
                "meaning": TERMINAL_MEANING.get(State(self.final_state), ""),
                "verification_level": self.verification_level,
                # CONFIRMED | DOCUMENT_INCONSISTENT | UNRESOLVED. The middle one means
                # the statement was read correctly and does not add up.
                "conclusion": self.conclusion,
                "conclusion_reason": self.conclusion_reason,
                "inconsistent_rows": list(self.inconsistent_rows),
            },
            # Values the first reader got wrong and a second reader put right, each
            # with both readings and the rule that confirmed the correction.
            "corrections": self.corrections,
            "second_opinions": self.opinions,
            "invariants": self.invariants,
            "grounding": self.grounding,
            "header_fields": self.fields,
            "rows": self.rows,
            "flags": self.flags,
            "review_targets": self.review_targets,
            "provenance": {
                "tiers_used": self.tiers_used,
                "model_calls": self.model_calls,
                "cost_usd": round(self.cost_usd, 6),
                "transition_path": self.transition_path,
                "replay_hash": self.replay_hash,
            },
            "not_claimed": self.undetectable_classes,
        }

    def dumps(self, indent: int = 1) -> str:
        return json.dumps(self.to_json(), indent=indent, ensure_ascii=False, default=str)

    def summary(self) -> str:
        n_ver = sum(1 for f in self.fields + [c for r in self.rows for c in r["fields"]]
                    if f["status"] == "VERIFIED")
        n_all = len(self.fields) + sum(len(r["fields"]) for r in self.rows)
        head = "ACCEPTED" if self.accepted else self.final_state
        lines = [f"{self.doc_id}: {self.conclusion or head}",
                 f"  {self.conclusion_reason}" if self.conclusion_reason else
                 f"  {head} at {self.verification_level}",
                 f"  {n_ver}/{n_all} fields VERIFIED; "
                 f"{self.invariants.get('passed', 0)}/{self.invariants.get('total', 0)} "
                 f"invariant checks passed",
                 f"  {len(self.tiers_used)} tier(s) used, ${self.cost_usd:.5f}"]
        fixed = sorted({c["row"] for c in self.corrections})
        if fixed:
            lines.append(f"  {len(fixed)} row(s) corrected: "
                         f"{fixed[:12]}{' ...' if len(fixed) > 12 else ''}")
        for flag in self.flags:
            lines.append(f"  FLAG {flag['code']}: {flag['message']}")
        for t in self.review_targets[:5]:
            lines.append(f"  REVIEW {t['location']}: {t['reason']}")
        return "\n".join(lines)


def _field_json(f: Field) -> dict[str, Any]:
    d = f.to_json()
    return {k: d[k] for k in ("name", "display", "value", "currency", "status",
                              "provenance", "source_model", "bbox", "grounded",
                              "verified_by", "error_code", "model_confidence")}


def _tiers_used(trace) -> list[str]:
    """Every tier that actually read something, in order, starting with the first."""
    out: list[str] = []
    for ev in trace.events:
        tier = None
        if ev.kind.value == "extraction":
            tier = ev.data.get("tier")
        elif ev.kind.value == "tier_change":
            tier = ev.data.get("new_tier")
        if tier and (not out or out[-1] != tier):
            out.append(tier)
    return out


def build_certificate(*, statement: Statement, spec, trace, inv_report, gr_report,
                      final_state: State, doc_sha256: str, version: str,
                      flags: list[dict[str, Any]] | None = None) -> Certificate:
    from .invariants import Scope

    inv_counts = inv_report.by_invariant() if inv_report else {}
    total = sum(v["pass"] + v["fail"] for v in inv_counts.values())
    passed = sum(v["pass"] for v in inv_counts.values())

    review: list[dict[str, Any]] = []
    if inv_report:
        for loc in inv_report.failed_locations():
            reasons = [r.message or r.code for r in inv_report.failures
                       if r.location.key() == loc.key()]
            page = loc.page
            if page is None and loc.scope is Scope.ROW:
                match = next((r for r in statement.rows if r.index == loc.row_index), None)
                page = match.page if match else None
            review.append({"location": loc.key(), "page": page,
                           "reason": reasons[0] if reasons else "", "all_reasons": reasons})

    return Certificate(
        doc_id=statement.doc_id,
        doc_sha256=doc_sha256,
        spec_fingerprint=spec.fingerprint(),
        spec_doc_type=spec.doc_type,
        framework_version=version,
        final_state=str(final_state),
        verification_level=spec.verification_level() if final_state is State.ACCEPT else "NONE",
        accepted=final_state is State.ACCEPT,
        issued_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        invariants={"total": total, "passed": passed, "by_invariant": inv_counts,
                    "failure_codes": inv_report.codes() if inv_report else [],
                    "failures": [r.to_json() for r in (inv_report.failures if inv_report else [])]},
        grounding=gr_report.to_json() if gr_report else {},
        fields=[_field_json(f) for f in statement.header.fields()],
        rows=[{"index": r.index, "page": r.page,
               "fields": [_field_json(f) for f in r.fields()]} for r in statement.rows],
        flags=flags or [],
        tiers_used=_tiers_used(trace),
        model_calls=[c.to_json() for c in trace.model_calls],
        cost_usd=trace.total_cost(),
        transition_path=trace.path(),
        replay_hash=trace.replay_hash(),
        review_targets=review,
    )
