"""Scoring a reading against a document's answer key.

* **Monetary and date fields decide correctness.** Amounts, balances and dates are
  compared as exact integers and ISO dates. ``ledger_correct`` is the headline: every
  row's date, debit, credit and balance, and the opening and closing balances. The
  statement period in the header is scored on its own (``period_correct``), because no
  condition has a way to correct it and it should not decide a comparison. Descriptions are free text where reading
  variance does not change what the money did, so they are reported separately and
  excluded from the primary figure.
* **Rows are compared as a multiset**, not positionally, so a statement printed newest
  first is not penalised.
* **The answer key for an altered document is what is printed on the page.** The reader
  should transcribe the altered figure faithfully, and the machine should then report
  the document as inconsistent. Reading and concluding are scored separately.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Iterable

MONEY_HEADER_FIELDS = ("opening_balance", "closing_balance")
DATE_HEADER_FIELDS = ("period_start", "period_end")


# ----------------------------------------------------------------- ground truth

def printed_rows(truth: dict[str, Any]) -> list[dict[str, Any]]:
    """The rows actually printed on the page, which is what a reader should return."""
    rows = truth["ledger"]["rows"]
    absent = set(truth.get("rows_absent") or [])
    return [r for r in rows if r["index"] not in absent]


def row_key(row: dict[str, Any]) -> tuple:
    """The identity of a transaction for comparison: date and the money, exactly.

    A zero amount and a blank cell are folded together. They are the same economic
    fact — no money moved — and documents disagree about which to print: a failed
    transaction ("FAILED-INSUFFICIENT FUNDS") is printed with an empty amount column
    and published in ground truth as ``0``. Scoring a blank cell as a mismatch against
    a published zero would charge the reader for a convention it cannot observe.

    Nothing else is normalised. Every non-zero amount must match to the minor unit.
    """
    def amount(value: Any) -> int | None:
        if value in (None, ""):
            return None
        n = int(value)
        return None if n == 0 else n

    return (str(row.get("date") or ""),
            amount(row.get("debit")),
            amount(row.get("credit")),
            int(row["balance"]) if row.get("balance") not in (None, "") else None)


def truth_header(truth: dict[str, Any]) -> dict[str, Any]:
    led = truth["ledger"]
    return {"opening_balance": led["opening_balance"],
            "closing_balance": led["closing_balance"],
            "period_start": led["period_start"],
            "period_end": led["period_end"],
            "tx_count": led.get("declared_tx_count", led["tx_count"]),
            "account_id": led["account_id"]}


# -------------------------------------------------------------------- comparison

@dataclass
class FieldDiff:
    where: str
    field: str
    expected: Any
    got: Any

    def to_json(self) -> dict[str, Any]:
        return {"where": self.where, "field": self.field,
                "expected": self.expected, "got": self.got}


@dataclass
class Comparison:
    """A full diff of one reading against one document's printed truth."""

    doc_id: str
    correct: bool = False
    diffs: list[FieldDiff] = dc_field(default_factory=list)
    rows_expected: int = 0
    rows_got: int = 0
    rows_matched: int = 0
    rows_missing: list[tuple] = dc_field(default_factory=list)
    rows_extra: list[tuple] = dc_field(default_factory=list)
    fields_total: int = 0
    fields_wrong: int = 0
    description_total: int = 0
    description_wrong: int = 0
    #: Every row's date, debit, credit and balance, and the opening and closing
    #: balances, match the answer key. The statement period is reported separately.
    ledger_correct: bool = False
    #: The period start and end dates in the header match the answer key.
    period_correct: bool = False

    @property
    def row_precision(self) -> float:
        return self.rows_matched / self.rows_got if self.rows_got else 0.0

    @property
    def row_recall(self) -> float:
        return self.rows_matched / self.rows_expected if self.rows_expected else 0.0

    @property
    def row_f1(self) -> float:
        p, r = self.row_precision, self.row_recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def field_accuracy(self) -> float:
        return 1.0 - (self.fields_wrong / self.fields_total) if self.fields_total else 0.0

    @property
    def description_error_rate(self) -> float:
        return self.description_wrong / self.description_total if self.description_total else 0.0

    def to_json(self) -> dict[str, Any]:
        return {"doc_id": self.doc_id, "correct": self.correct,
                "rows": {"expected": self.rows_expected, "got": self.rows_got,
                         "matched": self.rows_matched,
                         "missing": [list(k) for k in self.rows_missing[:20]],
                         "extra": [list(k) for k in self.rows_extra[:20]],
                         "f1": round(self.row_f1, 4)},
                "fields": {"total": self.fields_total, "wrong": self.fields_wrong,
                           "accuracy": round(self.field_accuracy, 4)},
                "descriptions": {"total": self.description_total,
                                 "wrong": self.description_wrong,
                                 "error_rate": round(self.description_error_rate, 4)},
                "diffs": [d.to_json() for d in self.diffs[:40]]}

    def explain(self, limit: int = 8) -> str:
        if self.correct:
            return (f"matches the page: {self.rows_matched}/{self.rows_expected} rows, "
                    f"{self.fields_total - self.fields_wrong}/{self.fields_total} fields")
        lines = [f"{self.fields_wrong}/{self.fields_total} monetary or date fields wrong; "
                 f"rows {self.rows_got} read against {self.rows_expected} printed "
                 f"({len(self.rows_missing)} missing, {len(self.rows_extra)} extra)"]
        for d in self.diffs[:limit]:
            lines.append(f"    {d.where}.{d.field}: expected {d.expected}, got {d.got}")
        if len(self.diffs) > limit:
            lines.append(f"    ... and {len(self.diffs) - limit} more")
        return "\n".join(lines)


