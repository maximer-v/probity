"""The checks, and above all what they do *not* claim to catch."""

from __future__ import annotations

import inspect
from datetime import date

import pytest

from probity.invariants import Code, Scope, run_invariants, stamp_witnesses
from probity.money import Money
from probity.records import Field, Header, Provenance, Row, Statement, Status
from probity.spec import DocumentSpec


def make_spec(**over):
    data = {
        "doc_type": "test.running_balance", "locale": "es-VE", "currency_default": "VES",
        "invariants": ["ROW_BAL", "GLOBAL_BAL", "LAST_ROW_EQ_CLOSING", "DATE_ORDER",
                       "COUNT", "NO_DUP_ROW"],
        "columns": {"mode": "debit_credit", "has_running_balance": True},
    }
    data.update(over)
    return DocumentSpec.from_dict(data)


def m(v):
    return Money(v, "VES")


def build(rows, opening=10000, closing=None, tx_count=None, ccy="VES"):
    st = Statement("t", ccy)
    st.header.opening_balance = Field("opening_balance", str(opening), m(opening),
                                      Provenance.TEXT_LAYER)
    bal = opening
    built = []
    for i, (d, c, day) in enumerate(rows):
        bal = bal + (c or 0) - (d or 0)
        row = Row(index=i, page=1)
        row.date = Field("date", str(day), day, Provenance.TEXT_LAYER)
        row.description = Field("description", f"TX {i}", f"TX {i}", Provenance.TEXT_LAYER)
        if d:
            row.debit = Field("debit", str(d), m(d), Provenance.TEXT_LAYER)
        if c:
            row.credit = Field("credit", str(c), m(c), Provenance.TEXT_LAYER)
        row.balance = Field("balance", str(bal), m(bal), Provenance.TEXT_LAYER)
        built.append(row)
    st.rows = built
    st.header.closing_balance = Field("closing_balance", str(bal),
                                      m(closing if closing is not None else bal),
                                      Provenance.TEXT_LAYER)
    st.header.period_start = Field("period_start", "", date(2026, 1, 1), Provenance.TEXT_LAYER)
    st.header.period_end = Field("period_end", "", date(2026, 12, 31), Provenance.TEXT_LAYER)
    st.header.tx_count = Field("tx_count", "", tx_count if tx_count is not None else len(rows),
                               Provenance.TEXT_LAYER)
    return st


ROWS = [(None, 5000, date(2026, 1, 2)), (2000, None, date(2026, 1, 3)),
        (None, 1500, date(2026, 1, 5)), (750, None, date(2026, 1, 8))]


def test_clean_statement_passes_everything():
    report = run_invariants(build(ROWS), make_spec())
    assert report.all_passed, report.explain()


def test_wrong_amount_breaks_exactly_one_row_and_names_it():
    st = build(ROWS)
    st.rows[1].debit = Field("debit", "3000", m(3000), Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec())
    row_fails = [r for r in report.failures if r.invariant_id == "ROW_BAL"]
    assert len(row_fails) == 1
    assert row_fails[0].location.row_index == 1
    # delta is actual minus expected: a debit 1000 too large leaves the printed balance
    # 1000 above what the amounts imply.
    assert row_fails[0].delta == 1000
    assert "row 1" in row_fails[0].message


def test_wrong_balance_breaks_two_consecutive_rows():
    """The signature that tells a repair step which cell to re-read first."""
    st = build(ROWS)
    st.rows[1].balance = Field("balance", "x", m(999999), Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec())
    broken = sorted(r.location.row_index for r in report.failures
                    if r.invariant_id == "ROW_BAL")
    assert broken == [1, 2]


def test_global_check_alone_misses_two_errors_that_cancel():
    """Why the row check is the primary one."""
    st = build(ROWS)
    st.rows[0].credit = Field("credit", "", m(6000), Provenance.TEXT_LAYER)
    st.rows[2].credit = Field("credit", "", m(500), Provenance.TEXT_LAYER)
    g = run_invariants(st, make_spec(invariants=["GLOBAL_BAL"]))
    assert g.all_passed, "the global check cannot see offsetting errors"
    r = run_invariants(st, make_spec(invariants=["ROW_BAL"]))
    assert not r.all_passed
    # Each altered amount breaks its own row. The chain is seeded from each row's
    # printed balance, so row 1, sitting between them, still holds.
    assert {x.location.row_index for x in r.failures} == {0, 2}


