"""Grounding catches what the arithmetic cannot, and repair must not be able to cheat."""

from __future__ import annotations

from datetime import date

import pytest

from probity.grounding import (BBox, DocumentIndex, GroundingCode, PageIndex, Token,
                              ground_field, ground_statement)
from probity.money import Money, get_locale
from probity.records import Field, Provenance, Row, Statement, Status
from probity.repair import build_repair_request
from probity.spec import DocumentSpec

ES = get_locale("es-VE")


def page_with(words: list[tuple[str, float, float]]) -> DocumentIndex:
    idx = PageIndex(page=1, width=595, height=842)
    for text, x, y in words:
        idx.tokens.append(Token(text, BBox(1, x, y, x + 40, y + 10), "text_layer"))
    return DocumentIndex(pages={1: idx}, sources=("text_layer",))


def test_value_printed_where_claimed_is_grounded():
    index = page_with([("1.234,56", 100, 200)])
    f = Field("balance", "1.234,56", Money(123456, "VES"), Provenance.TEXT_LAYER,
              BBox(1, 100, 200, 140, 210))
    res = ground_field(f, index, ES)
    assert res.ok and res.code is GroundingCode.GROUNDED


def test_invented_value_is_not_on_the_page():
    """The error class no invariant can catch: a value chosen to make totals agree."""
    index = page_with([("1.234,56", 100, 200)])
    f = Field("balance", "9.999,99", Money(999999, "VES"), Provenance.LLM,
              BBox(1, 100, 200, 140, 210))
    res = ground_field(f, index, ES)
    assert not res.ok
    assert res.code is GroundingCode.BOX_SAYS_OTHERWISE
    assert "1.234,56" in (res.found_text or "")


def test_value_on_the_page_but_in_the_wrong_place():
    index = page_with([("1.234,56", 400, 700)])
    f = Field("balance", "1.234,56", Money(123456, "VES"), Provenance.LLM,
              BBox(1, 100, 200, 140, 210))
    res = ground_field(f, index, ES)
    assert not res.ok and res.code is GroundingCode.WRONG_PLACE


def test_a_value_with_no_box_cannot_be_confirmed():
    """An agent types a number into JSON; nothing locates it. That must not pass."""
    index = page_with([("1.234,56", 100, 200)])
    f = Field("balance", "1.234,56", Money(123456, "VES"), Provenance.LLM, None)
    res = ground_field(f, index, ES)
    assert not res.ok and res.code is GroundingCode.NO_BBOX


def test_grounding_matches_across_split_tokens():
    """Statements split "1.234,56" into pieces often enough to matter."""
    index = page_with([("1.234", 100, 200), (",56", 122, 200)])
    f = Field("balance", "1.234,56", Money(123456, "VES"), Provenance.OCR,
              BBox(1, 100, 200, 165, 210))
    res = ground_field(f, index, ES)
    assert res.ok


def test_status_requires_both_grounding_and_a_witness():
    f = Field("balance", "1", Money(1, "VES"), Provenance.TEXT_LAYER)
    f.grounded = True
    assert f.status is Status.UNVERIFIED       # grounded, but nothing confirms it
    f.verified_by.append("ROW_BAL")
    assert f.status is Status.VERIFIED
    f.grounded = False
    assert f.status is Status.UNVERIFIED       # confirmed, but not on the page


# ------------------------------------------------------------------------- repair

class _Ctx:
    def __init__(self, statement, report):
        self.statement = statement
        self.inv_report = report


def _spec():
    return DocumentSpec.from_dict({
        "doc_type": "t", "locale": "es-VE", "currency_default": "VES",
        "invariants": ["ROW_BAL"], "columns": {"has_running_balance": True}})


def _statement_with_break():
    from probity.invariants import run_invariants

    st = Statement("d", "VES")
    st.header.opening_balance = Field("opening_balance", "", Money(10000, "VES"),
                                      Provenance.TEXT_LAYER)
    for i, (debit, bal) in enumerate([(1000, 9000), (2000, 6500)]):
        row = Row(index=i, page=1)
        row.date = Field("date", "", date(2026, 1, i + 1), Provenance.TEXT_LAYER)
        row.description = Field("description", "x", "x", Provenance.TEXT_LAYER)
        row.debit = Field("debit", "", Money(debit, "VES"), Provenance.TEXT_LAYER)
        row.balance = Field("balance", "", Money(bal, "VES"), Provenance.TEXT_LAYER)
        st.rows.append(row)
    st.header.closing_balance = Field("closing_balance", "", Money(6500, "VES"),
                                      Provenance.TEXT_LAYER)
    return st, run_invariants(st, _spec())


def test_repair_request_never_contains_the_answer():
    """The Goodhart guard, asserted on the object the proposer actually receives.

    If the expected balance can be read off the request, a model can solve for the
    number instead of reading it, and the resulting table will balance perfectly while
    being wrong.
    """
    st, report = _statement_with_break()
    assert not report.all_passed
    loc = report.failed_locations()[0]
    req = build_repair_request(_Ctx(st, report), loc)

    blob = str(req.to_json()) + req.instruction
    for forbidden in ("6500", "8000", "9000", "1000", "2000", "10000"):
        assert forbidden not in blob, f"the repair request leaks {forbidden}"
    assert req.reason_code == "MISMATCH"       # the class of failure is allowed
    assert req.rows                            # the location is allowed
    for word in ("expected", "should be", "must equal", "target"):
        assert word not in req.instruction.lower()


