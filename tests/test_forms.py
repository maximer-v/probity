"""Forms: fields and lines tied together by sums, defined in YAML, checked by formulas."""

from __future__ import annotations

from pathlib import Path

import pytest

from probity.forms import (CONFIRMED, INCONSISTENT, UNRESOLVED, FormPipeline, FormSpec,
                           FormulaError, build_reading, check, evaluate, parse_money)

SPEC = FormSpec.load(Path(__file__).resolve().parents[1] / "examples" / "specs"
                     / "receipt_cord.yaml")


class Fake:
    def __init__(self, name, data):
        self.name, self.data = name, data

    def read(self, image_path, spec, purpose="transcribe"):
        return build_reading(self.data, spec, self.name)


def receipt(**over):
    base = {"subtotal": "45,500", "tax": "4,550", "service": None, "discount": None,
            "total": "50,050", "cash": "100,000", "change": "49,950",
            "items": [{"name": "REAL GANACHE", "quantity": "1", "unit_price": None, "price": "16,500"},
                      {"name": "EGG TART", "quantity": "1", "unit_price": None, "price": "13,000"},
                      {"name": "PIZZA TOAST", "quantity": "2", "unit_price": "8,000", "price": "16,000"}]}
    base.update(over)
    return base


def with_item(i, **cell):
    r = receipt()
    r["items"] = [dict(x) for x in r["items"]]
    r["items"][i].update(cell)
    return r


def run(first, second=None, third=None):
    return FormPipeline(SPEC, Fake("a", first),
                        Fake("b", second) if second else None,
                        Fake("a-large", third) if third else None).run("t", "unused.png")


def test_money_is_read_exactly_in_both_separator_styles():
    assert parse_money("16,500", "integer") == parse_money("16.500", "integer") == 16500
    assert parse_money("Rp 16.500,00", "integer") == 16500
    assert parse_money("16.50", "integer") is None            # not a whole amount
    assert parse_money("1,234.56", "decimal") == 123456
    # Nothing ambiguous is turned into a number.
    for junk in ("1.5", "1,2,3", "12 or 34", "about 500", "16,5000", "1,234.567"):
        assert parse_money(junk, "integer") is None
    assert parse_money("1,234,56", "decimal") is None
    assert parse_money("10,000.00", "integer") == 10000
    assert parse_money("\u2212100", "integer") == -100          # a Unicode minus is a minus
    assert parse_money("12 or 34", "decimal") is None


def test_the_formula_language_is_small_on_purpose():
    assert evaluate("sum(items.price) == total", {"items": [{"price": 2}, {"price": 3}], "total": 5})
    for bad in ("__import__('os')", "items.__class__", "total ** 2", "[x for x in items]",
                "open('f')", "1.5 + total"):
        with pytest.raises(FormulaError):
            evaluate(bad, {"items": [], "total": 1})


def test_a_receipt_that_adds_up_is_confirmed_without_a_second_reader():
    result = run(receipt())
    assert result.conclusion == CONFIRMED and result.corrections == []


def test_a_misread_line_is_corrected_from_the_second_reading():
    result = run(with_item(1, price="18,000"), receipt())
    assert result.conclusion == CONFIRMED
    assert [(c["where"], c["first_reading"], c["corrected"]) for c in result.corrections] == [
        ("items[1].price", 18000, 13000)]


def test_two_readers_agreeing_on_figures_that_do_not_add_up():
    altered = with_item(1, price="18,000")
    result = run(altered, altered, altered)
    assert result.conclusion == INCONSISTENT
    assert "ITEMS_SUM_TO_SUBTOTAL" in result.reason and result.corrections == []


def test_a_shared_misreading_is_corrected_by_the_third_reading():
    shared = with_item(1, price="18,000")
    result = run(shared, shared, receipt())
    assert result.conclusion == CONFIRMED
    assert [c["method"] for c in result.corrections] == ["third_reading"]


def test_readers_that_disagree_without_either_adding_up_are_unresolved():
    result = run(with_item(1, price="18,000"), with_item(1, price="19,000"))
    assert result.conclusion == UNRESOLVED and result.corrections == []


def test_a_correction_may_not_create_a_failure():
    # The second reader has the misread line right, but a different total that breaks
    # the cash rule. Only the line is taken.
    result = run(with_item(1, price="18,000"), receipt(total="50,060"))
    assert result.conclusion == CONFIRMED
    assert {c["where"] for c in result.corrections} == {"items[1].price"}
    assert result.reading.fields["total"] == 50050