def test_invented_but_balancing_values_pass_every_invariant():
    """The limit of self-consistency, asserted rather than assumed.

    A ledger rewritten to be internally exact satisfies every check here. Only
    grounding can object, which is why the framework requires both.
    """
    fabricated = [(None, 7777, date(2026, 1, 2)), (3333, None, date(2026, 1, 4))]
    report = run_invariants(build(fabricated), make_spec())
    assert report.all_passed


def test_descending_statements_chain_the_other_way():
    st = build(ROWS)
    st.rows = list(reversed(st.rows))
    spec = make_spec(columns={"mode": "debit_credit", "has_running_balance": True,
                              "sort_order": "descending"},
                     invariants=["ROW_BAL", "LAST_ROW_EQ_CLOSING"])
    assert run_invariants(st, spec).all_passed


def test_duplicate_row_is_caught_even_though_the_chain_holds():
    st = build(ROWS)
    import copy
    dup = copy.deepcopy(st.rows[2])
    dup.index = 99
    st.rows.insert(3, dup)
    report = run_invariants(st, make_spec(invariants=["NO_DUP_ROW"]))
    assert not report.all_passed
    assert report.failures[0].code == Code.DUPLICATE_ROW


def test_count_mismatch_is_located_at_the_document():
    report = run_invariants(build(ROWS, tx_count=9), make_spec(invariants=["COUNT"]))
    assert report.failures[0].code == Code.COUNT_MISMATCH
    assert report.failures[0].expected == 9 and report.failures[0].actual == 4


def test_date_out_of_period_is_caught():
    st = build(ROWS)
    st.rows[2].date = Field("date", "", date(2020, 5, 5), Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec(invariants=["DATE_ORDER"]))
    codes = {r.code for r in report.failures}
    assert Code.OUT_OF_PERIOD in codes


def test_unreadable_operand_is_reported_not_treated_as_zero():
    st = build(ROWS)
    st.rows[1].balance = Field("balance", "???", None, Provenance.TEXT_LAYER,
                               error_code="UNEXPECTED_CHARS")
    report = run_invariants(st, make_spec(invariants=["ROW_BAL"]))
    codes = {r.code for r in report.failures}
    assert Code.UNREADABLE_OPERAND in codes


def test_one_cent_is_a_mismatch_and_there_is_no_way_to_configure_otherwise():
    """P2, pinned at the one place every arithmetic comparison goes through.

    A cent of tolerance is the most reasonable-sounding change anyone could make to this
    module, and it is a blind spot with a published size: a tolerance cannot detect a
    change smaller than itself. The library offers no setting for one, so nothing can
    turn exactness off in production by configuration.
    """
    from probity.invariants import balances_equal

    assert balances_equal(100, 100)
    assert not balances_equal(100, 101)
    assert not balances_equal(-1, 0)

    st = build(ROWS)
    # Move one balance by a single minor unit: the smallest change a statement can carry.
    st.rows[1].balance = Field("balance", "", m(st.rows[1].balance.value.minor + 1),
                               Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec(invariants=["ROW_BAL"]))
    assert not report.all_passed
    assert Code.MISMATCH in {f.code for f in report.failures}

    sig = inspect.signature(run_invariants)
    assert not any("toler" in p.lower() for p in sig.parameters), (
        "run_invariants must not take a tolerance argument")
    assert not any("toler" in name.lower() for name in dir(DocumentSpec)), (
        "a spec must not be able to request a tolerance")


