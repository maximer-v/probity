"""Wiring: the context, the guards, and the loop that drives the machine.

Everything a guard may look at lives on :class:`Context`, and every guard is a pure
predicate over it that returns a verdict together with the evidence for the verdict. The
loop itself is twenty lines: ask the table what is next, record it, run the state's
action, repeat. All of the intelligence is in the proposers, and all of the authority is
in the verifiers.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Callable

from .certificate import Certificate, build_certificate
from .grounding import DocumentIndex, GroundingReport, ground_statement
from .invariants import Location, Scope, VerificationReport, run_invariants, stamp_witnesses
from .machine import GuardRegistry, Machine, State, build_machine
from .proposers.base import Document, Proposal, Proposer
from .records import Provenance, Statement, Status
from .repair import RepairOutcome, attempt_repair
from .trace import Trace

__version_fallback__ = "0.2.0"


@dataclass
class Budget:
    """Hard stops. Every one of these is a number, not a judgement."""

    calls_by_tier: dict[str, int] = dc_field(default_factory=dict)
    regions_by_tier: dict[str, int] = dc_field(default_factory=dict)
    repairs_by_region: dict[str, int] = dc_field(default_factory=dict)
    max_usd: float = 1.0
    spent_usd: float = 0.0
    total_calls: int = 0
    max_total_calls: int = 40

    def can_call(self, tier: str, spec, *, free: bool = False) -> tuple[bool, str]:
        """May this tier run? ``free`` tiers are never gated by the cost cap.

        The text layer costs nothing, so a run configured with no money to spend must
        still be able to read a digital PDF. Gating it on ``spent >= max_usd`` makes a
        zero budget mean "do nothing", which looks exactly like a document that could
        not be read.
        """
        tb = spec.budgets.get(tier)
        used = self.calls_by_tier.get(tier, 0)
        if tb is not None and used >= tb.max_calls:
            return False, f"{tier} call budget spent ({used}/{tb.max_calls})"
        if self.total_calls >= self.max_total_calls:
            return False, f"total call budget spent ({self.total_calls}/{self.max_total_calls})"
        if not free and self.spent_usd >= self.max_usd:
            return False, f"cost budget spent (${self.spent_usd:.4f}/${self.max_usd:.4f})"
        return True, ""

    def note_call(self, tier: str, cost: float) -> None:
        self.calls_by_tier[tier] = self.calls_by_tier.get(tier, 0) + 1
        self.total_calls += 1
        self.spent_usd += cost


@dataclass
class Context:
    """Everything the machine and its guards can see."""

    doc: Document
    spec: Any
    trace: Trace
    proposers: dict[str, Proposer]
    budget: Budget

    tier_index: int = -1
    statement: Statement | None = None
    index: DocumentIndex | None = None
    inv_report: VerificationReport | None = None
    gr_report: GroundingReport | None = None
    region: Location | None = None
    last_proposal: Proposal | None = None
    repair_outcome: RepairOutcome | None = None
    repaired_regions: set[str] = dc_field(default_factory=set)
    #: Second-reader state. ``second_reads`` caches one read per page; ``settled_regions``
    #: are regions where two readers agree, so the fault is in the document and another
    #: re-read would learn nothing; ``corrections`` and ``opinions`` are the record.
    second_reads: dict[int, Any] = dc_field(default_factory=dict)
    settled_regions: dict[str, dict] = dc_field(default_factory=dict)
    #: Rows whose figures were taken from the second reader.
    from_second: set[int] = dc_field(default_factory=set)
    #: What the first reader originally transcribed (date, balance) on rows that were
    #: later replaced, so agreement on a carried-in balance is judged on what each
    #: reader independently produced.
    first_values: dict[int, tuple] = dc_field(default_factory=dict)
    corrections: list[dict[str, Any]] = dc_field(default_factory=list)
    opinions: list[dict[str, Any]] = dc_field(default_factory=list)
    ingest_error: str | None = None
    flags: list[dict[str, Any]] = dc_field(default_factory=list)
    step: int = 0
    _why: dict[str, str] = dc_field(default_factory=dict)

    # ------------------------------------------------------------------ helpers

    @property
    def tier(self) -> str:
        if 0 <= self.tier_index < len(self.available_tiers):
            return self.available_tiers[self.tier_index]
        return "none"

    @property
    def available_tiers(self) -> list[str]:
        """The spec's ladder, restricted to tiers that actually exist in this run."""
        return [t for t in self.spec.tier_order if t in self.proposers]

    def next_tier_index(self) -> int | None:
        for i in range(self.tier_index + 1, len(self.available_tiers)):
            tier = self.available_tiers[i]
            proposer = self.proposers.get(tier)
            free = not getattr(proposer, "bills_usd", True)
            ok, _ = self.budget.can_call(tier, self.spec, free=free)
            if ok:
                return i
        return None

    def acceptance_check(self) -> tuple[bool, str]:
        """The acceptance policy, as a verdict plus the reason it was reached."""
        pol = self.spec.acceptance
        if self.statement is None or self.inv_report is None:
            return False, "nothing has been read yet"
        if not self.statement.rows:
            return False, "no transaction rows"
        if pol.require_all_invariants and not self.inv_report.all_passed:
            return False, (f"{len(self.inv_report.failures)} invariant failure(s): "
                           f"{', '.join(self.inv_report.codes())}")
        frac = self.gr_report.fraction_grounded() if self.gr_report else 0.0
        if frac < pol.min_grounded_fraction:
            n = len(self.gr_report.failures) if self.gr_report else 0
            return False, (f"only {frac:.1%} of required fields grounded "
                           f"(policy {pol.min_grounded_fraction:.0%}); {n} not located")
        missing = [name for name in pol.require_header_fields
                   if getattr(st_header := self.statement.header, name).value is None]
        if missing:
            reasons = {name: getattr(st_header, name).error_code or "not found"
                       for name in missing}
            return False, (f"required header field(s) unreadable: {reasons}. A missing "
                           "value is skipped by grounding and treated as nothing to "
                           "check by the invariants, so absence has to refuse rather "
                           "than pass")
        if not pol.allow_inferred_fields:
            inferred = [f.name for f in self.statement.all_fields()
                        if f.status is Status.INFERRED]
            if inferred:
                return False, f"{len(inferred)} field(s) only INFERRED: {inferred[:4]}"
        # A cell that was present but could not be read, or whose printed text
        # disagrees with the value the proposer assigned it, must refuse. Both were
        # previously only logged: grounding skips a value of None, and the row gate
        # below inspects only cells that parsed, so an unreadable amount could ride
        # along inside an accepted document.
        broken = [(f.name, f.error_code) for f in self.statement.all_fields()
                  if f.raw and f.value is None and f.error_code
                  and f.error_code not in {"LABEL_NOT_FOUND"}]
        contradicted = [f.name for f in self.statement.all_fields()
                        if f.error_code in {"MODEL_SELF_CONTRADICTION",
                                            "COLUMN_CONTRADICTS_FIELD"}]
        if broken:
            return False, (f"{len(broken)} cell(s) are printed but unreadable: "
                           f"{broken[:4]}. An unreadable cell is not an empty one")
        if contradicted:
            return False, (f"{len(contradicted)} value(s) where the model's own figure "
                           f"disagrees with the characters it transcribed: "
                           f"{contradicted[:4]}")

        unverified_rows = [r.index for r in self.statement.rows
                           if any(f.status is Status.UNVERIFIED for f in
                                  (r.debit, r.credit, r.balance) if f.value is not None)]
        if len(unverified_rows) > pol.max_unverified_rows:
            return False, (f"{len(unverified_rows)} row(s) carry UNVERIFIED amounts "
                           f"(policy allows {pol.max_unverified_rows}): {unverified_rows[:4]}")
        return True, "every invariant passed and every required field is grounded"