def test_a_line_that_was_not_read_fails_the_sum():
    reading = build_reading(with_item(0, price=None), SPEC)
    assert any(f.rule == "ITEMS_SUM_TO_SUBTOTAL" and "not read" in f.reason
               for f in check(reading, SPEC))


def test_a_per_line_rule_names_the_line():
    reading = build_reading(with_item(2, unit_price="9,000"), SPEC)
    assert [(f.rule, f.row) for f in check(reading, SPEC)] == [("LINE_AMOUNT", 2)]


def test_the_same_model_twice_is_refused():
    with pytest.raises(ValueError):
        FormPipeline(SPEC, Fake("a", receipt()), Fake("a", receipt()))


def test_a_spec_that_names_something_unknown_is_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("doc_type: x\nkind: form\nfields: {total: {type: money}}\n"
                   "rules:\n  - {id: R, check: 'grand_total == total'}\n")
    with pytest.raises(ValueError):
        FormSpec.load(bad)


def test_a_rule_cannot_be_satisfied_by_switching_it_off():
    # LINE_AMOUNT fails on line 2 (2 x 9,000 is not 16,000). The second reader simply
    # has no unit price there, which would make the rule stop applying.
    result = run(with_item(2, unit_price="9,000"), with_item(2, unit_price=None))
    assert result.conclusion != CONFIRMED and result.corrections == []
    assert result.reading.tables["items"][2]["unit_price"] == 9000


def test_a_line_cannot_be_dropped_to_make_the_sum_work():
    # The receipt prints four lines and does not add up. The second reader returns only
    # three of them, which would. A line that was read is not removed.
    printed = receipt()
    printed["items"] = [dict(i) for i in printed["items"]] + [
        {"name": "ICE LATTE", "quantity": "1", "unit_price": None, "price": "9,000"}]
    result = run(printed, receipt())
    assert result.conclusion != CONFIRMED and result.corrections == []
    assert len(result.reading.tables["items"]) == 4


def test_a_value_does_not_move_between_look_alike_lines():
    # Lines "ITEM A" and "ITEM B"; the second reader lists them in the other order.
    first = receipt(subtotal="30,000", tax=None, total="30,000", cash=None, change=None)
    first["items"] = [{"name": "ITEM A", "quantity": "1", "unit_price": "12,000", "price": "10,000"},
                      {"name": "ITEM B", "quantity": "1", "unit_price": "20,000", "price": "20,000"}]
    second = dict(first)
    second["items"] = [{"name": "ITEM B", "quantity": "1", "unit_price": "20,000", "price": "20,000"},
                       {"name": "ITEM A", "quantity": "1", "unit_price": "12,000", "price": "10,000"}]
    result = run(first, second, first)
    assert result.conclusion != CONFIRMED and result.corrections == []
    assert result.reading.tables["items"][0]["unit_price"] == 12000


def test_two_readers_missing_the_same_value_do_not_accuse_the_document():
    blank = with_item(0, price=None)
    result = run(blank, blank, blank)
    assert result.conclusion == UNRESOLVED


def test_a_third_reading_that_needs_two_cells_changed_together_is_used():
    # Both models: 2 x 15,000 = 20,000 on the last line. Printed: 1 x 20,000.
    def line(q, u):
        r = receipt(subtotal="49,500", tax="4,950", total="54,450", change="45,550")
        r["items"] = [dict(i) for i in r["items"]]
        r["items"][2].update(quantity=q, unit_price=u, price="20,000")
        return r
    result = run(line("2", "15,000"), line("2", "15,000"), line("1", "20,000"))
    assert result.conclusion == CONFIRMED
    assert {c["where"] for c in result.corrections} == {"items[2].quantity", "items[2].unit_price"}


def test_similar_is_not_the_same_line():
    first = receipt(subtotal="30,000", tax=None, total="30,000", cash=None, change=None)
    first["items"] = [{"name": "COFFEE LARGE A", "quantity": "1", "unit_price": "12,000", "price": "10,000"},
                      {"name": "COFFEE LARGE C", "quantity": "1", "unit_price": "20,000", "price": "20,000"}]
    second = dict(first)
    second["items"] = [{"name": "COFFEE LARGE B", "quantity": "1", "unit_price": "10,000", "price": "10,000"},
                       {"name": "COFFEE LARGE C", "quantity": "1", "unit_price": "20,000", "price": "20,000"}]
    result = run(first, second, first)
    assert result.conclusion == UNRESOLVED and result.corrections == []


def test_a_total_that_neither_reader_has_is_not_an_inconsistency():
    blank = receipt(total=None, cash=None, change=None)
    result = run(blank, blank, blank)
    assert result.conclusion == UNRESOLVED
