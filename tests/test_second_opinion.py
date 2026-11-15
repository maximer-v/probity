"""The second reader: correct a misread, confirm a bad document, never patch the wrong row.

No model is called. Two fake readers return fixed transcriptions of an image-only PDF, so
each test states exactly what each reader "saw" and checks what the machine concluded.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from probity import Document, DocumentSpec, Pipeline, default_proposers
from probity.proposers.base import Proposer
from probity.proposers.vlm import _build

SPEC = Path(__file__).resolve().parents[1] / "examples" / "specs" / "agami_type1.yaml"


class FakeModel:
    def __init__(self, name: str):
        self.model = name


class FakeReader(Proposer):
    """Returns a fixed transcription. A page re-read returns only that page's rows."""

    bills_usd = False
    supports_regions = False
    cost_class = 3

    def __init__(self, name: str, rows: list[dict], opening: str, closing: str,
                 tier: str = "llm_small"):
        self.model = FakeModel(name)
        self.tier = tier
        self.rows, self.opening, self.closing = rows, opening, closing
        self.pages_asked: list[int] = []

    def available(self):
        return True, self.model.model

    def propose(self, doc, spec, *, region=None, previous=None):
        rows = self.rows
        if region is not None and region.page is not None:
            self.pages_asked.append(int(region.page))
            rows = [r for r in rows if r.get("page", 1) == region.page]
        data = {"opening_balance": self.opening, "closing_balance": self.closing,
                "period_start": "01 Jan 2024", "period_end": "31 Jan 2024",
                "account_id": "123", "rows": rows}
        pages = [f"p{i + 1}" for i in range(max(1, doc.page_count))]
        p = _build(data, spec, doc, pages, self.tier, source=f"llm:{self.model.model}")
        p.model_calls = []
        return p


def row(day: int, debit: str, credit: str, balance: str) -> dict:
    return {"page": 1, "date": f"{day:02d}-01-2024", "description": f"payment {day}",
            "debit": debit, "credit": credit, "balance": balance}


# A statement that ties: 1,000.00 opening, four movements, 1,150.00 closing.
GOOD = [row(1, "", "500.00", "1,500.00"),
        row(2, "200.00", "", "1,300.00"),
        row(3, "", "50.00", "1,350.00"),
        row(4, "200.00", "", "1,150.00")]


def changed(rows: list[dict], i: int, **over) -> list[dict]:
    out = [dict(r) for r in rows]
    out[i].update(over)
    return out


@pytest.fixture()
def pdf(tmp_path):
    from PIL import Image

    path = tmp_path / "scan.pdf"
    Image.new("L", (200, 280), 255).save(path)
    return str(path)


def run(pdf, first_rows, second_rows=None, closing="1,150.00"):
    spec = replace(DocumentSpec.load(str(SPEC)), tier_order=("llm_small",))
    first = FakeReader("reader-a", first_rows, "1,000.00", closing)
    checker = (None if second_rows is None else
               FakeReader("reader-b", second_rows, "1,000.00", closing, tier="checker"))
    result = Pipeline(spec, default_proposers(llm_small=first, checker=checker)).run(
        Document(doc_id="t", pdf_path=pdf))
    return result, checker


def test_clean_document_never_calls_the_second_reader(pdf):
    result, checker = run(pdf, GOOD, GOOD)
    assert result.accepted and result.conclusion == "CONFIRMED"
    assert checker.pages_asked == [] and result.corrections == []


def test_misread_direction_is_corrected_and_recorded(pdf):
    # The first reader puts row 1's debit in the credit column. The document is fine.
    misread = changed(GOOD, 1, debit="", credit="200.00")
    result, checker = run(pdf, misread, GOOD)
    assert result.accepted and result.conclusion == "CONFIRMED"
    assert checker.pages_asked == [1]
    fields = {(c["row"], c["field"]) for c in result.corrections}
    assert fields == {(1, "debit"), (1, "credit")}
    fix = next(c for c in result.corrections if c["field"] == "debit")
    assert fix["first_reading"] == "" and fix["corrected"] == "200.00"
    assert fix["first_reader"] == "reader-a" and fix["second_reader"] == "reader-b"
    assert "ROW_BAL" in fix["confirmed_by"]