# ----------------------------------------------------------------------- guards

def build_guards() -> GuardRegistry:
    reg = GuardRegistry()

    def g(name: str, doc: str):
        def deco(fn: Callable[[Context], bool]):
            def wrapped(ctx: Context) -> bool:
                answer, why = fn(ctx)
                ctx._why[name] = why
                return answer
            reg.add(name, wrapped, doc)
            return fn
        return deco

    @g("ingest_failed", "the file could not be opened or contains no pages")
    def _ingest_failed(ctx: Context):
        return bool(ctx.ingest_error), ctx.ingest_error or "the document opened and has pages"

    @g("extract_empty_and_tier_left", "this tier produced no rows and a dearer tier is free")
    def _empty_tier(ctx: Context):
        empty = not (ctx.statement and ctx.statement.rows)
        if not empty:
            return False, f"{len(ctx.statement.rows)} rows were read"
        nxt = ctx.next_tier_index()
        if nxt is None:
            return False, f"{ctx.tier} read nothing and no further tier is within budget"
        return True, f"{ctx.tier} read nothing; {ctx.available_tiers[nxt]} is available"

    @g("extract_empty", "this tier produced no rows")
    def _empty(ctx: Context):
        empty = not (ctx.statement and ctx.statement.rows)
        return empty, "no rows were read" if empty else f"{len(ctx.statement.rows)} rows were read"

    @g("accepts", "every invariant passed and the acceptance policy is satisfied")
    def _accepts(ctx: Context):
        return ctx.acceptance_check()

    @g("repairable", "the failure is localized and this region has repair budget left")
    def _repairable(ctx: Context):
        if ctx.inv_report is None:
            return False, "nothing verified yet"
        if not ctx.inv_report.is_localized():
            doc_fails = [r.invariant_id for r in ctx.inv_report.failures
                         if r.location.scope is Scope.DOCUMENT]
            return False, ("the failure is document-wide, so there is no region to re-read "
                           f"({', '.join(sorted(set(doc_fails)))}); repairing without a "
                           "location is how a model is invited to invent")
        locs = ctx.inv_report.failed_locations()
        if len(ctx.repaired_regions) >= ctx.spec.max_repair_regions:
            return False, (f"{len(ctx.repaired_regions)} regions already repaired, "
                           f"limit {ctx.spec.max_repair_regions}")
        for loc in locs:
            if _nothing_to_learn(ctx, loc):
                continue
            used = ctx.budget.repairs_by_region.get(loc.key(), 0)
            if used < ctx.spec.repair_budget_per_region:
                ctx.region = loc
                return True, (f"{loc.key()} has {ctx.spec.repair_budget_per_region - used} "
                              f"repair attempt(s) left")
        return False, (f"every failing region has used its {ctx.spec.repair_budget_per_region} "
                       f"repair attempts: {[l.key() for l in locs][:4]}")

    @g("tier_left", "a more capable tier is available within budget")
    def _tier_left(ctx: Context):
        # Once a reading exists, a failed check is settled by a second look under the
        # correction guards, or it is not settled. Handing the failing region to
        # another reader and splicing its answer in would change values outside those
        # guards and outside the corrections record, and could overturn a finding two
        # readers agreed on. Another reader is used only when nothing was read at all.
        if ctx.statement is not None and ctx.statement.rows:
            return False, ("a reading exists; a failed check is settled by a second "
                           "look or left unresolved, not by replacing the reading")
        nxt = ctx.next_tier_index()
        if nxt is None:
            spent = {k: v for k, v in ctx.budget.calls_by_tier.items()}
            return False, (f"no tier left within budget (used {spent}, "
                           f"${ctx.budget.spent_usd:.4f}/${ctx.budget.max_usd:.2f})")
        return True, f"{ctx.available_tiers[nxt]} is available"

    @g("repair_proposed", "the repair produced a grounded candidate from the source")
    def _repair_proposed(ctx: Context):
        out = ctx.repair_outcome
        if out is None:
            return False, "no repair was attempted"
        if not out.accepted:
            return False, out.reason
        return True, out.reason

    @g("tier_advanced", "the tier pointer moved to a usable tier")
    def _tier_advanced(ctx: Context):
        nxt = ctx.next_tier_index()
        if nxt is None:
            return False, "no further tier is within budget"
        old = ctx.tier
        ctx.tier_index = nxt
        ctx.trace.tier_change(old, ctx.tier, "verification failed at the cheaper tier",
                              region=ctx.region.key() if ctx.region else None)
        return True, f"now at {ctx.tier}"

    return reg


