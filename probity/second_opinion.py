"""A second reader, asked only where a rule has failed.

One model reading a page is one opinion. When a rule fails on row 74, there are two
things that could be true and they call for opposite responses:

* the reader misread the row, and the document is fine;
* the reader read the row correctly, and the document itself does not tie.

Asking the same model again does not separate them: same weights, same image, same
mistake. A *different* model can. It is shown the page and nothing else: not the first
reading, not the rule that failed, not which row is in question. Whatever it returns is
a second transcription, and the machine compares the two.

    readers disagree on a failing row, and the second reading satisfies the rule
        -> the row takes the second reading. The correction is recorded with both
           values and the rule that selected it.
    readers agree on the failing row AND on the figures it is computed from
        -> the rule still fails, so the DOCUMENT is inconsistent at this row.
    anything else
        -> not resolved. Both readings are reported and neither is used.

What this does and does not establish. The second reader never decides anything: it
supplies a candidate, and the rule that failed is re-run on it. But a rule passing is
evidence of *consistency*, not of what is printed. A correction is a value that a
second model read and that makes the arithmetic close; it is not proof of the ink on
the page. Two models that share a misreading can also agree with each other and be
wrong. The guards below narrow the room for both; they do not close it.

The guards, each of which exists because a counter-example was constructed without it:

1. **Only a row that itself fails a rule may be replaced.** A neighbouring row that
   passes is never edited to make a failing row pass, because that is how an altered
   row both readers agree on could be made to tie.
2. **A replacement may not create a failure anywhere.** The set of failing checks
   afterwards must be a strict subset of the set before. Counting failures is not
   enough: a wrong replacement can remove two and create one.
3. **A row is replaced only by the same line.** The two readings are aligned on
   (date, balance) and a pair is used only when the descriptions also match and, if the
   readings disagree on how many rows the page has, the row's key is unique on the
   page. A correct value on the wrong line can make a broken document tie.
4. **Agreement must cover the operands.** A row's balance rule depends on the previous
   balance, and a date-order rule on the previous date. The document is called
   inconsistent only when both readers agree on the failing row and on that previous
   figure too, reading the previous page a second time if that is where it sits.
5. **Agreement is between the two readers, not between the second reader and itself.**
   A row that already took the second reading and still fails is not "agreed"; it is
   unresolved.
6. **A finding is bound to the figures it was made on.** If any of them later changes,
   the finding lapses.

Cost. The second reader sees only pages on which a rule failed, each at most once per
document, so a clean first reading costs nothing extra.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from difflib import SequenceMatcher
from typing import Any

from .invariants import Location, Scope, run_invariants
from .records import Field, Row

AMOUNT_COLUMNS = ("debit", "credit", "balance")
#: What a correction may replace on a row.
REPLACED_COLUMNS = ("date",) + AMOUNT_COLUMNS
#: The failures a second reading of a row's date and amounts can speak to. A date that
#: falls outside the statement period is not among them: that failure depends on the
#: header's period, which a second reading of the row says nothing about.
AGREEMENT_SETTLES = {("ROW_BAL", "MISMATCH"), ("DATE_ORDER", "OUT_OF_ORDER")}
#: A second reading may additionally *correct* a row that failed for these reasons. It
#: cannot settle them by agreement: an unreadable cell is not a figure two readers can
#: agree on, and the closing-balance check depends on the header.
SUPPORTED_FAILURES = AGREEMENT_SETTLES | {
    ("ROW_BAL", "UNREADABLE_OPERAND"), ("ROW_BAL", "BOTH_SIDES_PRESENT"),
    ("DATE_ORDER", "UNREADABLE_OPERAND"),
    ("LAST_ROW_EQ_CLOSING", "MISMATCH")}

#: Finding names. These are what a consumer branches on.
CORRECTED = "CORRECTED"                       # first reading was wrong, now fixed
DOCUMENT_INCONSISTENT = "DOCUMENT_INCONSISTENT"   # both readers agree; the page is wrong
DISPUTED = "DISPUTED"                         # readers disagree and neither ties
UNALIGNED = "UNALIGNED"                       # could not prove which row is which
UNAVAILABLE = "UNAVAILABLE"                   # no second reader, or it returned nothing
REPEATED = "REPEATED"                         # the same reader read it the same way again


@dataclass
class Opinion:
    """What the second reader said about one region, and what the machine concluded."""

    finding: str
    region: str
    page: int
    reason: str
    readers: tuple[str, str] = ("", "")
    rows: list[dict[str, Any]] = dc_field(default_factory=list)
    corrections: list[dict[str, Any]] = dc_field(default_factory=list)
    #: The figures a DOCUMENT_INCONSISTENT finding was made on.
    operands: list[Any] = dc_field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.finding == CORRECTED

    @property
    def settled(self) -> bool:
        """The repair step is finished with this region for now.

        Every finding ends it: a correction, an inconsistency, or a result that a
        further look by the same two readers could not change.
        """
        return True

    def to_json(self) -> dict[str, Any]:
        return {"finding": self.finding, "region": self.region, "page": self.page,
                "reason": self.reason, "readers": list(self.readers),
                "rows": self.rows, "corrections": self.corrections,
                "operands": self.operands}


def _minor(f: Field | None) -> int | None:
    return getattr(getattr(f, "value", None), "minor", None)


def _amounts(row: Row) -> tuple[int | None, int | None, int | None]:
    return (_minor(row.debit), _minor(row.credit), _minor(row.balance))


def _date_key(row: Row) -> str:
    v = getattr(row.date, "value", None)
    return v.isoformat() if hasattr(v, "isoformat") else str(row.date.raw or "")


def _key(row: Row) -> tuple[str, int | None]:
    return (_date_key(row), _minor(row.balance))


def _desc(row: Row) -> str:
    return " ".join(str(row.description.raw or "").lower().split())


def _digits(text: str) -> str:
    return "".join(ch for ch in text if ch.isdigit())


def _same_text(a: Row, b: Row) -> bool:
    """Do two transcribed descriptions name the same transaction?

    Closely similar wording, and exactly the same digits. Descriptions on a statement
    differ from one another mostly in their reference numbers ("cheque 5512" against
    "cheque 5513"), so similar wording with a different number is a different line, not
    a reading variation.
    """
    da, db = _desc(a), _desc(b)
    if not (da and db):
        return False
    return _digits(da) == _digits(db) and SequenceMatcher(None, da, db).ratio() >= 0.8


def align(first: list[Row], second: list[Row]) -> dict[int, Row]:
    """Pair rows of two readings of one page. Returns first-reading index -> second row.

    The sequences are aligned on (date, balance). Rows inside a run the readers agree
    on, and rows inside a stretch they disagree on that has the same length in both,
    are candidates for pairing position by position. A candidate pair is used only if
    there is positive evidence that it is the same printed line:

    * if the row's (date, balance) is unique on the page in both readings, the two must
      share a date or a balance, and when both readers transcribed a description the
      descriptions must be closely similar with identical digits (two readers that each
      dropped a different one of two look-alike lines would otherwise be paired);
    * if that key is NOT unique in either reading (several rows on one date with the
      same balance), position proves nothing, because a reader that dropped one such
      row and duplicated another leaves every count intact. The descriptions must then
      be identical after normalising case and spacing, and unique on the page in both
      readings.

    Anything unpaired is left untouched downstream.
    """
    ka, kb = [_key(r) for r in first], [_key(r) for r in second]
    da, db = [_desc(r) for r in first], [_desc(r) for r in second]
    out: dict[int, Row] = {}
    for tag, a0, a1, b0, b1 in SequenceMatcher(None, ka, kb, autojunk=False).get_opcodes():
        if not (tag == "equal" or (tag == "replace" and a1 - a0 == b1 - b0)):
            continue
        for a, b in zip(first[a0:a1], second[b0:b1]):
            same_date = bool(_date_key(a)) and _date_key(a) == _date_key(b)
            same_balance = (_minor(a.balance) is not None
                            and _minor(a.balance) == _minor(b.balance))
            if not (same_date or same_balance):
                continue
            unique = ka.count(_key(a)) == 1 and kb.count(_key(b)) == 1
            if unique:
                if _desc(a) and _desc(b):
                    if not _same_text(a, b):
                        continue
                elif not (same_date and same_balance):
                    continue
            else:
                if not (_desc(a) and _desc(a) == _desc(b)
                        and da.count(_desc(a)) == 1 and db.count(_desc(b)) == 1):
                    continue
            out[a.index] = b
    return out


def read_page(ctx, spec, page: int, source: str = "checker"
              ) -> tuple[list[Row] | None, str]:
    """A second transcription of one page, made at most once per document.

    ``source`` says who makes it: ``"checker"`` is the second reader, a different
    model; ``"self"`` is the first reader asked again at its re-read resolution, which
    is what a run without a second reader falls back to. Either way the request carries
    the page and the transcription instruction and nothing of the first reading.
    """
    cache: dict[tuple[str, int], Any] = ctx.second_reads
    if (source, page) in cache:
        return cache[(source, page)][0], cache[(source, page)][1]

    def keep(rows, why, opening=None):
        cache[(source, page)] = (rows, why, opening)
        return rows, why

    tier = "checker" if source == "checker" else ctx.tier
    reader = ctx.proposers.get(tier)
    if reader is None:
        return None, "no second reader is configured"
    if source == "checker" and _reader_name(ctx, "checker") == _reader_name(ctx, ctx.tier):
        return None, ("the second reader is the same model as the first, so its "
                      "reading would not be a second opinion")
    if source == "self" and not getattr(reader, "supports_regions", False):
        return None, f"{tier} cannot re-read a single page"
    ok, why = ctx.budget.can_call(tier, spec, free=not getattr(reader, "bills_usd", True))
    if not ok:
        return None, f"second reading not requested: {why}"
    try:
        # previous=None on purpose: the request must not carry the first reading.
        proposal = reader.propose(ctx.doc, spec,
                                  region=Location(Scope.PAGE, page=page), previous=None)
    except Exception as exc:  # noqa: BLE001 - recorded, and treated as "no opinion"
        return keep(None, f"second reading raised {type(exc).__name__}: {exc}")

    for call in getattr(proposal, "model_calls", []) or []:
        call.purpose = "second_opinion" if source == "checker" else "reread"
        ctx.trace.model_call(call)
        ctx.budget.note_call(tier, call.cost_usd)

    rows = [r for r in proposal.statement.rows]
    if not rows:
        why = "; ".join(proposal.notes or []) or "the second reading returned no rows"
        return keep(None, why)

    from .pipeline import _merge_index
    ctx.index = _merge_index(ctx.index, proposal.index)
    return keep(rows, "", _minor(proposal.statement.header.opening_balance))


def _second_opening(ctx) -> int | None:
    """The opening balance as the second reader transcribed it, if it read page one."""
    entry = ctx.second_reads.get(("checker", 1))
    return entry[2] if entry else None


def _reader_name(ctx, tier: str) -> str:
    p = ctx.proposers.get(tier)
    return str(getattr(getattr(p, "model", None), "model", tier))


def _failing_rows(report) -> dict[int, set[tuple[str, str]]]:
    """Row index -> the (rule, code) pairs currently failing on it."""
    out: dict[int, set[tuple[str, str]]] = {}
    for r in report.failures:
        if r.location.scope is Scope.ROW and r.location.row_index is not None:
            out.setdefault(r.location.row_index, set()).add((r.invariant_id, str(r.code)))
    return out


def _failure_ids(report) -> set[tuple[str, str]]:
    return {(r.invariant_id, r.location.key()) for r in report.failures}


def _row_view(row: Row) -> tuple:
    return (_date_key(row),) + _amounts(row)


OPENING = "opening"


def carried_from(statement, spec, row_index: int) -> list:
    """The rows whose figures the rules on this row are computed from.

    Two rules, two notions of "the row before", and both are by position in the
    transcription, never by index arithmetic (indices can have gaps):

    * ``ROW_BAL`` walks the statement in time order, so the balance carried in comes
      from the row above on an oldest-first statement and from the row below on a
      newest-first one, or from the opening balance for the earliest row;
    * ``DATE_ORDER`` compares each row's date with the row printed above it.

    Returns those rows, with the string ``OPENING`` standing for the opening balance.
    """
    rows = statement.rows
    pos = next((i for i, r in enumerate(rows) if r.index == row_index), None)
    if pos is None:
        return []
    ascending = spec.columns.sort_order == "ascending"
    out: list = []
    t = pos - 1 if ascending else pos + 1
    out.append(rows[t] if 0 <= t < len(rows) else OPENING)
    if pos - 1 >= 0 and rows[pos - 1] not in out:
        out.append(rows[pos - 1])
    return out


def operands(statement, spec, row_index: int) -> tuple:
    """Every figure the rules on this row are computed from, as currently held.

    A finding about a row is a finding about these values. It is stored with them and
    lapses if any of them changes.
    """
    row = next((r for r in statement.rows if r.index == row_index), None)
    if row is None:
        return ()
    out = _row_view(row)
    for other in carried_from(statement, spec, row_index):
        out += ((OPENING, _minor(statement.header.opening_balance)) if other is OPENING
                else (other.index, _date_key(other), _minor(other.balance)))
    return out


def second_opinion(ctx, spec, request, source: str = "checker") -> Opinion:
    """Compare two transcriptions of the failing row and act on the result.

    With ``source="checker"`` the second transcription comes from a different model.
    With ``source="self"`` it comes from the first reader asked again: the same
    comparison and the same guards apply, but agreement between a model and itself
    confirms nothing, so that path can correct a row and can never report the document
    as inconsistent.
    """
    region_key, page = request.region.key(), request.page
    second_tier = "checker" if source == "checker" else ctx.tier
    readers = (_reader_name(ctx, ctx.tier), _reader_name(ctx, second_tier))
    method = "second_reader" if source == "checker" else "same_reader_reread"

    def done(finding: str, reason: str, **kw: Any) -> Opinion:
        return Opinion(finding, region_key, page, reason, readers=readers, **kw)

    target = request.region.row_index
    if request.region.scope is not Scope.ROW or target is None:
        return done(UNAVAILABLE, "a second look is taken at a row; this failure is "
                    "not located on one")
    failing = _failing_rows(ctx.inv_report)
    rules = failing.get(target, set())
    if not rules:
        return done(UNAVAILABLE, "no rule is failing on this row any more")
    if not rules <= SUPPORTED_FAILURES:
        other = sorted(f"{r}/{c}" for r, c in rules - SUPPORTED_FAILURES)
        return done(UNAVAILABLE, f"a second reading of a row's date and amounts cannot "
                    f"settle {other}")

    second, why = read_page(ctx, spec, page, source)
    if second is None:
        return done(UNAVAILABLE, why)

    by_index = {r.index: r for r in ctx.statement.rows}
    first = [r for r in ctx.statement.rows if r.page == page]
    pairs = align(first, second)
    view = [{"row": i, "first": _show(by_index[i]), "second": _show(pairs[i]),
             "agree": _row_view(by_index[i]) == _row_view(pairs[i])}
            for i in (target - 1, target, target + 1) if i in by_index and i in pairs]

    if target not in pairs:
        return done(UNALIGNED, f"the second reading of page {page} has {len(second)} "
                    f"rows against {len(first)}, and no row in it could be shown to be "
                    f"the row in question", rows=view)
    if target in ctx.from_second:
        return done(DISPUTED, "this row already carries the second reading and the rule "
                    "still fails, so the two readers cannot be said to agree on it",
                    rows=view)

    a, b = by_index[target], pairs[target]

    # ---------------------------------------------------------------- they agree
    if _row_view(a) == _row_view(b):
        if not rules <= AGREEMENT_SETTLES:
            other = sorted(f"{r}/{c}" for r, c in rules - AGREEMENT_SETTLES)
            return done(DISPUTED, f"the readers agree on this row, but agreement on a "
                        f"row cannot settle {other}", rows=view)
        if source != "checker":
            return done(REPEATED, "the first reader transcribed the same figures again. "
                        "That is the same opinion twice and confirms nothing", rows=view)
        ok, why = _operands_agree(ctx, spec, target, pairs, page, source)
        if not ok:
            return done(DISPUTED, why, rows=view)
        # Two readers agree and the rule fails. Before the document is held responsible,
        # one more look: two models can share a misreading, and when they do it is
        # usually of the same low-resolution image. The first reader transcribes the
        # page again at its re-read resolution, blind as before.
        third = _third_reading(ctx, spec, target, by_index, failing, page, readers)
        if third["corrections"] is not None:
            return done(CORRECTED,
                        f"two readers had agreed on row {target}, but a third reading at "
                        f"higher resolution has row(s) {_span(third['touched'])} "
                        f"differently, and with it the rule passes and no other check "
                        f"fails. The two earlier readings shared a misreading",
                        rows=view + third["view"], corrections=third["corrections"])
        return done(DOCUMENT_INCONSISTENT,
                    "two readers transcribed the same date and amounts on this row and "
                    "the same balance carried into it, and the rule still fails, so "
                    "the document as transcribed does not hold at this row. "
                    + third["note"],
                    rows=view + third["view"],
                    operands=list(operands(ctx.statement, spec, target)))

    # --------------------------------------------------------------- they differ
    # Candidates are rows of this page that fail a rule themselves, are paired, read
    # differently in the second transcription, and have not already taken it.
    def candidate(i: int) -> bool:
        return (i in failing and failing[i] <= SUPPORTED_FAILURES and i in pairs
                and i not in ctx.from_second
                and _row_view(by_index[i]) != _row_view(pairs[i]))

    near = [i for i in (target + 1, target - 1) if i in by_index and candidate(i)]
    attempts = [[target]] + [[target, i] for i in near]
    if len(near) == 2:
        attempts.append([target] + near)
    before = len(ctx.inv_report.failures)
    for rows in attempts:
        corrections = _apply(ctx, spec, [(by_index[i], pairs[i]) for i in rows],
                             page, readers, method)
        if corrections is None:
            continue
        touched = set(rows)
        # The page has now been read twice and one misread on it is established. Every
        # other row of this page that is failing is offered the same second reading,
        # under the same test, in this step.
        swept = _sweep_page(ctx, spec, by_index, pairs, page, readers, method)
        corrections += swept
        touched |= {c["row"] for c in swept}
        return done(CORRECTED,
                    f"the second reading has row(s) {_span(touched)} "
                    f"differently, and with it the rule passes and no other "
                    f"check fails ({before} failure(s) before, "
                    f"{len(ctx.inv_report.failures)} after)",
                    rows=view, corrections=corrections)

    return done(DISPUTED, "the two readings disagree on this row and the second does "
                "not satisfy the rule without breaking another, so both are shown and "
                "neither is used", rows=view)


def _third_reading(ctx, spec, target: int, by_index: dict[int, Row],
                   failing: dict[int, set], page: int, readers) -> dict[str, Any]:
    """A tie-break for a row two readers agree on and a rule rejects.

    The first reader transcribes the page once more at its re-read resolution. This can
    do exactly one thing: replace that one row, under the same guards as any correction,
    if its transcription differs and makes the rule pass. If it agrees with the other two,
    cannot be matched to the row, is unavailable, or differs without satisfying the
    rule, nothing changes and the two-reader finding stands.

    It is a third transcription, not a third independent reader: same model as the
    first reading, different image. It guards against a misreading shared at the
    reading resolution, which is the failure this method was observed to have.
    """
    out: dict[str, Any] = {"corrections": None, "touched": set(), "view": [], "note": ""}
    reader = ctx.proposers.get(ctx.tier)
    if reader is None or not getattr(reader, "supports_regions", False):
        out["note"] = "No third reading was available."
        return out
    rows, why = read_page(ctx, spec, page, "self")
    if rows is None:
        out["note"] = f"A third reading was not obtained ({why})."
        return out
    first = [r for r in ctx.statement.rows if r.page == page]
    pairs3 = align(first, rows)
    if target not in pairs3:
        out["note"] = "A third reading could not be matched to this row."
        return out
    out["view"] = [{"row": target, "first": _show(by_index[target]),
                    "third": _show(pairs3[target]),
                    "agree": _row_view(by_index[target]) == _row_view(pairs3[target])}]
    if _row_view(by_index[target]) == _row_view(pairs3[target]):
        out["note"] = ("A third reading, by the first reader at higher resolution, "
                       "has the same figures.")
        return out

    # Only the row the two readers agreed on is offered the third reading. A
    # neighbouring row is not: nothing has established that the readers agree on it,
    # and it gets its own second look in its own turn.
    third_readers = (readers[0], readers[0] + " (re-read at higher resolution)")
    got = _apply(ctx, spec, [(by_index[target], pairs3[target])], page,
                 third_readers, "third_reading")
    if got is not None:
        for c in got:
            c["note"] = ("two readers had agreed on the first reading; a third "
                         "reading differs and satisfies the rule")
        out["corrections"], out["touched"] = got, {target}
        return out
    out["note"] = ("A third reading differs on this row but does not satisfy the rule, "
                   "so it is not used.")
    return out


def _operands_agree(ctx, spec, target: int, pairs: dict[int, Row], page: int,
                    source: str) -> tuple[bool, str]:
    """Did the two readers independently agree on every figure carried into this row?

    "Independently" matters. If a neighbouring row was corrected, its current figures
    are the second reader's. What is compared is what the FIRST reader originally
    transcribed there against the second reader's, because a figure only one of them
    ever produced is not agreed on.
    """
    for other in carried_from(ctx.statement, spec, target):
        if other is OPENING:
            mine = _minor(ctx.statement.header.opening_balance)
            read_page(ctx, spec, 1, source)
            theirs = _second_opening(ctx)
            if theirs is None:
                return False, ("this row starts from the opening balance, and the second "
                               "reader's opening balance is not available to confirm it")
            if mine != theirs:
                return False, "the two readers disagree on the opening balance"
            continue
        if other.page == page:
            match = pairs.get(other.index)
        else:
            rows, why = read_page(ctx, spec, other.page, source)
            if rows is None:
                return False, (f"a figure carried into this row is on page {other.page}, "
                               f"which could not be read a second time: {why}")
            match = align([r for r in ctx.statement.rows if r.page == other.page],
                          rows).get(other.index)
        if match is None:
            return False, (f"row {other.index}, which this row's rule is computed from, "
                           f"could not be matched in the second reading")
        mine = ctx.first_values.get(other.index,
                                    (_date_key(other), _minor(other.balance)))
        theirs = (_date_key(match), _minor(match.balance))
        if mine != theirs:
            return False, (f"the two readers did not independently agree on the date and "
                           f"balance of row {other.index}, which this row's rule is "
                           f"computed from")
        # And what they agreed on must be what the row holds now. After a third-reading
        # correction a row can hold a figure neither of the two readers produced, and
        # their agreement on the old figure says nothing about the new one.
        if (_date_key(other), _minor(other.balance)) != theirs:
            return False, (f"row {other.index}, which this row's rule is computed from, "
                           f"now holds a date or balance that the two readers did not "
                           f"agree on")
    return True, ""


def _apply(ctx, spec, attempt, page: int, readers,
           method: str = "second_reader") -> list[dict[str, Any]] | None:
    """Put the second reading on these rows and keep it only if the rules say so.

    Kept when every touched row then passes every rule, no check fails that was not
    failing before, and at least one failure is gone. Otherwise the first reading is
    restored and None is returned.
    """
    before = _failure_ids(ctx.inv_report)
    saved = [(a, {c: getattr(a, c) for c in REPLACED_COLUMNS}) for a, _ in attempt]
    for a, b in attempt:
        for c in REPLACED_COLUMNS:
            # The date is taken from the second reader only where the two readers
            # actually read a different date; the same date written differently
            # ("03-01-2024" against "03-01-2024 17:04") is not a correction.
            if c == "date" and _date_key(a) == _date_key(b):
                continue
            setattr(a, c, getattr(b, c))
    report = run_invariants(ctx.statement, spec)
    after = _failure_ids(report)
    touched = {a.index for a, _ in attempt}
    rows_ok = all(r.ok for r in report.results
                  if r.location.scope is Scope.ROW and r.location.row_index in touched)
    if not (rows_ok and after < before):
        for a, old in saved:
            for c in REPLACED_COLUMNS:
                setattr(a, c, old[c])
        return None

    ctx.inv_report = report
    ctx.from_second |= touched
    for a, old in saved:
        # What the first reader originally had here, for later operand checks.
        ctx.first_values.setdefault(
            a.index, (old["date"].value.isoformat()
                      if hasattr(old["date"].value, "isoformat")
                      else str(old["date"].raw or ""), _minor(old["balance"])))
    corrections = []
    for a, old in saved:
        for c in REPLACED_COLUMNS:
            new = getattr(a, c)
            if c == "date":
                changed = str(old[c].value) != str(new.value)
            else:
                # An unreadable cell and a blank one both hold no value; replacing one
                # by the other is still a change to what the reading says.
                changed = (_minor(old[c]) != _minor(new)
                           or (old[c].value is None and new.value is None
                               and (old[c].raw or "").strip() != (new.raw or "").strip()))
            if changed:
                corrections.append({
                    "row": a.index, "page": page, "field": c,
                    "first_reading": old[c].raw or "", "corrected": new.raw or "",
                    "method": method,
                    "first_reader": readers[0], "second_reader": readers[1],
                    "confirmed_by": sorted({r.invariant_id for r in report.results
                                            if r.ok and r.location.scope is Scope.ROW
                                            and r.location.row_index == a.index}),
                })
    return corrections


def _sweep_page(ctx, spec, by_index: dict[int, Row], pairs: dict[int, Row], page: int,
                readers, method: str = "second_reader") -> list[dict[str, Any]]:
    """Offer the second reading to every other failing row of an already re-read page.

    Only rows that fail a rule themselves are offered it, alone first and then together
    with an adjacent failing row (a misread balance breaks its own row and the next).
    A row that passes is never edited, and a row the readers agree on is left for its
    own finding.
    """
    out: list[dict[str, Any]] = []
    progress = True
    while progress:
        progress = False
        failing = _failing_rows(ctx.inv_report)

        def candidate(i: int) -> bool:
            row = by_index.get(i)
            return (row is not None and row.page == page and i in failing
                    and failing[i] <= SUPPORTED_FAILURES
                    and i in pairs and i not in ctx.from_second
                    and _row_view(row) != _row_view(pairs[i]))

        for i in sorted(failing):
            if not candidate(i):
                continue
            tries = [[i]] + [[i, j] for j in (i + 1, i - 1) if candidate(j)]
            for rows in tries:
                got = _apply(ctx, spec, [(by_index[k], pairs[k]) for k in rows],
                             page, readers, method)
                if got is not None:
                    out += got
                    progress = True
                    break
            if progress:
                break
    return out


def _span(rows) -> str:
    rows = sorted(rows)
    return str(rows) if len(rows) <= 6 else f"{rows[0]}..{rows[-1]} ({len(rows)} rows)"


def _show(row: Row) -> dict[str, str]:
    return {c: (getattr(row, c).raw or "") for c in ("date",) + AMOUNT_COLUMNS}