def test_misread_digit_is_corrected(pdf):
    misread = changed(GOOD, 2, credit="80.00")
    result, _ = run(pdf, misread, GOOD)
    assert result.accepted
    assert [(c["row"], c["field"], c["corrected"]) for c in result.corrections] == [
        (2, "credit", "50.00")]


def test_both_readers_agree_so_the_document_is_inconsistent(pdf):
    # Row 2 really is printed as 80.00 on the page. Both readers transcribe it so.
    altered = changed(GOOD, 2, credit="80.00")
    result, _ = run(pdf, altered, altered)
    assert not result.accepted
    assert result.conclusion == "DOCUMENT_INCONSISTENT"
    assert "row:2" in result.conclusion_reason
    assert result.corrections == []


def test_a_misread_and_a_forgery_are_told_apart(pdf):
    # The page prints a altered 80.00 on row 2. The first reader ALSO misreads row 1.
    altered = changed(GOOD, 2, credit="80.00")
    first = changed(altered, 1, debit="", credit="200.00")
    result, _ = run(pdf, first, altered)
    assert not result.accepted
    assert {c["row"] for c in result.corrections} == {1}
    assert result.conclusion == "DOCUMENT_INCONSISTENT"
    assert "row:2" in result.conclusion_reason and "row:1" not in result.conclusion_reason


def test_readers_disagree_and_neither_ties(pdf):
    altered = changed(GOOD, 2, credit="80.00")
    other = changed(GOOD, 2, credit="90.00")
    result, _ = run(pdf, altered, other)
    assert not result.accepted and result.conclusion == "UNRESOLVED"
    assert result.corrections == []
    assert any(o["finding"] == "DISPUTED" for o in result.opinions)


def test_a_dropped_row_cannot_patch_the_wrong_line(pdf):
    # A counter-example worth pinning. Three printed rows: no movement, an inconsistent
    # debit of 20.00, then a debit of 10.00. The second reader omits the FIRST row, so
    # by position its second row (the 10.00) lines up with the inconsistent one, and
    # copying it across would make a broken document tie.
    printed = [row(1, "", "", "100.00"), row(2, "20.00", "", "90.00"),
               row(3, "10.00", "", "80.00")]
    spec = replace(DocumentSpec.load(str(SPEC)), tier_order=("llm_small",))
    first = FakeReader("reader-a", printed, "100.00", "80.00")
    checker = FakeReader("reader-b", printed[1:], "100.00", "80.00", tier="checker")
    result = Pipeline(spec, default_proposers(llm_small=first, checker=checker)).run(
        Document(doc_id="t", pdf_path=pdf))
    assert not result.accepted
    assert result.corrections == []
    assert result.statement.rows[1].debit.raw == "20.00"


def test_without_a_second_reader_nothing_changes(pdf):
    misread = changed(GOOD, 1, debit="", credit="200.00")
    result, _ = run(pdf, misread, None)
    assert not result.accepted and result.conclusion == "UNRESOLVED"
    # This reader cannot re-read a page either, so nothing is available and nothing moves.
    assert result.corrections == []
    assert all(o["finding"] == "UNAVAILABLE" for o in result.opinions)


def test_a_page_read_without_its_amounts_is_corrected_in_one_step(pdf):
    # The first reader returns every row of the page with the amount columns blank:
    # dates and balances are right, debits and credits are missing. One second reading
    # of the page must be enough to put all of them back.
    blank = [dict(r, debit="", credit="") for r in GOOD]
    result, checker = run(pdf, blank, GOOD)
    assert result.accepted and result.conclusion == "CONFIRMED"
    assert checker.pages_asked == [1]
    assert {c["row"] for c in result.corrections} == {0, 1, 2, 3}
    assert sum(1 for o in result.opinions if o["finding"] == "CORRECTED") == 1