# ------------------------------------------------------------------- the engine

@dataclass
class Result:
    doc_id: str
    final_state: State
    statement: Statement | None
    certificate: Certificate
    trace: Trace
    corrections: list[dict[str, Any]] = dc_field(default_factory=list)
    opinions: list[dict[str, Any]] = dc_field(default_factory=list)
    conclusion: str = "UNRESOLVED"
    conclusion_reason: str = ""

    @property
    def accepted(self) -> bool:
        return self.final_state is State.ACCEPT

    @property
    def flagged(self) -> bool:
        return bool(self.certificate.flags)


class Pipeline:
    """Runs one document through the machine."""

    def __init__(self, spec, proposers: dict[str, Proposer], *,
                 max_usd: float = 1.0, max_total_calls: int = 40,
                 version: str | None = None, keep_model_text: bool = False):
        self.spec = spec
        self.proposers = proposers
        self.max_usd = max_usd
        self.max_total_calls = max_total_calls
        self.keep_model_text = keep_model_text
        self.guards = build_guards()
        self.machine: Machine = build_machine(self.guards)
        if version is None:
            try:
                from . import __version__ as v
                version = v
            except Exception:
                version = __version_fallback__
        self.version = version

    # -------------------------------------------------------------- state actions

    def _ingest(self, ctx: Context) -> None:
        path = Path(ctx.doc.pdf_path) if ctx.doc.pdf_path else None
        if path is None or not path.exists():
            ctx.ingest_error = f"no such file: {ctx.doc.pdf_path}"
            return
        data = path.read_bytes()
        ctx.doc.sha256 = hashlib.sha256(data).hexdigest()
        from .images import images_to_pdf, is_image
        if is_image(path):
            # A photo or a scan saved as an image: wrap it as pages. The hash above is
            # of the file the caller supplied, not of the wrapper.
            try:
                ctx.doc.meta["source_image"] = str(path)
                ctx.doc.pdf_path = images_to_pdf([path])
                path = Path(ctx.doc.pdf_path)
            except Exception as exc:
                ctx.ingest_error = f"{type(exc).__name__}: {exc}"
                return
        try:
            import pypdfium2 as pdfium
            from .proposers.vlm import _RENDER_LOCK
            with _RENDER_LOCK:      # the PDF library is not safe across threads
                pdf = pdfium.PdfDocument(str(path))
                ctx.doc.page_count = len(pdf)
            if ctx.doc.page_count == 0:
                ctx.ingest_error = "the PDF has no pages"
        except Exception as exc:
            ctx.ingest_error = f"{type(exc).__name__}: {exc}"
        ctx.trace.note(f"ingested {path.name}", sha256=ctx.doc.sha256[:16],
                       pages=ctx.doc.page_count, bytes=len(data))

    def _classify(self, ctx: Context) -> None:
        """Decide digital or scanned, and set the ladder's starting rung accordingly."""
        from .proposers.text_layer import has_text_layer, read_index

        digital, evidence = False, {}
        if "text_layer" in ctx.proposers:
            try:
                idx = read_index(ctx.doc.pdf_path)
                digital, evidence = has_text_layer(idx)
            except Exception as exc:
                evidence = {"error": f"{type(exc).__name__}: {exc}"}
        ctx.doc.is_digital = digital
        ctx.trace.guard(State.CLASSIFY, "has_text_layer", digital,
                        why=("a usable text layer is present" if digital
                             else "no usable text layer; OCR will be required"),
                        **evidence)
        tiers = ctx.available_tiers
        if digital:
            ctx.tier_index = 0
        else:
            # Skip the tiers that read a text layer that does not exist. Running them
            # anyway would burn a step and report a confusing empty read.
            start = next((i for i, t in enumerate(tiers)
                          if t not in {"text_layer", "template"}), len(tiers) - 1)
            ctx.tier_index = max(0, start)
            ctx.trace.note(f"starting at {tiers[ctx.tier_index] if tiers else 'none'}: "
                           "the text-layer tiers cannot apply to a scan")

    def _extract(self, ctx: Context) -> None:
        tier = ctx.tier
        proposer = ctx.proposers.get(tier)
        if proposer is None:
            ctx.statement = ctx.statement or Statement(ctx.doc.doc_id, self.spec.currency_default)
            ctx.trace.note(f"tier {tier} has no proposer registered")
            return
        ok, why = ctx.budget.can_call(tier, self.spec,
                                      free=not getattr(proposer, "bills_usd", True))
        if not ok:
            ctx.trace.budget(f"tier:{tier}", ctx.budget.calls_by_tier.get(tier, 0),
                             float(getattr(self.spec.budgets.get(tier), "max_calls", 0) or 0),
                             blocked=True)
            ctx.trace.note(f"cannot run {tier}: {why}")
            ctx.statement = ctx.statement or Statement(ctx.doc.doc_id, self.spec.currency_default)
            return

        region = ctx.region
        try:
            proposal = proposer.propose(ctx.doc, self.spec, region=region,
                                        previous=ctx.statement)
        except Exception as exc:
            ctx.trace.note(f"{tier} raised {type(exc).__name__}: {exc}",
                           tier=tier, error=str(exc))
            ctx.statement = ctx.statement or Statement(ctx.doc.doc_id, self.spec.currency_default)
            return

        for call in getattr(proposal, "model_calls", []) or []:
            ctx.trace.model_call(call)
            ctx.budget.note_call(tier, call.cost_usd)
        if not getattr(proposal, "model_calls", None):
            ctx.budget.note_call(tier, 0.0)

        if region is not None and ctx.statement is not None and proposal.statement.rows:
            _splice(ctx.statement, proposal.statement, region)
            ctx.index = _merge_index(ctx.index, proposal.index)
        else:
            ctx.statement = proposal.statement
            ctx.index = _merge_index(ctx.index, proposal.index)
        ctx.last_proposal = proposal

        ctx.trace.extraction(tier, len(ctx.statement.rows),
                             sum(proposal.parse_errors.values()),
                             proposal.parse_errors,
                             region=region.key() if region else None,
                             notes=proposal.notes or None,
                             model_confidence=proposal.model_confidence)
        ctx.region = None

    def _ground(self, ctx: Context) -> None:
        if ctx.statement is None or ctx.index is None:
            return
        ctx.gr_report = ground_statement(ctx.statement, ctx.index, self.spec)
        ctx.trace.grounding(ctx.gr_report)

    def _verify(self, ctx: Context) -> None:
        if ctx.statement is None:
            return
        for f in ctx.statement.all_fields():
            f.verified_by.clear()
        ctx.inv_report = run_invariants(ctx.statement, self.spec)
        stamp_witnesses(ctx.statement, ctx.inv_report)
        ctx.trace.invariants(ctx.inv_report)
        _raise_flags(ctx)

    def _repair(self, ctx: Context) -> None:
        """Work through the failing regions until one is fixed or none is left.

        A region that comes back settled-but-not-fixed (two readers agree, so the
        document is at fault there) must not end the repair: a misread further down the
        page is still worth correcting, and leaving it would report a reading error as
        if it were a second fault in the document. So the loop moves on to the next
        failing region, under the same per-region and per-document limits as before.
        """
        while True:
            ctx.repair_outcome = attempt_repair(ctx, self.spec)
            if ctx.region is not None:
                key = ctx.region.key()
                ctx.budget.repairs_by_region[key] = (
                    ctx.budget.repairs_by_region.get(key, 0) + 1)
                ctx.repaired_regions.add(key)
            if ctx.repair_outcome.accepted:
                return
            nxt = self._next_region(ctx)
            if nxt is None:
                return
            ctx.region = nxt

    def _next_region(self, ctx: Context) -> Location | None:
        if ctx.inv_report is None or not ctx.inv_report.is_localized():
            return None
        if len(ctx.repaired_regions) >= self.spec.max_repair_regions:
            return None
        for loc in ctx.inv_report.failed_locations():
            if _nothing_to_learn(ctx, loc):
                continue
            if ctx.budget.repairs_by_region.get(loc.key(), 0) < self.spec.repair_budget_per_region:
                return loc
        return None

    ACTIONS: dict[State, str] = {
        State.INGEST: "_ingest", State.CLASSIFY: "_classify", State.EXTRACT: "_extract",
        State.GROUND: "_ground", State.VERIFY: "_verify", State.REPAIR: "_repair",
    }

    # ------------------------------------------------------------------- the loop

    def run(self, doc: Document) -> Result:
        trace = Trace(doc_id=doc.doc_id, spec_fingerprint=self.spec.fingerprint(),
                      framework_version=self.version, keep_model_text=self.keep_model_text)
        ctx = Context(doc=doc, spec=self.spec, trace=trace, proposers=self.proposers,
                      budget=Budget(max_usd=self.max_usd,
                                    max_total_calls=self.max_total_calls))
        trace.run_start(doc_type=self.spec.doc_type, tiers=ctx.available_tiers,
                        verification_level=self.spec.verification_level())

        state = self.machine.initial
        while True:
            trace.state_enter(state)
            action = self.ACTIONS.get(state)
            if action:
                getattr(self, action)(ctx)
            if state.is_terminal:
                break
            ctx.step += 1
            if ctx.step > self.machine.max_steps:
                trace.note(f"step limit {self.machine.max_steps} reached; stopping")
                state = State.HUMAN_REVIEW
                trace.state_enter(state)
                break
            transition, asked = self.machine.next_transition(state, ctx)
            for name, answer in asked:
                trace.guard(state, name, answer, why=ctx._why.get(name, ""))
            trace.transition(state, transition.target, transition.guard, asked)
            state = transition.target

        reason = ctx._why.get("accepts", "")
        trace.run_end(state, reason=reason)
        cert = build_certificate(
            statement=ctx.statement or Statement(doc.doc_id, self.spec.currency_default),
            spec=self.spec, trace=trace, inv_report=ctx.inv_report,
            gr_report=ctx.gr_report, final_state=state, doc_sha256=doc.sha256,
            version=self.version, flags=ctx.flags)
        conclusion, why = _conclude(ctx, state)
        cert.conclusion = conclusion
        cert.conclusion_reason = why
        cert.corrections = list(ctx.corrections)
        cert.opinions = list(ctx.opinions)
        # Rows whose "two readers agree" finding still stands on the final figures. An
        # earlier finding on a row whose figures have since changed is history.
        cert.inconsistent_rows = sorted({
            r.location.row_index for r in (ctx.inv_report.failures if ctx.inv_report else [])
            if r.location.scope is Scope.ROW
            and _finding_for(ctx, r.location) == "DOCUMENT_INCONSISTENT"})
        return Result(doc.doc_id, state, ctx.statement, cert, trace,
                      corrections=list(ctx.corrections), opinions=list(ctx.opinions),
                      conclusion=conclusion, conclusion_reason=why)


