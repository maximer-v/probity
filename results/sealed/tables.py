"""Recompute the tables of docs/RESULTS.md from the scored outcomes in this folder.

    python results/sealed/tables.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).parent


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def cell(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k} of {n} ({lo * 100:.0f}-{hi * 100:.0f}%)"


def load(path: str) -> list[dict]:
    return [json.loads(l) for l in (HERE / path / "outcomes.jsonl").read_text().splitlines()
            if l.strip()]


def view(r: dict) -> dict:
    """One vocabulary for the machine's outcomes and a model's final answer."""
    if "final" in r:                                   # a model deciding alone
        f = r["final"]
        return {"confirmed": bool(f.get("certified")), "exact": bool(f.get("named_exactly")),
                "located": bool(f.get("target_named")), "ledger": bool(f.get("amounts_exact")),
                "answered": bool(f.get("answered"))}
    named = r["conclusion"] == "DOCUMENT_INCONSISTENT"
    want = sorted(r["expected_rows"])
    return {"confirmed": r["conclusion"] == "CONFIRMED",
            "exact": named and sorted(r["rows_failing"]) == want,
            "located": named and bool(set(want) & set(r["rows_failing"])),
            "ledger": bool(r["amounts_and_dates_exact"]), "answered": True}


def statements(path: str, rows: list[dict] | None = None) -> dict[str, str]:
    rows = rows if rows is not None else load(path)
    v = [(r, view(r)) for r in rows]
    clean = [x for r, x in v if not r["altered"]]
    det = [x for r, x in v if r["detectable"]]
    und = [x for r, x in v if r["group"] in ("amount_adjusted", "row_adjusted")]
    txt = [x for r, x in v if r["group"] == "text"]
    count = lambda xs, key: cell(sum(x[key] for x in xs), len(xs))  # noqa: E731
    return {"clean confirmed": count(clean, "confirmed"),
            "detectable confirmed": count(det, "confirmed"),
            "detectable located exactly": count(det, "exact"),
            "detectable located": count(det, "located"),
            "undetectable confirmed": count(und, "confirmed"),
            "text alteration confirmed": count(txt, "confirmed"),
            "amounts, balances and dates exact": count([x for _, x in v], "ledger"),
            "no usable answer": str(sum(not x["answered"] for _, x in v))}


def receipts(path: str) -> dict[str, str]:
    rows = load(path)
    clean = [r for r in rows if not r["altered"]]
    alt = [r for r in rows if r["altered"]]
    count = lambda xs, key: cell(sum(bool(x[key]) for x in xs), len(xs))  # noqa: E731
    return {"clean confirmed": count(clean, "confirmed"),
            "clean reported": count(clean, "reported"),
            "altered confirmed": count(alt, "confirmed"),
            "altered reported": count(alt, "reported"),
            "altered located": count(alt, "located"),
            "reading exact": count(rows, "reading_exact"),
            "no usable answer": str(sum(not r["answered"] for r in rows))}


def show(title: str, table: dict[str, dict[str, str]]) -> None:
    print(f"\n{title}")
    for name, values in table.items():
        print(f"  {name}")
        for k, v in values.items():
            print(f"    {k:36} {v}")


def main() -> None:
    conditions = ["probity", "gemini_alone", "gemini_with_interpreter", "ocr_rules",
                  "qwen_alone"]
    show("Statements", {c: statements(f"statements/{c}") for c in conditions})
    probity = load("statements/probity")
    for tier in ("T1", "T2", "T3"):
        show(f"Probity, tier {tier}",
             {"": statements("", [r for r in probity if r["tier"] == tier])})
    for n in (60, 40, 30):
        ids = set(json.loads((HERE / f"statements/subset_{n}.json").read_text()))
        show(f"Probity on the {n}-statement subset",
             {"": statements("", [r for r in probity if r["doc_id"] in ids])})
    gem = load("statements/gemini_alone")
    for n in (60, 40, 30):
        ids = set(json.loads((HERE / f"statements/subset_{n}.json").read_text()))
        show(f"Gemini alone on the {n}-statement subset",
             {"": statements("", [r for r in gem if r["doc_id"] in ids])})
    show("Subsets", {c: statements(f"statements/{c}") for c in (
        "factorial_gemini_rereads_itself", "factorial_qwen_first_gemini_second",
        "gemini_alone_paraphrase_b", "gemini_alone_paraphrase_c",
        "probity_replicate_1", "probity_replicate_2")})
    show("Receipts", {c: receipts(f"receipts/{c}") for c in conditions})


if __name__ == "__main__":
    main()