def test_the_sweep_leaves_a_altered_row_for_its_own_finding(pdf):
    # Same lost columns, but row 2 is also altered on the page. The sweep must correct
    # the misread rows and must not touch, or hide, the row both readers agree on.
    altered = changed(GOOD, 2, credit="80.00")
    blank = [dict(r, debit="", credit="") if i != 2 else dict(r)
             for i, r in enumerate(altered)]
    result, _ = run(pdf, blank, altered)
    assert not result.accepted
    assert result.conclusion == "DOCUMENT_INCONSISTENT"
    assert "row:2" in result.conclusion_reason
    assert {c["row"] for c in result.corrections} == {0, 1, 3}


# --------------------------------------------------------------------------------
# The guards. Each test is an input that would produce a wrong conclusion without the
# guard it names.
# --------------------------------------------------------------------------------

def run_with(pdf, first_rows, second_rows, opening, closing, second_name="reader-b"):
    spec = replace(DocumentSpec.load(str(SPEC)), tier_order=("llm_small",))
    first = FakeReader("reader-a", first_rows, opening, closing)
    checker = FakeReader(second_name, second_rows, opening, closing, tier="checker")
    result = Pipeline(spec, default_proposers(llm_small=first, checker=checker)).run(
        Document(doc_id="t", pdf_path=pdf))
    return result, checker


@pytest.fixture()
def pdf2(tmp_path):
    from PIL import Image

    path = tmp_path / "scan2.pdf"
    pages = [Image.new("L", (200, 280), 255) for _ in range(2)]
    pages[0].save(path, save_all=True, append_images=pages[1:])
    return str(path)


def test_a_passing_row_is_never_edited_to_make_an_altered_row_tie(pdf):
    # Printed: no movement / 100, debit 10 / 90, debit 20 / 80. The last row is altered
    # and both readers transcribe it identically. Reader A invents a credit on row 0;
    # reader B gets row 0 right but misreads row 1 as "no movement, balance 100", which
    # would make the altered row tie (100 - 20 = 80).
    a = [row(1, "", "5.00", "100.00"), row(2, "10.00", "", "90.00"),
         row(3, "20.00", "", "80.00")]
    b = [row(1, "", "", "100.00"), row(2, "", "", "100.00"), row(3, "20.00", "", "80.00")]
    result, _ = run_with(pdf, a, b, "100.00", "80.00")
    assert not result.accepted and result.conclusion != "CONFIRMED"
    assert result.statement.rows[1].debit.raw == "10.00"        # row 1 passed; untouched
    assert {c["row"] for c in result.corrections} == {0}


def test_a_replacement_that_moves_the_failure_is_refused(pdf):
    # Taking reader B's row 0 removes two failures and creates one on row 1. Fewer
    # failures in total is not good enough.
    a = [row(1, "30.00", "", "90.00"), row(2, "10.00", "", "80.00")]
    b = [row(1, "20.00", "", "80.00"), row(2, "10.00", "", "80.00")]
    result, _ = run_with(pdf, a, b, "100.00", "70.00")
    assert not result.accepted and result.corrections == []
    assert result.statement.rows[0].debit.raw == "30.00"


def test_a_value_is_not_copied_from_a_different_line(pdf):
    # Two rows share a date and a balance. Reader B omits the first, so its only row
    # lines up with A's first by key. It is a different transaction.
    one = dict(row(1, "20.00", "", "100.00"), description="cheque 5512")
    two = dict(row(1, "", "", "100.00"), description="service fee")
    result, _ = run_with(pdf, [one, two], [two], "100.00", "100.00")
    assert not result.accepted and result.corrections == []
    assert result.statement.rows[0].debit.raw == "20.00"

    # The same with identical descriptions: the key is not unique on the page and the
    # readers disagree on the number of rows, so nothing may be paired.
    one, two = row(1, "20.00", "", "100.00"), row(1, "", "", "100.00")
    result, _ = run_with(pdf, [one, two], [two], "100.00", "100.00")
    assert not result.accepted and result.corrections == []