# ------------------------------------------------------------------------ helpers

def _finding_for(ctx, loc) -> str | None:
    """The second-reader finding that still stands for this location, if any.

    A finding is about specific figures. It is stored with them, and if the row or the
    balance carried into it has changed since, the finding no longer applies.
    """
    entry = ctx.settled_regions.get(loc.key())
    if not entry:
        return None
    if entry["finding"] == "DOCUMENT_INCONSISTENT":
        from .second_opinion import operands
        if loc.row_index is None or list(operands(ctx.statement, ctx.spec, loc.row_index)) != list(
                entry["operands"]):
            return None
    return entry["finding"]


def _explained_by_rows(ctx, failure) -> bool:
    """Is this document-level failure fully accounted for by confirmed row failures?

    Only the closing total is treated this way, and only when it is arithmetically the
    same fact: every failing row has been confirmed as inconsistent by two readers, and
    the amount the total is off by equals the sum of what those rows are off by. Any
    other document-level or page-level failure is its own problem.
    """
    if failure.invariant_id != "GLOBAL_BAL" or failure.delta is None:
        return False
    rows = [r for r in ctx.inv_report.failures if r.location.scope is Scope.ROW]
    if not rows or any(_finding_for(ctx, r.location) != "DOCUMENT_INCONSISTENT"
                       for r in rows):
        return False
    balance = [r for r in rows if r.invariant_id == "ROW_BAL"]
    if len(balance) != len(rows) or any(r.delta is None for r in balance):
        return False
    return sum(r.delta for r in balance) == failure.delta


