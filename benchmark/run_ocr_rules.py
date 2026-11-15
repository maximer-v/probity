"""The baseline with no language model: conventional OCR, a table parser, and the same rules.

    python -m benchmark.run_ocr_rules --manifest data/sealed/manifest.json \\
        --out benchmark/results/ocr_rules

If this did as well as the method, the vision models would be adding nothing. It uses an
off-the-shelf OCR engine (RapidOCR, the PaddleOCR models on ONNX Runtime) to get words
with positions, the repository's own position-based table parser to turn them into
rows, and exactly the same rules. There is no second look: with one deterministic
reader there is nothing to compare. So that this baseline can be credited with finding
an alteration, a statement on which a rule fails is scored as REPORTED at the rows that
fail, exactly as if those rows had been confirmed; the price is that a clean statement
it misreads is scored as a false report.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from probity import Document, DocumentSpec, Pipeline
from probity.grounding import BBox, DocumentIndex, PageIndex, Token
from probity.proposers.base import Proposal, Proposer
from probity.proposers.text_layer import parse_statement_from_index

from .convert import statement_to_reading
from .metrics import compare
from .run_scanned import describe, summarise

OCR_WIDTH = 2000          # pixels across the page handed to the OCR engine
_ENGINE = None


def ocr_index(pdf_path: str) -> DocumentIndex:
    """Words and their boxes for every page, in PDF points, from the OCR engine."""
    import pypdfium2 as pdfium
    from rapidocr_onnxruntime import RapidOCR

    global _ENGINE
    if _ENGINE is None:
        _ENGINE = RapidOCR()
    pdf = pdfium.PdfDocument(pdf_path)
    pages: dict[int, PageIndex] = {}
    for n in range(len(pdf)):
        page = pdf[n]
        scale = OCR_WIDTH / page.get_width()
        to_points = 595.276 / OCR_WIDTH
        result, _ = _ENGINE(page.render(scale=scale).to_numpy())
        idx = PageIndex(page=n + 1, width=595.276, height=page.get_height() * scale * to_points)
        for box, text, _conf in result or []:
            xs, ys = [p[0] for p in box], [p[1] for p in box]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            words = str(text).split()
            if not words:
                continue
            # The engine returns phrases. Split them into words, sharing the box out in
            # proportion to length, because the parser assigns columns word by word.
            total = sum(len(w) for w in words) + len(words) - 1
            cursor = 0
            for w in words:
                a = x0 + (x1 - x0) * cursor / total
                b = x0 + (x1 - x0) * (cursor + len(w)) / total
                idx.tokens.append(Token(text=w, source="ocr", bbox=BBox(
                    n + 1, a * to_points, y0 * to_points, b * to_points, y1 * to_points)))
                cursor += len(w) + 1
        pages[n + 1] = idx
    return DocumentIndex(pages=pages, sources=("ocr",))


class OcrProposer(Proposer):
    """Conventional OCR as the only reader."""

    tier = "ocr"
    cost_class = 1
    bills_usd = False
    supports_regions = False

    def propose(self, doc, spec, *, region=None, previous=None) -> Proposal:
        index = ocr_index(doc.pdf_path)
        st, errors, notes = parse_statement_from_index(
            index, spec, doc_id=doc.doc_id, provenance_source="ocr")
        return Proposal(statement=st, index=index, tier=self.tier,
                        parse_errors=errors, notes=notes)


def run(manifest_path: str, out_dir: str, limit: int | None = None) -> dict[str, Any]:
    docs = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["documents"]
    if limit:
        docs = docs[:limit]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = out / "outcomes.jsonl"
    done = ({json.loads(l)["doc_id"] for l in results.read_text().splitlines() if l.strip()}
            if results.exists() else set())
    specs: dict[str, Any] = {}
    with results.open("a", encoding="utf-8") as fh:
        for n, doc in enumerate(docs, start=1):
            if doc["doc_id"] in done:
                continue
            spec = specs.setdefault(doc["spec"], DocumentSpec.load(doc["spec"]))
            truth = json.loads(Path(doc["truth"]).read_text(encoding="utf-8"))
            what = describe(doc)
            t0 = time.perf_counter()
            result = Pipeline(spec, {"ocr": OcrProposer()}).run(
                Document(doc_id=doc["doc_id"], pdf_path=doc["document"]))
            reading = (statement_to_reading(result.statement) if result.statement
                       else {"rows": []})
            cmp = compare(reading, truth, doc_id=doc["doc_id"])
            cert = result.certificate.to_json()
            failing = sorted({f["location"]["row_index"]
                              for f in cert["invariants"].get("failures", [])
                              if f.get("location", {}).get("scope") == "row"})
            conclusion = result.conclusion
            if conclusion != "CONFIRMED" and failing and cmp.rows_got:
                conclusion = "DOCUMENT_INCONSISTENT"
            rec = {"doc_id": doc["doc_id"], "group": what["group"], "tier": what["tier"],
                   "altered": what["altered"], "detectable": what["detectable"],
                   "expected_rows": what["expected_rows"],
                   "altered_row": what["expected_rows"][0] if what["expected_rows"] else None,
                   "conclusion": conclusion,
                   "conclusion_reason": result.conclusion_reason,
                   "rows_failing": failing, "rows_corrected": [], "corrected_by": [],
                   "amounts_and_dates_exact": cmp.ledger_correct,
                   "period_dates_exact": cmp.period_correct,
                   "field_accuracy": round(cmp.field_accuracy, 4),
                   "rows_matched": cmp.rows_matched, "rows_expected": cmp.rows_expected,
                   "descriptions_wrong": cmp.description_wrong,
                   "descriptions_total": cmp.description_total,
                   "second_reader_calls": 0, "cached_calls": 0, "cost_usd": 0.0,
                   "seconds": round(time.perf_counter() - t0, 1)}
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"[{n}/{len(docs)}] {doc['doc_id'][-34:]:34} {rec['conclusion']:22} "
                  f"rows {cmp.rows_matched}/{cmp.rows_expected}", flush=True)
    return summarise(results)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default="benchmark/results/ocr_rules")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    run(args.manifest, args.out, limit=args.limit)


if __name__ == "__main__":
    main()