def test_agreement_on_a_row_is_not_enough_if_the_balance_carried_in_is_disputed(pdf2):
    # A clean two-page statement. Reader A misreads page 1 consistently (debit 5,
    # balance 95), so the only failing row is on page 2, where both readers agree.
    # The document is fine; it must not be called inconsistent.
    p1, p2 = row(1, "10.00", "", "90.00"), dict(row(2, "10.00", "", "80.00"), page=2)
    wrong = row(1, "5.00", "", "95.00")
    result, checker = run_with(pdf2, [wrong, p2], [p1, p2], "100.00", "80.00")
    assert result.conclusion == "UNRESOLVED"
    assert sorted(checker.pages_asked) == [1, 2]      # it went back for the operand


def test_a_date_the_readers_disagree_on_does_not_accuse_the_document(pdf):
    # Reader A misreads the first date as the 3rd, so the 2nd appears out of order.
    # The amounts agree throughout; the readers disagree on the field that fails.
    a = [row(3, "", "500.00", "1,500.00")] + GOOD[1:]
    result, _ = run_with(pdf, a, GOOD, "1,000.00", "1,150.00")
    assert result.conclusion != "DOCUMENT_INCONSISTENT"


def test_the_same_model_twice_is_not_a_second_opinion(pdf):
    misread = changed(GOOD, 1, debit="", credit="200.00")
    result, _ = run_with(pdf, misread, GOOD, "1,000.00", "1,150.00", second_name="reader-a")
    assert not result.accepted and result.corrections == []
    assert all(o["finding"] == "UNAVAILABLE" for o in result.opinions)


def test_a_cell_whose_heading_contradicts_its_column_cannot_be_confirmed(pdf):
    # The amount sits in `credit` while the model reports the heading as "Debit". It
    # happens to balance. A reading the model contradicts itself on is not confirmed.
    rows = [dict(row(1, "", "20.00", "120.00"), amount_column="Debit")]
    result, _ = run_with(pdf, rows, rows, "100.00", "120.00")
    assert not result.accepted and result.conclusion != "CONFIRMED"


def test_a_finding_lapses_when_the_figures_it_was_made_on_change(pdf):
    from types import SimpleNamespace

    from probity.pipeline import _finding_for
    from probity.second_opinion import operands

    altered = changed(GOOD, 2, credit="80.00")
    result, _ = run(pdf, altered, altered)
    st, loc = result.statement, None
    from probity.invariants import Location, Scope
    loc = Location(Scope.ROW, row_index=2, page=1)
    spec = DocumentSpec.load(str(SPEC))
    ctx = SimpleNamespace(statement=st, spec=spec, settled_regions={
        loc.key(): {"finding": "DOCUMENT_INCONSISTENT",
                    "operands": list(operands(st, spec, 2))}})
    assert _finding_for(ctx, loc) == "DOCUMENT_INCONSISTENT"
    st.rows[1].balance = st.rows[0].balance          # the balance carried in changes
    assert _finding_for(ctx, loc) is None


# --------------------------------------------------------------------------------
# More guard cases: look-alike lines, other readers, operands, newest-first order.
# --------------------------------------------------------------------------------

def test_a_dropped_and_duplicated_row_cannot_stand_in_for_its_neighbour(pdf):
    # Same date, same balance, near-identical descriptions. Reader B drops the first
    # row and returns the second twice, so the row counts still match.
    one = dict(row(1, "20.00", "", "100.00"), description="cheque 5512")
    two = dict(row(1, "", "", "100.00"), description="cheque 5513")
    result, _ = run_with(pdf, [one, two], [two, dict(two)], "100.00", "100.00")
    assert not result.accepted and result.corrections == []
    assert result.statement.rows[0].debit.raw == "20.00"