def _nothing_to_learn(ctx, loc) -> bool:
    """Would another look at this region by the same readers be wasted?"""
    if loc.scope is Scope.ROW:
        return loc.key() in ctx.settled_regions and (
            _finding_for(ctx, loc) is not None
            or ctx.settled_regions[loc.key()]["finding"] != "DOCUMENT_INCONSISTENT")
    here = [r for r in ctx.inv_report.failures if r.location.key() == loc.key()]
    return bool(here) and all(_explained_by_rows(ctx, r) for r in here)


def _conclude(ctx: Context, state: State) -> tuple[str, str]:
    """One of three statements about the document, and why.

    CONFIRMED              every rule passed on the final reading.
    DOCUMENT_INCONSISTENT  a rule fails, and every failure is either a row on which two
                           readers agree (the row and the figure carried into it), or
                           the closing total being off by exactly what those rows are
                           off by.
    UNRESOLVED             anything else.

    These are statements about the transcription and its arithmetic. CONFIRMED does
    not mean the document is authentic, and DOCUMENT_INCONSISTENT does not say why it
    fails to add up.
    """
    if state is State.ACCEPT:
        failing = ctx.inv_report.failures if ctx.inv_report is not None else []
        if failing:
            # Reachable only with a spec whose acceptance policy tolerates failing
            # rules. The machine accepted; the conclusion still may not say "confirmed".
            return "UNRESOLVED", (
                f"accepted under a policy that tolerates failing rules, but "
                f"{len(failing)} check(s) fail, so the reading is not confirmed")
        rows = sorted({c["row"] for c in ctx.corrections})
        return "CONFIRMED", ("every rule passed" + (
            f"; {len(rows)} row(s) were corrected on the way" if rows else ""))
    if ctx.inv_report is None or not (ctx.statement and ctx.statement.rows):
        return "UNRESOLVED", "nothing could be read and checked"
    fails = ctx.inv_report.failures
    row_fails = [r for r in fails if r.location.scope is Scope.ROW]
    other = [r for r in fails if r.location.scope is not Scope.ROW]
    open_rows = sorted({r.location.key() for r in row_fails
                        if _finding_for(ctx, r.location) != "DOCUMENT_INCONSISTENT"},
                       key=lambda k: int(k.split(":")[1]))
    open_other = sorted({f"{r.invariant_id} ({r.location.key()})" for r in other
                         if not _explained_by_rows(ctx, r)})
    if row_fails and not open_rows and not open_other:
        rows = sorted({r.location.key() for r in row_fails},
                      key=lambda k: int(k.split(":")[1]))
        return "DOCUMENT_INCONSISTENT", (
            f"the rules fail at {', '.join(rows)}, and two readers agree on what is "
            f"printed there and on the balance carried into it")
    if open_rows:
        return "UNRESOLVED", ("not confirmed by a second reading: "
                              + ", ".join(open_rows[:6]))
    if open_other:
        return "UNRESOLVED", ("a failure that is not located on a row is unexplained: "
                              + ", ".join(open_other[:4]))
    return "UNRESOLVED", "the document could not be accepted, and no rule is failing"


