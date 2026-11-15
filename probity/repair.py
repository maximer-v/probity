"""Bounded, grounded repair: fix a region without ever naming the target.

This is where a system quietly becomes dishonest. Told "the closing balance must be
12,430.55, fix the table", a capable model will deliver a table that totals 12,430.55,
and the way it gets there is to change whatever it must. The FinBalance benchmark
measured this: feeding ledger feedback back to models raised reported balance-sheet
accuracy by roughly 30 points while *reducing* inconsistency detection for some of them.
The accuracy was real. So was the damage.

Three rules keep it honest, and all three are enforced in code rather than requested in
a prompt:

1. The repair is told *where* to look (row 23, page 2), never what the answer should be.
   :func:`build_repair_request` has no access to the expected value, so no prompt
   built from it can leak one.
2. Every candidate goes back through grounding before verification. A value that is not
   printed on the page is rejected even when it makes every total agree. That is the
   test a fabricated value fails and a correctly re-read value passes.
3. The attempt is bounded per region and per document, and the ladder is finite. When
   the budget is gone the document goes to a human, which is a worse outcome for a
   dashboard and a better one for a lender.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

from .grounding import ground_field
from .invariants import Location, Scope, run_invariants
from .records import Field, Provenance, Row, Statement


@dataclass
class RepairRequest:
    """What a repair proposer is allowed to know. Deliberately missing the answer."""

    region: Location
    page: int
    rows: tuple[int, ...]
    columns: tuple[str, ...]
    reason_code: str                 # e.g. "MISMATCH" — the class of failure, not the delta
    instruction: str

    def to_json(self) -> dict[str, Any]:
        return {"region": self.region.key(), "page": self.page, "rows": list(self.rows),
                "columns": list(self.columns), "reason_code": self.reason_code,
                "instruction": self.instruction}


@dataclass
class RepairOutcome:
    accepted: bool
    reason: str
    strategy: str = ""
    changed: list[dict[str, Any]] = dc_field(default_factory=list)
    rejected: list[dict[str, Any]] = dc_field(default_factory=list)
    #: True when re-reading this region again cannot change anything: either it was
    #: corrected, or two readers agree and the document itself is at fault.
    settled: bool = False
    finding: str = ""

    def to_json(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "reason": self.reason, "strategy": self.strategy,
                "changed": self.changed, "rejected": self.rejected,
                "settled": self.settled, "finding": self.finding}


def build_repair_request(ctx, region: Location) -> RepairRequest:
    """Describe the region to re-read, with no expected value anywhere in it.

    The failure *code* is included (a mismatch is a different job from an unreadable
    cell) but never the delta, the expected figure or the neighbouring balances. A
    proposer given those would be able to solve for the number instead of reading it.
    """
    failures = [r for r in (ctx.inv_report.failures if ctx.inv_report else [])
                if r.location.key() == region.key()]
    code = failures[0].code if failures else "UNKNOWN"

    rows: tuple[int, ...] = ()
    page = region.page or 1
    if region.scope is Scope.ROW and region.row_index is not None:
        i = region.row_index
        # The neighbours matter: a wrong balance on row i breaks rows i and i+1, so the
        # cell to re-read may be on the line above the one that failed.
        rows = tuple(sorted({max(0, i - 1), i, i + 1}))
        match = next((r for r in (ctx.statement.rows if ctx.statement else [])
                      if r.index == i), None)
        if match is not None:
            page = match.page
    cols = tuple(region.fields) or ("date", "debit", "credit", "balance")

    instruction = (
        "Transcribe exactly what is printed in the marked area. Report the characters as "
        "they appear, including separators and any sign or CR/DR marker. If a cell is "
        "empty, say it is empty. Do not compute, complete or correct anything."
    )
    return RepairRequest(region=region, page=page, rows=rows, columns=cols,
                         reason_code=code, instruction=instruction)


def redact_for_repair(statement: Statement | None, request: RepairRequest) -> Statement | None:
    """Strip everything a proposer could solve the answer from.

    Sanitising the *request* is not enough on its own. A proposer is also handed the
    previous reading so it can place its work, and that reading contains the opening
    balance and the neighbouring running balances — which is precisely the arithmetic
    needed to compute the number the repair is supposed to read off the page. A model
    that receives it can satisfy every check by calculating rather than transcribing.

    So the copy that goes out keeps the shape of the document and the rows in scope,
    and removes every monetary value and the whole header. What survives is enough to
    say "this is row 23 on page 2", and not enough to work out what row 23 should say.
    """
    if statement is None:
        return None
    out = statement.copy()
    out.header = type(statement.header)()
    out.carried_forward = {}
    keep = set(request.rows)
    for row in out.rows:
        if row.index not in keep:
            row.date = Field("date")
            row.description = Field("description")
        for name in ("debit", "credit", "balance"):
            setattr(row, name, Field(name))
    out.notes = ["redacted for repair: amounts and header removed so that the target "
                 "value cannot be derived"]
    return out


def attempt_repair(ctx, spec) -> RepairOutcome:
    """Take a second look at the failing region.

    There is one way a value is changed after the first reading: a second transcription
    of the page is obtained, and :mod:`probity.second_opinion` compares the two under
    its guards. Every change it makes is appended to ``ctx.corrections``.
    """
    region = ctx.region
    if region is None or ctx.statement is None:
        return RepairOutcome(False, "no region to repair")

    request = build_repair_request(ctx, region)
    ctx.trace.note(f"repair request for {region.key()}", request=request.to_json())

    # One mechanism, two possible sources of the second transcription. With a second
    # reader configured it is that model. Without one, the first reader is asked again
    # at its re-read resolution and exactly the same comparison and guards apply; what
    # it changes is recorded as a same-reader correction, and its agreeing with itself
    # is never taken as confirmation.
    strategies = ["second_opinion" if "checker" in ctx.proposers else "reread_region"]
    for strategy in strategies:
        outcome = _run_strategy(strategy, ctx, spec, request)
        verdict = ("accepted" if outcome.accepted else
                   "both readers agree, the document is inconsistent here"
                   if outcome.finding == "DOCUMENT_INCONSISTENT" else "rejected")
        ctx.trace.repair(region.key(), strategy, verdict, detail=outcome.to_json())
        if outcome.accepted or outcome.settled:
            return outcome
    return RepairOutcome(False, f"no grounded candidate for {region.key()}",
                         strategy="exhausted")


def _run_strategy(strategy: str, ctx, spec, request: RepairRequest) -> RepairOutcome:
    if strategy == "second_opinion":
        return _second_opinion(ctx, spec, request)
    return _reread_region(ctx, spec, request)


def _second_opinion(ctx, spec, request: RepairRequest,
                    source: str = "checker") -> RepairOutcome:
    """Get a second transcription of the page, and let the failed rule judge.

    See :mod:`probity.second_opinion`. The outcome is recorded on the context whatever
    it is: a correction, a confirmed inconsistency, or a dispute are all things the
    person reading the report needs to see.
    """
    from .second_opinion import second_opinion

    op = second_opinion(ctx, spec, request, source=source)
    ctx.opinions.append(op.to_json())
    ctx.corrections.extend(op.corrections)
    if not op.accepted:
        # Bound to the figures it was made on: see pipeline._finding_for.
        ctx.settled_regions[request.region.key()] = {
            "finding": op.finding, "operands": list(op.operands)}
    return RepairOutcome(op.accepted, op.reason,
                         strategy="second_opinion" if source == "checker"
                         else "reread_region",
                         changed=op.corrections, settled=op.settled,
                         finding=op.finding)


def _reread_region(ctx, spec, request: RepairRequest) -> RepairOutcome:
    """No second reader: ask the first reader again, under the same guards."""
    return _second_opinion(ctx, spec, request, source="self")


def _merge(old, new):
    from .pipeline import _merge_index
    return _merge_index(old, new)