def test_another_reader_cannot_overturn_what_two_readers_agreed(pdf):
    # Both readers transcribe debit 20 / balance 90 on the first row, which does not
    # tie. A third, stronger reader is configured and would return debit 10. It must
    # not be consulted to replace the reading.
    rows = [row(1, "20.00", "", "90.00"), row(2, "10.00", "", "80.00")]
    fixed = [row(1, "10.00", "", "90.00"), row(2, "10.00", "", "80.00")]
    spec = replace(DocumentSpec.load(str(SPEC)), tier_order=("llm_small", "llm_large"))
    first = FakeReader("reader-a", rows, "100.00", "80.00")
    checker = FakeReader("reader-b", rows, "100.00", "80.00", tier="checker")
    large = FakeReader("reader-c", fixed, "100.00", "80.00", tier="llm_large")
    result = Pipeline(spec, default_proposers(llm_small=first, llm_large=large,
                                              checker=checker)).run(
        Document(doc_id="t", pdf_path=pdf))
    assert result.conclusion == "DOCUMENT_INCONSISTENT"
    assert result.corrections == [] and large.pages_asked == []
    assert result.statement.rows[0].debit.raw == "20.00"


def test_a_balance_only_one_reader_produced_is_not_an_agreed_operand(pdf):
    # Clean: debit 30 / 70, debit 10 / 60. Reader A has 40 / 90 on the first row, reader
    # B has 20 / 80, which ties and is accepted (a correction is selected by arithmetic,
    # and here it selects a wrong value). Both then agree on the second row, which no
    # longer follows. The balance carried into it was never agreed by two readers, so
    # the document must not be reported as inconsistent.
    a = [row(1, "40.00", "", "90.00"), row(2, "10.00", "", "60.00")]
    b = [row(1, "20.00", "", "80.00"), row(2, "10.00", "", "60.00")]
    result, _ = run_with(pdf, a, b, "100.00", "60.00")
    assert result.conclusion == "UNRESOLVED"


def test_a_statement_printed_newest_first_uses_the_row_below_as_its_operand(pdf):
    # Newest first: row 0 is the 2nd (debit 10 / 80), row 1 the 1st (debit 10 / 90).
    # Reader A misreads the older row consistently as 5 / 95, so the newer row fails.
    # The balance carried into it is the OLDER row's, which the readers disagree on.
    base = DocumentSpec.load(str(SPEC))
    spec = replace(base, tier_order=("llm_small",),
                   columns=replace(base.columns, sort_order="descending"))
    a = [row(2, "10.00", "", "80.00"), row(1, "5.00", "", "95.00")]
    b = [row(2, "10.00", "", "80.00"), row(1, "10.00", "", "90.00")]
    first = FakeReader("reader-a", a, "100.00", "80.00")
    checker = FakeReader("reader-b", b, "100.00", "80.00", tier="checker")
    result = Pipeline(spec, default_proposers(llm_small=first, checker=checker)).run(
        Document(doc_id="t", pdf_path=pdf))
    assert result.conclusion != "DOCUMENT_INCONSISTENT"


class RereadReader(FakeReader):
    """A first reader that can re-read a page, and reads it differently when it does."""

    supports_regions = True

    def __init__(self, *a, reread_rows=None, **kw):
        super().__init__(*a, **kw)
        self.reread_rows = reread_rows

    def propose(self, doc, spec, *, region=None, previous=None):
        if region is not None and region.page is not None and self.reread_rows is not None:
            keep, self.rows = self.rows, self.reread_rows
            try:
                return super().propose(doc, spec, region=region, previous=previous)
            finally:
                self.rows = keep
        return super().propose(doc, spec, region=region, previous=previous)


def run_alone(pdf, first_rows, reread_rows, opening="1,000.00", closing="1,150.00"):
    spec = replace(DocumentSpec.load(str(SPEC)), tier_order=("llm_small",))
    reader = RereadReader("reader-a", first_rows, opening, closing, reread_rows=reread_rows)
    return Pipeline(spec, default_proposers(llm_small=reader)).run(
        Document(doc_id="t", pdf_path=pdf)), reader