def _raise_flags(ctx: Context) -> None:
    """Turn invariant failures into named flags a consumer can act on.

    A flag is not the same thing as a rejection. "This page's carry-forward does not
    match" is a statement about the *document*, and the right response is to tell
    somebody, not to adjust a number until it agrees.
    """
    from .invariants import Code

    ctx.flags = []
    if ctx.inv_report is None:
        return
    mapping = {
        "NO_DUP_ROW": ("DUPLICATE_TRANSACTION", "a transaction line is printed twice"),
        "PAGE_SUBTOTAL": ("CARRY_FORWARD_BROKEN", "a page carry-forward does not match "
                                                  "the last balance on that page"),
        "COUNT": ("COUNT_MISMATCH", "the declared transaction count disagrees with the rows"),
        "DATE_ORDER": ("DATE_ANOMALY", "a transaction date is out of period or out of order"),
        "ROW_BAL": ("BALANCE_CHAIN_BROKEN", "the running balance does not follow from the "
                                            "amounts on at least one row"),
        "GLOBAL_BAL": ("STATEMENT_DOES_NOT_BALANCE",
                       "opening plus movements does not equal the closing balance"),
        "LAST_ROW_EQ_CLOSING": ("CLOSING_BALANCE_MISMATCH",
                                "the final row's balance is not the closing balance"),
    }
    seen: set[str] = set()
    for res in ctx.inv_report.failures:
        if res.code in {Code.NOT_APPLICABLE}:
            continue
        code, msg = mapping.get(res.invariant_id, (res.invariant_id, res.message))
        if code in seen:
            continue
        seen.add(code)
        ctx.flags.append({
            "code": code, "message": msg, "invariant": res.invariant_id,
            "failure_code": res.code, "location": res.location.key(),
            "detail": res.message, "delta_minor": res.delta,
        })


