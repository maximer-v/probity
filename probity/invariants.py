"""The invariant engine: exact accounting checks that say *where* they broke.

The point of the row-level running balance is not that it is a stronger check than the
global one. It is that its failures are *located*. A global check answers "does this
document balance"; ROW_BAL answers "row 23 is off by 500 minor units, and the two
candidate explanations are the amount on row 23 or the balance on row 22".

Every check is exact integer arithmetic on minor units (P2). Every failure carries the
operands, so the trace log can show the subtraction that failed rather than a verdict.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field as dc_field
from typing import Any, Callable, Iterable

from .money import Money
from .records import Row, Statement


class Scope(enum.StrEnum):
    DOCUMENT = "document"
    PAGE = "page"
    ROW = "row"


@dataclass(frozen=True)
class Location:
    """Where a failure is, precisely enough to crop the page and re-read it."""

    scope: Scope
    row_index: int | None = None
    page: int | None = None
    fields: tuple[str, ...] = ()

    def key(self) -> str:
        if self.scope is Scope.ROW:
            return f"row:{self.row_index}"
        if self.scope is Scope.PAGE:
            return f"page:{self.page}"
        return "document"

    def to_json(self) -> dict[str, Any]:
        return {"scope": str(self.scope), "row_index": self.row_index,
                "page": self.page, "fields": list(self.fields)}


@dataclass
class InvariantResult:
    """One evaluation of one invariant at one location."""

    invariant_id: str
    ok: bool
    location: Location
    # Why, in enough detail to reconstruct the arithmetic without re-running anything.
    code: str = "OK"
    expected: int | None = None     # minor units
    actual: int | None = None
    delta: int | None = None
    operands: dict[str, Any] = dc_field(default_factory=dict)
    message: str = ""
    # Which fields this result is evidence *about*. Used to stamp `verified_by`
    # only on the fields the check actually constrains (P3).
    witnesses: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "invariant": self.invariant_id, "ok": self.ok, "code": self.code,
            "location": self.location.to_json(), "expected": self.expected,
            "actual": self.actual, "delta": self.delta,
            "operands": self.operands, "message": self.message,
            "witnesses": list(self.witnesses),
        }


# Failure codes. These are the vocabulary the logs and the metrics speak.
class Code:
    OK = "OK"
    MISMATCH = "MISMATCH"                     # the arithmetic does not hold
    UNREADABLE_OPERAND = "UNREADABLE_OPERAND"  # a value needed by the check is missing
    NOT_APPLICABLE = "NOT_APPLICABLE"          # the layout does not carry what is needed
    OUT_OF_ORDER = "OUT_OF_ORDER"
    OUT_OF_PERIOD = "OUT_OF_PERIOD"
    COUNT_MISMATCH = "COUNT_MISMATCH"
    DUPLICATE_ROW = "DUPLICATE_ROW"
    BOTH_SIDES_PRESENT = "BOTH_SIDES_PRESENT"


@dataclass(frozen=True)
class Invariant:
    id: str
    scope: Scope
    description: str
    evaluate: Callable[[Statement, Any], list[InvariantResult]]
    # Which classes of field the invariant can act as a witness for.
    witness_fields: tuple[str, ...] = ()


def _money(f) -> Money | None:
    return f.value if isinstance(f.value, Money) else None


def balances_equal(a: int, b: int) -> bool:
    """P2 in one function: two amounts agree only if they are the same integer.

    Every arithmetic comparison in this module goes through here, so the no-tolerance
    claim is enforced in a single place instead of being re-stated at four call sites
    where one of them could later drift. The library offers no way to turn exactness
    off, because a tolerance setting is a blind spot that a caller could enable in
    production without meaning to.
    """
    return a == b


# --------------------------------------------------------------------------- ROW_BAL

def _eval_row_bal(st: Statement, spec) -> list[InvariantResult]:
    """balance[i] == balance[i-1] + credit[i] - debit[i], seeded by the opening balance.

    Chaining matters: one wrong amount breaks exactly one row, while one wrong balance
    breaks two consecutive rows. The result codes preserve that signature so the repair
    step knows which cell to re-read first.
    """
    out: list[InvariantResult] = []
    opening = _money(st.header.opening_balance)
    prev: Money | None = opening
    prev_src = "header.opening_balance"

    if not st.rows:
        return [InvariantResult("ROW_BAL", False, Location(Scope.DOCUMENT),
                                code=Code.UNREADABLE_OPERAND, message="no rows extracted")]

    # The chain runs in time order, which is the printed order only on an ascending
    # statement. Some banks print newest first; walking those top to bottom produces a
    # failure on every single row, which looks like a broken document rather than a
    # misread sort order, so the spec declares the direction and we follow it.
    sequence = st.rows if spec.columns.sort_order == "ascending" else list(reversed(st.rows))

    for row in sequence:
        loc = Location(Scope.ROW, row_index=row.index, page=row.page,
                       fields=("debit", "credit", "balance"))
        bal = _money(row.balance)
        delta = row.signed_amount(st.currency)

        missing = []
        if prev is None:
            missing.append(prev_src)
        if bal is None:
            missing.append(f"row[{row.index}].balance")
        if delta is None:
            missing.append(f"row[{row.index}].debit/credit")
        if missing:
            out.append(InvariantResult(
                "ROW_BAL", False, loc, code=Code.UNREADABLE_OPERAND,
                operands={"missing": missing},
                message=f"cannot check row {row.index}: unreadable {', '.join(missing)}"))
            prev, prev_src = bal, f"row[{row.index}].balance"
            continue

        if (row.debit.value is not None and row.credit.value is not None
                and _money(row.debit) and _money(row.credit)
                and _money(row.debit).minor != 0 and _money(row.credit).minor != 0):
            out.append(InvariantResult(
                "ROW_BAL", False, loc, code=Code.BOTH_SIDES_PRESENT,
                operands={"debit": _money(row.debit).minor, "credit": _money(row.credit).minor},
                message=f"row {row.index} has a non-zero debit and credit at once"))

        expected = prev + delta
        ok = balances_equal(expected.minor, bal.minor)
        out.append(InvariantResult(
            "ROW_BAL", ok, loc,
            code=Code.OK if ok else Code.MISMATCH,
            expected=expected.minor, actual=bal.minor,
            delta=None if ok else bal.minor - expected.minor,
            operands={"prev_balance": prev.minor, "prev_source": prev_src,
                      "debit": (_money(row.debit).minor if _money(row.debit) else 0),
                      "credit": (_money(row.credit).minor if _money(row.credit) else 0)},
            message=("" if ok else
                     f"row {row.index}: {prev.minor} + {delta.minor} = {expected.minor}, "
                     f"but the balance column reads {bal.minor} "
                     f"(off by {bal.minor - expected.minor})"),
            witnesses=("debit", "credit", "balance") if ok else (),
        ))
        prev, prev_src = bal, f"row[{row.index}].balance"
    return out


# ------------------------------------------------------------------------ GLOBAL_BAL

def _eval_global_bal(st: Statement, spec) -> list[InvariantResult]:
    opening, closing = _money(st.header.opening_balance), _money(st.header.closing_balance)
    if opening is None or closing is None:
        return [InvariantResult("GLOBAL_BAL", False, Location(Scope.DOCUMENT),
                                code=Code.UNREADABLE_OPERAND,
                                operands={"opening": opening and opening.minor,
                                          "closing": closing and closing.minor},
                                message="opening or closing balance unreadable")]
    total = Money.zero(st.currency)
    unreadable: list[int] = []
    for row in st.rows:
        d = row.signed_amount(st.currency)
        if d is None:
            unreadable.append(row.index)
        else:
            total = total + d
    if unreadable:
        return [InvariantResult("GLOBAL_BAL", False, Location(Scope.DOCUMENT),
                                code=Code.UNREADABLE_OPERAND,
                                operands={"rows_unreadable": unreadable},
                                message=f"{len(unreadable)} rows have no readable amount")]
    expected = opening + total
    ok = balances_equal(expected.minor, closing.minor)
    return [InvariantResult(
        "GLOBAL_BAL", ok, Location(Scope.DOCUMENT, fields=("opening_balance", "closing_balance")),
        code=Code.OK if ok else Code.MISMATCH,
        expected=expected.minor, actual=closing.minor,
        delta=None if ok else closing.minor - expected.minor,
        operands={"opening": opening.minor, "sum_signed": total.minor, "closing": closing.minor},
        message=("" if ok else
                 f"opening {opening.minor} + movements {total.minor} = {expected.minor}, "
                 f"closing balance reads {closing.minor}"),
        witnesses=("opening_balance", "closing_balance") if ok else (),
    )]


# ----------------------------------------------------------------- LAST_ROW_EQ_CLOSING

def _eval_last_row(st: Statement, spec) -> list[InvariantResult]:
    closing = _money(st.header.closing_balance)
    if not st.rows or closing is None:
        return [InvariantResult("LAST_ROW_EQ_CLOSING", False, Location(Scope.DOCUMENT),
                                code=Code.UNREADABLE_OPERAND,
                                message="no rows or no closing balance")]
    last = st.rows[-1] if spec.columns.sort_order == "ascending" else st.rows[0]
    bal = _money(last.balance)
    if bal is None:
        return [InvariantResult("LAST_ROW_EQ_CLOSING", False,
                                Location(Scope.ROW, row_index=last.index, page=last.page,
                                         fields=("balance",)),
                                code=Code.UNREADABLE_OPERAND,
                                message=f"balance on the final row ({last.index}) unreadable")]
    ok = balances_equal(bal.minor, closing.minor)
    return [InvariantResult(
        "LAST_ROW_EQ_CLOSING", ok,
        Location(Scope.ROW, row_index=last.index, page=last.page, fields=("balance",)),
        code=Code.OK if ok else Code.MISMATCH,
        expected=closing.minor, actual=bal.minor,
        delta=None if ok else bal.minor - closing.minor,
        operands={"final_row": last.index},
        message="" if ok else f"final row balance {bal.minor} vs closing {closing.minor}",
        witnesses=("balance", "closing_balance") if ok else (),
    )]


# --------------------------------------------------------------------- PAGE_SUBTOTAL

def _eval_page_subtotal(st: Statement, spec) -> list[InvariantResult]:
    out: list[InvariantResult] = []
    pages = sorted({r.page for r in st.rows})
    for page in pages:
        field = st.carried_forward.get(page)
        rows = st.rows_on_page(page)
        loc = Location(Scope.PAGE, page=page, fields=("carried_forward",))
        if page == pages[-1] and field is None:
            # The final page carries nothing forward; its closing figure is the
            # statement's closing balance, which LAST_ROW_EQ_CLOSING already checks.
            continue
        if field is None or not isinstance(field.value, Money):
            out.append(InvariantResult("PAGE_SUBTOTAL", False, loc, code=Code.NOT_APPLICABLE,
                                       message=f"page {page} has no readable carry-forward"))
            continue
        if not rows:
            out.append(InvariantResult("PAGE_SUBTOTAL", False, loc, code=Code.UNREADABLE_OPERAND,
                                       message=f"page {page} has no rows"))
            continue
        bal = _money(rows[-1].balance)
        if bal is None:
            out.append(InvariantResult("PAGE_SUBTOTAL", False, loc, code=Code.UNREADABLE_OPERAND,
                                       message=f"last balance on page {page} unreadable"))
            continue
        ok = balances_equal(bal.minor, field.value.minor)
        out.append(InvariantResult(
            "PAGE_SUBTOTAL", ok, loc, code=Code.OK if ok else Code.MISMATCH,
            expected=field.value.minor, actual=bal.minor,
            delta=None if ok else bal.minor - field.value.minor,
            operands={"last_row": rows[-1].index},
            message="" if ok else
                    f"page {page} carry-forward {field.value.minor} vs last row {bal.minor}",
            witnesses=("carried_forward", "balance") if ok else (),
        ))
    return out


# ------------------------------------------------------------------------- DATE_ORDER

def _eval_date_order(st: Statement, spec) -> list[InvariantResult]:
    from datetime import date as _date

    out: list[InvariantResult] = []
    start = st.header.period_start.value if isinstance(st.header.period_start.value, _date) else None
    end = st.header.period_end.value if isinstance(st.header.period_end.value, _date) else None
    prev: _date | None = None
    ascending = spec.columns.sort_order == "ascending"

    for row in st.rows:
        loc = Location(Scope.ROW, row_index=row.index, page=row.page, fields=("date",))
        d = row.date.value if isinstance(row.date.value, _date) else None
        if d is None:
            out.append(InvariantResult("DATE_ORDER", False, loc, code=Code.UNREADABLE_OPERAND,
                                       message=f"row {row.index} has no readable date",
                                       operands={"raw": row.date.raw, "error": row.date.error_code}))
            continue
        if start and d < start:
            out.append(InvariantResult("DATE_ORDER", False, loc, code=Code.OUT_OF_PERIOD,
                                       operands={"date": d.isoformat(), "period_start": start.isoformat()},
                                       message=f"row {row.index} dated {d} is before the period start {start}"))
        elif end and d > end:
            out.append(InvariantResult("DATE_ORDER", False, loc, code=Code.OUT_OF_PERIOD,
                                       operands={"date": d.isoformat(), "period_end": end.isoformat()},
                                       message=f"row {row.index} dated {d} is after the period end {end}"))
        elif prev is not None and ((d < prev) if ascending else (d > prev)):
            out.append(InvariantResult("DATE_ORDER", False, loc, code=Code.OUT_OF_ORDER,
                                       operands={"date": d.isoformat(), "previous": prev.isoformat(),
                                                 "sort_order": spec.columns.sort_order},
                                       message=f"row {row.index} dated {d} breaks {spec.columns.sort_order} order "
                                               f"after {prev}"))
        else:
            out.append(InvariantResult("DATE_ORDER", True, loc, witnesses=("date",)))
        prev = d
    return out


# ------------------------------------------------------------------------------ COUNT

def _eval_count(st: Statement, spec) -> list[InvariantResult]:
    declared = st.header.tx_count.value
    loc = Location(Scope.DOCUMENT, fields=("tx_count",))
    if not isinstance(declared, int):
        return [InvariantResult("COUNT", False, loc, code=Code.NOT_APPLICABLE,
                                message="the statement declares no transaction count")]
    ok = declared == len(st.rows)
    return [InvariantResult("COUNT", ok, loc, code=Code.OK if ok else Code.COUNT_MISMATCH,
                            expected=declared, actual=len(st.rows),
                            delta=None if ok else len(st.rows) - declared,
                            message="" if ok else
                                    f"the statement declares {declared} transactions, {len(st.rows)} were read",
                            witnesses=("tx_count",) if ok else ())]


# -------------------------------------------------------------------------- NO_DUP_ROW

def _eval_no_dup(st: Statement, spec) -> list[InvariantResult]:
    """A duplicated line is the one source corruption the balance chain cannot see.

    If a row is printed twice *and* the balance column is printed twice with it, every
    ROW_BAL check still passes. Only the repeated (date, description, amount, balance)
    tuple gives it away, which is why this check exists separately.
    """
    out: list[InvariantResult] = []
    seen: dict[tuple, int] = {}
    for row in st.rows:
        key = (
            row.date.value.isoformat() if hasattr(row.date.value, "isoformat") else row.date.value,
            (row.description.value or "").strip().lower() if isinstance(row.description.value, str) else None,
            _money(row.debit).minor if _money(row.debit) else None,
            _money(row.credit).minor if _money(row.credit) else None,
            # The balance is part of the identity, and it is what separates a repeat
            # from a duplicate. Two identical coffees on the same day are an ordinary
            # thing for a statement to contain, and they carry *different* running
            # balances. A line that was printed twice carries the same balance twice.
            # Without this the check fires on honest repetition, which is the fastest
            # way to make a flag worthless.
            _money(row.balance).minor if _money(row.balance) else None,
        )
        if key[0] is None or key[1] is None or key[4] is None:
            continue
        if key in seen:
            out.append(InvariantResult(
                "NO_DUP_ROW", False,
                Location(Scope.ROW, row_index=row.index, page=row.page,
                         fields=("date", "description", "debit", "credit")),
                code=Code.DUPLICATE_ROW,
                operands={"first_seen_row": seen[key], "key": list(key)},
                message=f"row {row.index} repeats row {seen[key]} exactly"))
        else:
            seen[key] = row.index
    if not out:
        return [InvariantResult("NO_DUP_ROW", True, Location(Scope.DOCUMENT))]
    return out


REGISTRY: dict[str, Invariant] = {
    inv.id: inv for inv in [
        Invariant("ROW_BAL", Scope.ROW,
                  "balance[i] == balance[i-1] + credit[i] - debit[i], exact",
                  _eval_row_bal, ("debit", "credit", "balance")),
        Invariant("GLOBAL_BAL", Scope.DOCUMENT,
                  "opening + sum(credit) - sum(debit) == closing",
                  _eval_global_bal, ("opening_balance", "closing_balance")),
        Invariant("LAST_ROW_EQ_CLOSING", Scope.ROW,
                  "the balance on the final row equals the closing balance",
                  _eval_last_row, ("balance", "closing_balance")),
        Invariant("PAGE_SUBTOTAL", Scope.PAGE,
                  "each page's carry-forward equals the last balance printed on it",
                  _eval_page_subtotal, ("carried_forward", "balance")),
        Invariant("DATE_ORDER", Scope.ROW,
                  "row dates lie inside the period and follow the declared sort order",
                  _eval_date_order, ("date",)),
        Invariant("COUNT", Scope.DOCUMENT,
                  "the number of rows equals the declared transaction count",
                  _eval_count, ("tx_count",)),
        Invariant("NO_DUP_ROW", Scope.ROW,
                  "no transaction line is repeated exactly",
                  _eval_no_dup, ()),
    ]
}


@dataclass
class VerificationReport:
    """Everything the invariant engine concluded about one candidate reading."""

    results: list[InvariantResult]

    @property
    def failures(self) -> list[InvariantResult]:
        return [r for r in self.results if not r.ok]

    @property
    def all_passed(self) -> bool:
        return not self.failures

    def failed_locations(self) -> list[Location]:
        """Distinct locations to repair, innermost first (rows before pages before doc)."""
        order = {Scope.ROW: 0, Scope.PAGE: 1, Scope.DOCUMENT: 2}
        seen: dict[str, Location] = {}
        for r in self.failures:
            seen.setdefault(r.location.key(), r.location)
        return sorted(seen.values(), key=lambda l: (order[l.scope], l.row_index or 0, l.page or 0))

    def is_localized(self) -> bool:
        """True when at least one failure points at a row or a page, so a crop can fix it.

        Note that a single misread amount breaks the row it is on *and* the document's
        global balance, because the global check is a sum over the same rows. Requiring
        that no document-scope failure be present would therefore refuse to repair the
        most common error of all. What must not be repaired is a failure with *no*
        located companion: sending an unlocated failure to a repair step is how a model
        is invited to invent a value that makes the total agree.
        """
        return any(r.location.scope is not Scope.DOCUMENT for r in self.failures)

    def has_unlocated_failure_only(self) -> bool:
        """True when the only thing known is that the document does not add up."""
        return bool(self.failures) and not self.is_localized()

    def by_invariant(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for r in self.results:
            slot = out.setdefault(r.invariant_id, {"pass": 0, "fail": 0})
            slot["pass" if r.ok else "fail"] += 1
        return out

    def codes(self) -> list[str]:
        return sorted({r.code for r in self.failures})

    def to_json(self) -> dict[str, Any]:
        return {"all_passed": self.all_passed, "by_invariant": self.by_invariant(),
                "failure_codes": self.codes(),
                "results": [r.to_json() for r in self.results]}

    def explain(self, limit: int = 12) -> str:
        """Human-readable forensics: the arithmetic that failed, not a verdict."""
        if self.all_passed:
            counts = self.by_invariant()
            return "all invariants passed (" + ", ".join(
                f"{k} {v['pass']}/{v['pass'] + v['fail']}" for k, v in sorted(counts.items())) + ")"
        lines = [f"{len(self.failures)} invariant failure(s):"]
        for r in self.failures[:limit]:
            lines.append(f"  [{r.invariant_id}/{r.code}] {r.location.key()}: {r.message or '-'}")
        if len(self.failures) > limit:
            lines.append(f"  ... and {len(self.failures) - limit} more")
        return "\n".join(lines)


def run_invariants(st: Statement, spec, ids: Iterable[str] | None = None) -> VerificationReport:
    """Evaluate the spec's invariants against a candidate reading."""
    chosen = list(ids) if ids is not None else list(spec.invariant_ids)
    results: list[InvariantResult] = []
    for inv_id in chosen:
        inv = REGISTRY[inv_id]
        results.extend(inv.evaluate(st, spec))
    return VerificationReport(results)


def stamp_witnesses(st: Statement, report: VerificationReport) -> None:
    """Record on each field which invariants confirmed it (P3).

    A derived field never gets a witness from the invariant that derived it: the
    field's provenance is DERIVED, and :attr:`Field.status` refuses VERIFIED for those
    regardless of what is stamped here.
    """
    by_row: dict[int, Row] = {r.index: r for r in st.rows}
    for res in report.results:
        if not res.ok:
            continue
        loc = res.location
        if loc.scope is Scope.ROW and loc.row_index in by_row:
            row = by_row[loc.row_index]
            for f in row.fields():
                if f.name in res.witnesses and res.invariant_id not in f.verified_by:
                    f.verified_by.append(res.invariant_id)
        elif loc.scope is Scope.PAGE and loc.page is not None:
            f = st.carried_forward.get(loc.page)
            if f is not None and "carried_forward" in res.witnesses:
                if res.invariant_id not in f.verified_by:
                    f.verified_by.append(res.invariant_id)
        else:
            for f in st.header.fields():
                if f.name in res.witnesses and res.invariant_id not in f.verified_by:
                    f.verified_by.append(res.invariant_id)
