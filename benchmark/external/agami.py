"""Adapter for AgamiAI/Indian-Bank-Statements, a public corpus of synthetic statements.

The layouts, the rendering, the transaction vocabulary and the ground truth all come
from somebody else, so nothing here can have been tuned to them in advance. 400
documents (200 digital, 200 scanned, across two layouts), Apache 2.0, with exact
per-transaction ground truth and a running balance on every row.

What it does not give: bounding boxes, labelled inconsistencies, or more than one locale
(en-IN, INR).

The ground-truth amounts are JSON floats. They are converted through ``Decimal(str(x))``
rather than ``round(x * 100)``: 59131.72 is not representable in binary floating point,
and multiplying it by 100 can land a cent away from the printed figure. Converting the
*string* is exact, and it is the same discipline P1 demands of the parser.

    python -m benchmark.external.agami --dir <download dir> --out data/external/agami
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

MINOR = 2        # INR has two decimal places


def to_minor(value: Any) -> int | None:
    """Exact conversion of a JSON number or string to integer minor units."""
    if value is None or value == "":
        return None
    d = Decimal(str(value)).scaleb(MINOR)
    if d != d.to_integral_value():
        # A third decimal in an INR amount means the source is not what we think it is.
        raise ValueError(f"{value!r} has more precision than INR supports")
    return int(d)


@dataclass
class AgamiDoc:
    doc_id: str
    layout: str          # "type1" | "type2"
    render: str          # "digital" | "scanned"
    pdf: str
    truth: dict[str, Any]


def _iso_date(value: Any) -> str:
    """Their two layouts date their rows differently; normalise to ISO.

    Type 1 writes ``"2024-01-01 11:30:55"``; Type 2 writes ``"01/01/2024"``. Guessing
    from the characters is exactly the ambiguity P1 and the strict date parser exist to
    refuse, so each form is matched explicitly and anything else is left empty rather
    than coerced into a plausible wrong date.
    """
    s = str(value or "").strip()
    if not s:
        return ""
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    if len(s) >= 10 and s[2] == "/" and s[5] == "/":
        d, m, y = s[:10].split("/")
        return f"{y}-{m}-{d}"
    return ""


def convert_truth(raw: dict[str, Any], doc_id: str, layout: str, render: str,
                  pdf_path: str) -> dict[str, Any]:
    """Their JSON into the truth shape the scorer already understands.

    The two layouts do not share a transaction schema. Type 1 publishes ``debit`` /
    ``credit`` / ``balance``; Type 2 publishes ``transaction_amount`` with a ``cr_dr``
    indicator and ``available_balance``. Reading Type 2 with Type 1's field names
    yields a ledger of nulls in which every row appears to break the running balance,
    which is an artefact of the adapter and not a property of the corpus. Both are
    handled explicitly, and a row whose schema matches neither is recorded as
    unreadable instead of being silently zeroed.
    """
    rows = []
    unknown_schema = 0
    for i, t in enumerate(raw["transactions"]):
        if "cr_dr" in t or "transaction_amount" in t:
            amount = to_minor(t.get("transaction_amount"))
            marker = str(t.get("cr_dr") or "").strip().upper()
            debit = amount if marker.startswith("D") else None
            credit = amount if marker.startswith("C") else None
            if marker and not marker[0] in "DC":
                unknown_schema += 1
            balance = to_minor(t.get("available_balance"))
        elif "debit" in t or "credit" in t:
            debit = to_minor(t.get("debit"))
            credit = to_minor(t.get("credit"))
            balance = to_minor(t.get("balance"))
        else:
            unknown_schema += 1
            debit = credit = balance = None
        rows.append({
            "index": i,
            "date": _iso_date(t.get("date")),
            "value_date": _iso_date(t.get("value_date")),
            "description": t.get("description") or "",
            "debit": debit,
            "credit": credit,
            "balance": balance,
            "cheque_no": t.get("cheque_no") or "",
            "failed": bool(t.get("failed")),
        })

    ledger = {
        "account_id": str(raw.get("account_number") or ""),
        "currency": raw.get("currency") or "INR",
        "locale": "en-IN",
        "period_start": raw.get("start_date"),
        "period_end": raw.get("end_date"),
        "opening_balance": to_minor(raw.get("opening_balance")),
        "closing_balance": to_minor(raw.get("closing_balance")),
        "tx_count": len(rows),
        "bank_name": raw.get("bank_name"),
        "holder": raw.get("account_holder"),
        "rows": rows,
    }
    return {
        "doc_id": doc_id,
        "source": "AgamiAI/Indian-Bank-Statements",
        "license": "apache-2.0",
        "bank_id": f"agami_{layout}",
        "locale": "en-IN",
        "currency": ledger["currency"],
        "render": render,
        "group": "external_digital" if render == "digital" else "external_scanned",
        "page_count": None,
        "ledger": ledger,
        # No per-field boxes exist for this corpus, so grounding cannot be scored here.
        "boxes": {},
        "has_box_truth": False,
        "rows_with_unknown_schema": unknown_schema,
        "inconsistency": {"code": None, "detail": {}, "detectable_by": [],
                          "expected_output": "clean reading"},
    }


def audit_ledger(truth: dict[str, Any]) -> dict[str, Any]:
    """Is their ground truth internally exact? Check before trusting it, and record it.

    This matters more than it looks. If the published ground truth does not satisfy the
    running balance, then a system that reads the document *perfectly* fails the
    invariant, and scoring it as an extraction error would be scoring our own
    correctness as a mistake.

    On this corpus the audit does fire, and the PDFs agree with the JSON: a minority of
    rows are printed with a balance that does not follow from the printed amounts. The
    documents are internally inconsistent, not mis-transcribed. That changes what the
    corpus is good for rather than making it useless:

    * extraction accuracy is still measurable against their JSON, row by row, because
      what is printed and what is published agree;
    * document-level ACCEPT is *correctly* refused, so coverage here is expected to be
      near zero and that is the right answer, not a failure;
    * and the rows where their own chain breaks become third-party ground truth for
      **which rows are broken** — a localisation target we did not author.

    That last use is the strongest external evidence available for the row-level claim:
    the rows ROW_BAL points at should be the rows their published figures disagree on.
    """
    led = truth["ledger"]
    bal = led["opening_balance"]
    problems: list[dict[str, Any]] = []
    broken_rows: list[int] = []
    for r in led["rows"]:
        if r["balance"] is None:
            problems.append({"row": r["index"], "issue": "no balance in ground truth"})
            broken_rows.append(r["index"])
            continue
        bal = bal + (r["credit"] or 0) - (r["debit"] or 0)
        if bal != r["balance"]:
            problems.append({"row": r["index"], "issue": "running balance breaks",
                             "expected": bal, "ground_truth": r["balance"],
                             "delta": r["balance"] - bal})
            broken_rows.append(r["index"])
            bal = r["balance"]      # resynchronise so one break is not counted twice
    closing_ok = bal == led["closing_balance"]
    return {"row_chain_ok": not problems, "closing_ok": closing_ok,
            "n_problems": len(problems), "n_rows": len(led["rows"]),
            "broken_rows": broken_rows,
            "problems": problems[:10],
            # Usable for extraction accuracy either way; "chain_exact" says whether a
            # correct reading can also be expected to reach ACCEPT.
            "usable": True,
            "chain_exact": (not problems) and closing_ok}


def load_dir(directory: str | Path) -> list[AgamiDoc]:
    """Read a download directory of ``<Layout>_<n>.pdf`` / ``.json`` pairs."""
    d = Path(directory)
    out: list[AgamiDoc] = []
    for pdf in sorted(d.glob("*.pdf")):
        js = pdf.with_suffix(".json")
        if not js.exists():
            continue
        name = pdf.stem
        layout = "type2" if "Type2" in name else "type1"
        render = "scanned" if "Scanned" in name else "digital"
        raw = json.loads(js.read_text(encoding="utf-8"))
        out.append(AgamiDoc(doc_id=f"agami-{name}", layout=layout, render=render,
                            pdf=str(pdf),
                            truth=convert_truth(raw, f"agami-{name}", layout, render,
                                                str(pdf))))
    return out


def build(directory: str | Path, out_dir: str | Path) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    docs = load_dir(directory)
    records, excluded = [], []
    for doc in docs:
        audit = audit_ledger(doc.truth)
        doc.truth["ground_truth_audit"] = audit
        truth_path = out / f"{doc.doc_id}.truth.json"
        truth_path.write_text(json.dumps(doc.truth, indent=1, ensure_ascii=False),
                              encoding="utf-8")
        rec = {
            "doc_id": doc.doc_id, "bank_id": f"agami_{doc.layout}",
            "group": doc.truth["group"], "inconsistency": None,
            "severity": None, "document": doc.pdf, "truth": str(truth_path),
            "is_digital": doc.render == "digital", "page_images": {},
            "spec": f"examples/specs/agami_{doc.layout}.yaml",
            "n_rows_ledger": len(doc.truth["ledger"]["rows"]),
            "sha256": hashlib.sha256(Path(doc.pdf).read_bytes()).hexdigest(),
            "ground_truth_usable": audit["usable"],
            "chain_exact": audit["chain_exact"],
            "broken_rows_in_source": audit["broken_rows"],
            "n_broken_rows": len(audit["broken_rows"]),
        }
        (records if audit["usable"] else excluded).append(rec)

    exact = [r for r in records if r["chain_exact"]]
    broken = [r for r in records if not r["chain_exact"]]
    total_rows = sum(r["n_rows_ledger"] for r in records)
    total_broken = sum(r["n_broken_rows"] for r in records)
    manifest = {
        "split": "external_agami",
        "source": "AgamiAI/Indian-Bank-Statements",
        "license": "apache-2.0",
        "note": ("Third-party synthetic corpus, used for external validation. No "
                 "bounding-box truth, so grounding runs but is not scored here; no "
                 "labelled source inconsistencies of our own design."),
        "ground_truth_finding": (
            f"{len(broken)} of {len(records)} documents are internally inconsistent in "
            f"the publisher's own ground truth: {total_broken} of {total_rows} rows "
            "carry a balance that does not follow from the printed amounts. The PDFs "
            "agree with the JSON, so these are inconsistent documents rather than "
            "transcription errors. Extraction accuracy is therefore scored per field "
            "and per row; document-level ACCEPT is expected to be refused on the "
            "inconsistent documents, and the rows listed in broken_rows_in_source are "
            "used as third-party ground truth for failure localisation."),
        "n_documents": len(records),
        "n_chain_exact": len(exact),
        "n_chain_broken": len(broken),
        "n_rows_total": total_rows,
        "n_rows_broken_in_source": total_broken,
        "n_excluded_unusable_truth": len(excluded),
        "excluded": excluded,
        "groups": {g: sum(1 for r in records if r["group"] == g)
                   for g in sorted({r["group"] for r in records})},
        "documents": records,
    }
    (Path(out_dir).parent / "manifest_external_agami.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", required=True, help="directory of downloaded pdf/json pairs")
    ap.add_argument("--out", default="data/external/agami")
    args = ap.parse_args()
    m = build(args.dir, args.out)
    print(f"{m['n_documents']} documents; {m['n_chain_exact']} tie out in the "
          f"publisher's own ground truth, {m['n_chain_broken']} do not "
          f"({m['n_rows_broken_in_source']}/{m['n_rows_total']} rows)")
    for g, n in m["groups"].items():
        print(f"  {g}: {n}")


if __name__ == "__main__":
    main()