def test_without_a_second_reader_a_reread_goes_through_the_same_mechanism(pdf):
    # A debit read as a credit, read correctly on the re-read. The whole row is taken,
    # as it would be from a second reader, and the change is labelled for what it is.
    misread = changed(GOOD, 1, debit="", credit="200.00")
    result, reader = run_alone(pdf, misread, GOOD)
    assert result.accepted and result.conclusion == "CONFIRMED"
    assert {c["method"] for c in result.corrections} == {"same_reader_reread"}
    assert {(c["row"], c["field"]) for c in result.corrections} == {(1, "debit"), (1, "credit")}


def test_a_reader_agreeing_with_itself_does_not_accuse_the_document(pdf):
    altered = changed(GOOD, 2, credit="80.00")
    result, _ = run_alone(pdf, altered, altered)
    assert result.conclusion == "UNRESOLVED"
    assert any(o["finding"] == "REPEATED" for o in result.opinions)


# --------------------------------------------------------------------------------
# Guard cases: line identity, date order, unreadable cells, exit codes.
# --------------------------------------------------------------------------------

def test_two_readers_that_each_dropped_a_different_look_alike_line_are_not_paired(pdf):
    # Printed: "cheque 5512" debit 20 / 100 and "cheque 5513" blank / 100, same date.
    # Reader A returns only the first, reader B only the second. One row each, same
    # date, same balance, similar wording. They are different transactions.
    one = dict(row(1, "20.00", "", "100.00"), description="cheque 5512")
    two = dict(row(1, "", "", "100.00"), description="cheque 5513")
    result, _ = run_with(pdf, [one], [two], "100.00", "100.00")
    assert not result.accepted and result.corrections == []
    assert result.statement.rows[0].debit.raw == "20.00"


def test_a_disputed_date_on_a_newest_first_statement_does_not_accuse_the_document(pdf):
    # Newest first, so dates must not increase down the page. Reader A has the 1st then
    # the 2nd, which breaks the order at the second row; reader B has the 3rd then the
    # 2nd, which does not. The balances follow either way. The readers disagree on the
    # date the failure is computed from.
    base = DocumentSpec.load(str(SPEC))
    spec = replace(base, tier_order=("llm_small",),
                   columns=replace(base.columns, sort_order="descending"))
    a = [row(1, "10.00", "", "80.00"), row(2, "10.00", "", "90.00")]
    b = [row(3, "10.00", "", "80.00"), row(2, "10.00", "", "90.00")]
    first = FakeReader("reader-a", a, "100.00", "80.00")
    checker = FakeReader("reader-b", b, "100.00", "80.00", tier="checker")
    result = Pipeline(spec, default_proposers(llm_small=first, checker=checker)).run(
        Document(doc_id="t", pdf_path=pdf))
    assert result.conclusion != "DOCUMENT_INCONSISTENT"


def test_an_unreadable_cell_replaced_by_a_blank_is_recorded(pdf):
    # The first reader could not read the credit cell ("??"); the second reader has it
    # blank. Both hold no value, but the reading changed and the record must say so.
    a = [row(1, "20.00", "??", "90.00")]
    b = [row(1, "10.00", "", "90.00")]
    result, _ = run_with(pdf, a, b, "100.00", "90.00")
    fields = {(c["field"], c["first_reading"], c["corrected"]) for c in result.corrections}
    assert ("credit", "??", "") in fields and ("debit", "20.00", "10.00") in fields


def test_the_exit_code_follows_the_conclusion(pdf):
    from types import SimpleNamespace

    from probity.cli import exit_code

    ok = SimpleNamespace(final_state="ACCEPT", conclusion="CONFIRMED")
    tolerated = SimpleNamespace(final_state="ACCEPT", conclusion="UNRESOLVED")
    broken = SimpleNamespace(final_state="ERROR", conclusion="UNRESOLVED")
    assert (exit_code(ok), exit_code(tolerated), exit_code(broken)) == (0, 1, 2)


# --------------------------------------------------------------------------------
# The third reading: a tie-break before the document is held responsible.
# --------------------------------------------------------------------------------