def test_a_row_with_no_amount_printed_at_all_is_zero_movement():
    """An empty cell is not an unreadable one.

    A row carrying a date, a description and an unchanged balance but no amount is a real
    statement line -- 277 rows of the external corpus are exactly that. Since the blank
    credit cell on an ordinary debit row is already read as zero, a row blank on both
    sides has to read as zero too, or the same absence of ink would mean two things.
    """
    st = build(ROWS)
    st.rows[1].debit = Field("debit", "", None, Provenance.MISSING)
    st.rows[1].credit = Field("credit", "", None, Provenance.MISSING)
    # Make the balance column agree that nothing moved on that row.
    for row in st.rows[1:]:
        row.balance = Field("balance", "", m(row.balance.value.minor + 2000),
                            Provenance.TEXT_LAYER)
    st.header.closing_balance = Field("closing_balance", "",
                                      m(st.rows[-1].balance.value.minor),
                                      Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec(invariants=["ROW_BAL", "GLOBAL_BAL"]))
    assert report.all_passed, [f.message for f in report.failures]


def test_a_row_whose_amount_is_printed_but_unparseable_stays_unreadable():
    """The other half of the same rule: ink we could not parse is never assumed zero."""
    st = build(ROWS)
    st.rows[1].debit = Field("debit", "l.OOO", None, Provenance.TEXT_LAYER,
                             error_code="UNEXPECTED_CHARS")
    st.rows[1].credit = Field("credit", "", None, Provenance.MISSING)
    report = run_invariants(st, make_spec(invariants=["ROW_BAL"]))
    codes = {r.code for r in report.failures}
    assert Code.UNREADABLE_OPERAND in codes


def test_localisation_requires_a_located_failure():
    st = build(ROWS)
    st.rows[1].debit = Field("debit", "", m(3000), Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec())
    assert report.is_localized()
    assert not report.has_unlocated_failure_only()
    locs = [l.key() for l in report.failed_locations()]
    assert locs[0].startswith("row:")       # rows are offered for repair before the document


def test_only_global_failure_is_not_localized():
    st = build(ROWS)
    st.header.closing_balance = Field("closing_balance", "", m(1), Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec(invariants=["GLOBAL_BAL"]))
    assert not report.is_localized()
    assert report.has_unlocated_failure_only()


def test_witnesses_are_stamped_only_on_the_fields_a_check_constrains():
    st = build(ROWS)
    report = run_invariants(st, make_spec())
    stamp_witnesses(st, report)
    assert "ROW_BAL" in st.rows[0].balance.verified_by
    assert "ROW_BAL" not in st.rows[0].description.verified_by


def test_derived_values_can_never_be_verified(monkeypatch):
    """Principle P3, enforced by the type rather than by discipline."""
    f = Field("debit", "x", m(100), Provenance.DERIVED)
    f.grounded = True
    f.verified_by.append("ROW_BAL")
    assert f.status is Status.INFERRED


def test_spec_refuses_row_check_without_a_running_balance():
    with pytest.raises(ValueError, match="ROW_BAL requires"):
        DocumentSpec.from_dict({
            "doc_type": "cards", "locale": "en-US", "currency_default": "USD",
            "invariants": ["ROW_BAL"],
            "columns": {"has_running_balance": False}})


def test_verification_level_degrades_with_the_layout():
    assert make_spec().verification_level() == "ROW_LEVEL"
    weak = DocumentSpec.from_dict({
        "doc_type": "cards", "locale": "en-US", "currency_default": "USD",
        "invariants": ["GLOBAL_BAL"], "columns": {"has_running_balance": False}})
    assert weak.verification_level() == "DOCUMENT_LEVEL"


def test_legitimate_repeat_is_not_a_duplicate():
    """Two identical coffees on the same day are ordinary, not a defect.

    They carry different running balances; a line printed twice carries the same
    balance twice. Without that distinction the check fires on honest repetition.
    """
    rows = [(500, None, date(2026, 1, 3)), (500, None, date(2026, 1, 3))]
    st = build(rows)
    for row in st.rows:
        row.description = Field("description", "COFFEE", "COFFEE", Provenance.TEXT_LAYER)
    report = run_invariants(st, make_spec(invariants=["NO_DUP_ROW", "ROW_BAL"]))
    assert report.all_passed, report.explain()


def test_a_line_printed_twice_is_still_caught():
    import copy

    st = build(ROWS)
    dup = copy.deepcopy(st.rows[2])
    dup.index = 99
    st.rows.insert(3, dup)
    report = run_invariants(st, make_spec(invariants=["NO_DUP_ROW"]))
    assert not report.all_passed
    assert report.failures[0].code == Code.DUPLICATE_ROW