def test_repair_request_includes_the_neighbouring_rows():
    """A wrong balance on row k breaks rows k and k+1; the cell may be either."""
    st, report = _statement_with_break()
    loc = report.failed_locations()[0]
    req = build_repair_request(_Ctx(st, report), loc)
    assert loc.row_index in req.rows
    assert len(req.rows) >= 2


def test_repair_instruction_asks_for_transcription_not_correction():
    st, report = _statement_with_break()
    req = build_repair_request(_Ctx(st, report), report.failed_locations()[0])
    assert "transcribe" in req.instruction.lower()
    assert "do not compute" in req.instruction.lower()


@pytest.mark.parametrize("printed,claimed,should_ground", [
    ("110,00", 1000, False),      # 10,00 must not ground against 110,00
    ("100,00", 0, False),         # 0,00 must not ground against 100,00
    ("1.234,56", 123456, True),
    ("110,00", 11000, True),
])
def test_a_value_cannot_ground_against_a_fragment_of_another(printed, claimed, should_ground):
    """The exploit that would defeat the whole guarantee.

    A substring test grounds 10,00 against a printed 110,00, so a value invented to
    make a statement balance could supply its own evidence. The match must be against
    a complete number.
    """
    index = page_with([(printed, 100, 200)])
    f = Field("balance", None, Money(claimed, "VES"), Provenance.LLM,
              BBox(1, 100, 200, 140, 210))
    assert ground_field(f, index, ES).ok is should_ground


def test_repair_does_not_receive_the_balances_it_could_solve_from():
    """Sanitising the request is not enough; the previous reading leaks the answer too."""
    from probity.repair import redact_for_repair

    st, report = _statement_with_break()
    req = build_repair_request(_Ctx(st, report), report.failed_locations()[0])
    redacted = redact_for_repair(st, req)

    assert redacted.header.opening_balance.value is None
    for row in redacted.rows:
        assert row.debit.value is None
        assert row.credit.value is None
        assert row.balance.value is None
    blob = str(redacted.to_json())
    for forbidden in ("10000", "9000", "6500", "1000", "2000"):
        assert forbidden not in blob, f"the redacted statement still leaks {forbidden}"


def test_adjacent_amounts_do_not_merge_into_one_number():
    """Two amounts in the same box must stay two amounts.

    When the text found in a box is concatenated without separators, 3.454,93 and
    8.011,48 become 3.454,938.011,48 — one run that matches neither, so both correctly
    read values are reported as ungrounded and a good document goes to a human.
    """
    index = page_with([("3.454,93", 100, 200), ("8.011,48", 150, 200)])
    for minor in (345493, 801148):
        f = Field("balance", None, Money(minor, "VES"), Provenance.LLM,
                  BBox(1, 90, 190, 200, 215))
        assert ground_field(f, index, ES).ok, f"{minor} should ground"
    # and a value that is only an artefact of the join must not ground
    bogus = Field("balance", None, Money(3454938011, "VES"), Provenance.LLM,
                  BBox(1, 90, 190, 200, 215))
    assert not ground_field(bogus, index, ES).ok


def test_grounding_uses_the_printed_spelling_not_the_canonical_one():
    """(250,00) and 1.234,56 CR parse correctly and must ground against themselves."""
    for printed, minor in [("(250,00)", -25000), ("1.234,56", 123456)]:
        index = page_with([(printed, 100, 200)])
        f = Field("balance", printed, Money(minor, "VES"), Provenance.LLM,
                  BBox(1, 100, 200, 160, 210))
        assert ground_field(f, index, ES).ok, f"{printed} should ground against itself"


def test_printed_text_must_reproduce_the_value_it_carries():
    """A field cannot be confirmed by characters that do not parse back to its value.

    Grounding searches the printed spelling, which is correct, but nothing else ties
    `raw` to `value`: a proposer reporting raw="90.00" beside value=80.00 would have the
    page confirm a number the field does not hold.
    """
    index = page_with([("90,00", 100, 200)])
    honest = Field("balance", "90,00", Money(9000, "VES"), Provenance.LLM,
                   BBox(1, 100, 200, 140, 210))
    lying = Field("balance", "90,00", Money(8000, "VES"), Provenance.LLM,
                  BBox(1, 100, 200, 140, 210))
    assert ground_field(honest, index, ES).ok
    assert not ground_field(lying, index, ES).ok


def test_a_sign_is_not_interchangeable():
    """A printed -10,00 and a claimed 10,00 are different balances."""
    index = page_with([("-10,00", 100, 200)])
    f = Field("balance", None, Money(1000, "VES"), Provenance.LLM,
              BBox(1, 100, 200, 140, 210))
    assert not ground_field(f, index, ES).ok


def test_unrelated_neighbours_do_not_join_into_a_value():
    """'1' beside '10,00' must not ground a claimed 110,00.

    A number is split at a separator, not through the middle of an integer.
    """
    index = page_with([("1", 100, 200), ("10,00", 140, 200)])
    f = Field("balance", None, Money(11000, "VES"), Provenance.LLM,
              BBox(1, 95, 195, 220, 215))
    assert not ground_field(f, index, ES).ok