def _norm_desc(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.upper().replace("/", " ").split())


def compare(reading: dict[str, Any], truth: dict[str, Any], *,
            doc_id: str = "") -> Comparison:
    """Diff a flat reading (see ``Statement.to_simple``) against the printed truth."""
    exp_rows = printed_rows(truth)
    exp_header = truth_header(truth)
    got_rows = list(reading.get("rows") or [])

    cmp = Comparison(doc_id=doc_id or truth.get("doc_id", ""),
                     rows_expected=len(exp_rows), rows_got=len(got_rows))

    # Header: money exactly, dates as ISO strings.
    for name in MONEY_HEADER_FIELDS:
        cmp.fields_total += 1
        got, exp = reading.get(name), exp_header[name]
        if got != exp:
            cmp.fields_wrong += 1
            cmp.diffs.append(FieldDiff("header", name, exp, got))
    balances_wrong = cmp.fields_wrong
    for name in DATE_HEADER_FIELDS:
        cmp.fields_total += 1
        got, exp = reading.get(name), exp_header[name]
        if (got or None) != exp:
            cmp.fields_wrong += 1
            cmp.diffs.append(FieldDiff("header", name, exp, got))
    cmp.period_correct = cmp.fields_wrong == balances_wrong

    # Rows as a multiset of (date, debit, credit, balance).
    exp_counter = Counter(row_key(r) for r in exp_rows)
    got_counter = Counter(row_key(r) for r in got_rows)
    matched = exp_counter & got_counter
    cmp.rows_matched = sum(matched.values())
    def sort_key(k: tuple) -> tuple:
        # A row key holds None for the side that is blank, so it cannot be sorted
        # directly; None is ordered before any number.
        return tuple((x is not None, x if x is not None else 0) for x in k)

    cmp.rows_missing = sorted((exp_counter - got_counter).elements(), key=sort_key)
    cmp.rows_extra = sorted((got_counter - exp_counter).elements(), key=sort_key)

    # Each printed row contributes four scored cells, and so does each fabricated one.
    # Counting only *missing* rows would let a reader return every true row plus an
    # invented transaction and still score as correct, which is the opposite of what
    # this benchmark exists to measure.
    unmatched = sum((exp_counter - got_counter).values())
    extra = sum((got_counter - exp_counter).values())
    cmp.fields_total += 4 * (len(exp_rows) + extra)
    cmp.fields_wrong += 4 * (unmatched + extra)
    cmp.ledger_correct = balances_wrong == 0 and unmatched == 0 and extra == 0
    for key in cmp.rows_missing[:40]:
        cmp.diffs.append(FieldDiff("row", "date/debit/credit/balance",
                                   list(key), "not present in the reading"))
    for key in cmp.rows_extra[:40]:
        cmp.diffs.append(FieldDiff("row", "date/debit/credit/balance",
                                   "not printed on the page", list(key)))

    # Descriptions, reported but outside the primary metric.
    exp_desc = Counter(_norm_desc(r.get("description")) for r in exp_rows)
    got_desc = Counter(_norm_desc(r.get("description")) for r in got_rows)
    cmp.description_total = len(exp_rows)
    cmp.description_wrong = sum((exp_desc - got_desc).values())

    cmp.correct = cmp.fields_wrong == 0
    return cmp


# ----------------------------------------------------------------- aggregation

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """A Wilson interval, which stays inside [0, 1] when k is 0 or n."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))