def run_three(pdf, first_rows, second_rows, reread_rows, opening="1,000.00",
              closing="1,150.00"):
    spec = replace(DocumentSpec.load(str(SPEC)), tier_order=("llm_small",))
    first = RereadReader("reader-a", first_rows, opening, closing, reread_rows=reread_rows)
    checker = FakeReader("reader-b", second_rows, opening, closing, tier="checker")
    return Pipeline(spec, default_proposers(llm_small=first, checker=checker)).run(
        Document(doc_id="t", pdf_path=pdf))


def test_a_misreading_shared_by_both_models_is_caught_by_the_third_reading(pdf):
    # Both models put row 1's debit in the credit column. The document is fine. On its
    # higher-resolution re-read the first reader gets it right.
    shared = changed(GOOD, 1, debit="", credit="200.00")
    result = run_three(pdf, shared, shared, GOOD)
    assert result.accepted and result.conclusion == "CONFIRMED"
    assert {(c["row"], c["method"]) for c in result.corrections} == {(1, "third_reading")}


def test_three_readings_that_agree_leave_the_document_responsible(pdf):
    altered = changed(GOOD, 2, credit="80.00")
    result = run_three(pdf, altered, altered, altered)
    assert result.conclusion == "DOCUMENT_INCONSISTENT" and result.corrections == []
    assert "third reading" in result.opinions[-1]["reason"].lower()


def test_a_third_reading_that_differs_without_tying_changes_nothing(pdf):
    altered = changed(GOOD, 2, credit="80.00")
    odd = changed(GOOD, 2, credit="90.00")
    result = run_three(pdf, altered, altered, odd)
    assert result.conclusion == "DOCUMENT_INCONSISTENT" and result.corrections == []
    assert result.statement.rows[2].credit.raw == "80.00"


def test_a_balance_set_by_the_third_reading_is_not_an_operand_the_readers_agreed_on(pdf):
    # Both models: debit 20 / 90, then debit 10 / 60. The third reading changes the
    # first balance to 80, which ties the first row. The second row still fails, and
    # the balance now carried into it (80) came from neither of the two readers.
    both = [row(1, "20.00", "", "90.00"), row(2, "10.00", "", "60.00")]
    third = [row(1, "20.00", "", "80.00"), row(2, "10.00", "", "60.00")]
    result = run_three(pdf, both, both, third, opening="100.00", closing="60.00")
    assert result.conclusion == "UNRESOLVED"


def test_the_third_reading_touches_only_the_row_the_readers_agreed_on(pdf):
    # The models agree on row 0 and disagree on row 1. The third reading differs on
    # both. It may be tried on row 0 alone; here that does not tie, so nothing moves on
    # its account, and row 1 is never described as agreed.
    a = [row(1, "20.00", "", "90.00"), row(2, "10.00", "", "70.00")]
    b = [row(1, "20.00", "", "90.00"), row(2, "30.00", "", "70.00")]
    third = [row(1, "10.00", "", "90.00"), row(2, "20.00", "", "70.00")]
    result = run_three(pdf, a, b, third, opening="100.00", closing="70.00")
    notes = [c.get("note", "") for c in result.corrections if c["row"] == 1]
    assert not any("agreed" in n for n in notes)


def test_a_report_with_a_superseded_third_reading_still_renders(pdf):
    from probity.report import render_report

    both = [row(1, "20.00", "", "90.00"), row(2, "10.00", "", "60.00")]
    third = [row(1, "15.00", "", "90.00"), row(2, "10.00", "", "60.00")]
    result = run_three(pdf, both, both, third, opening="100.00", closing="60.00")
    assert "Verification report" in render_report(result.certificate.to_json())


def test_a_date_the_first_reader_could_not_read_is_taken_from_the_second(pdf):
    # A statement with two date columns: on one row the first reader copied the other
    # column's format, which does not parse. The amounts are fine. The second reader
    # has the date in the declared format.
    unreadable = [dict(r) for r in GOOD]
    unreadable[1]["date"] = "02 Jan 2024"
    result, _ = run(pdf, unreadable, GOOD)
    assert result.accepted and result.conclusion == "CONFIRMED"
    assert [(c["row"], c["field"]) for c in result.corrections] == [(1, "date")]