def _splice(target: Statement, patch: Statement, region: Location) -> None:
    """Replace only the rows the region names, matching on page as well as index.

    Two traps here, both of which let a "bounded, local" repair edit rows it was never
    asked about. A patch index matches by number alone, so a patch produced for row 0
    would overwrite row 1 if the patch happened to contain one; and a proposer that
    re-reads a single page numbers its rows from zero, so a page-2 reread would land on
    page-1 rows. Restricting by the region's own scope and by page closes both.
    """
    allowed: set[int] | None = None
    if region.scope is Scope.ROW and region.row_index is not None:
        allowed = {region.row_index}
    page = region.page

    by_key = {}
    for r in patch.rows:
        by_key[(r.page, r.index)] = r

    for i, row in enumerate(target.rows):
        if allowed is not None and row.index not in allowed:
            continue
        if page is not None and row.page != page:
            continue
        candidate = by_key.get((row.page, row.index))
        if candidate is not None:
            target.rows[i] = candidate
    for page, field in patch.carried_forward.items():
        if region.scope is Scope.PAGE and region.page == page:
            target.carried_forward[page] = field
    for name in ("opening_balance", "closing_balance", "tx_count"):
        pf = getattr(patch.header, name)
        if pf.value is not None and region.scope is Scope.DOCUMENT:
            setattr(target.header, name, pf)


def _merge_index(old: DocumentIndex | None, new: DocumentIndex) -> DocumentIndex:
    """Keep every source's tokens: the text layer and OCR can cross-check each other."""
    if old is None:
        return new
    for page_no, page in new.pages.items():
        if page_no in old.pages:
            existing = {(t.text, round(t.bbox.x0, 1), round(t.bbox.y0, 1))
                        for t in old.pages[page_no].tokens}
            for t in page.tokens:
                if (t.text, round(t.bbox.x0, 1), round(t.bbox.y0, 1)) not in existing:
                    old.pages[page_no].tokens.append(t)
        else:
            old.pages[page_no] = page
    old.sources = tuple(sorted(set(old.sources) | set(new.sources)))
    return old
