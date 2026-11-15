"""How often do the two readers make the same mistake, and what is agreement worth?

    python -m benchmark.analysis --manifest data/sealed/manifest.json \\
        --first-cache benchmark/results/probity/.cache \\
        --second-cache benchmark/results/qwen_alone/.cache \\
        --subset subset.json --out benchmark/results/analysis.json

The method rests on one assumption: where two different models transcribe a cell the
same way, that is what is printed. This measures it directly, on statements that both
models transcribed in full, by comparing each model's raw transcription with the answer
key cell by cell.

For every amount cell (debit, credit, balance) of every row:

    both right          the assumption is not tested
    one wrong           the readers disagree; the method will look again
    both wrong, differently     they disagree; the method will look again
    both wrong, the same way    they agree on something that is not printed

The last category is the method's exposure, and its rate is the headline of this file.
The same is reported for dates and descriptions, for the opening and closing balances,
and for the account number. The account holder's name is not part of what the readers
are asked to transcribe, so it cannot be measured. Only transcriptions with the right number of rows are compared cell by cell;
the others are counted and reported, because a dropped or invented row shifts every row
after it.

Nothing is requested from a model here: every transcription is replayed from the caches
of runs that have already been paid for, and a missing one stops the analysis.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from probity import Document, DocumentSpec, vlm_proposer

from .convert import statement_to_reading
from .metrics import wilson

FIRST, SECOND = "google/gemini-3.1-flash-lite", "qwen/qwen3.5-flash-02-23"
JSON_HINT = "\nReply with a single JSON object."


def _norm(text: Any) -> str:
    return " ".join(str(text or "").upper().replace("/", " ").split())


def _transcribe(model: str, cache: str, doc: dict[str, Any], spec, hint: bool) -> dict[str, Any]:
    reader = vlm_proposer(model, cap_usd=0.01, cache_dir=cache)
    reader.client.offline = True
    if hint:
        reader.prompt_suffix = JSON_HINT
    proposal = reader.propose(Document(doc_id=doc["doc_id"], pdf_path=doc["document"]), spec)
    if any(not c.cached for c in proposal.model_calls):
        raise RuntimeError(f"{doc['doc_id']}: a transcription by {model} is not in {cache}")
    return statement_to_reading(proposal.statement)


def _classify(a: Any, b: Any, truth: Any) -> str:
    ra, rb = a == truth, b == truth
    if ra and rb:
        return "both_right"
    if ra or rb:
        return "one_wrong"
    return "both_wrong_same" if a == b else "both_wrong_differently"


def run(manifest_path: str, first_cache: str, second_cache: str, out_path: str,
        subset: set[str] | None = None) -> dict[str, Any]:
    docs = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["documents"]
    if subset is not None:
        docs = [d for d in docs if d["doc_id"] in subset]
    cells: dict[str, Counter] = {k: Counter() for k in
                                 ("amount", "date", "description", "header_balance",
                                  "account_number")}
    skipped, compared, shared = [], 0, []
    for d in docs:
        spec = DocumentSpec.load(d["spec"])
        truth = json.loads(Path(d["truth"]).read_text(encoding="utf-8"))["ledger"]
        a = _transcribe(FIRST, first_cache, d, spec, hint=False)
        b = _transcribe(SECOND, second_cache, d, spec, hint=True)
        for name in ("opening_balance", "closing_balance"):
            cells["header_balance"][_classify(a.get(name), b.get(name), truth.get(name))] += 1
        digits = lambda v: "".join(ch for ch in str(v or "") if ch.isdigit())  # noqa: E731
        cells["account_number"][_classify(digits(a.get("account_id")),
                                          digits(b.get("account_id")),
                                          digits(truth.get("account_id")))] += 1
        rows = truth["rows"]
        if len(a["rows"]) != len(rows) or len(b["rows"]) != len(rows):
            skipped.append({"doc_id": d["doc_id"], "rows": len(rows),
                            "first": len(a["rows"]), "second": len(b["rows"])})
            continue
        compared += 1
        for i, t in enumerate(rows):
            ra, rb = a["rows"][i], b["rows"][i]
            for col in ("debit", "credit", "balance"):
                want = t.get(col) or None
                va, vb = (ra.get(col) or None), (rb.get(col) or None)
                if col != "balance":
                    va, vb = (abs(va) if va else None), (abs(vb) if vb else None)
                kind = _classify(va, vb, want)
                cells["amount"][kind] += 1
                if kind == "both_wrong_same":
                    shared.append({"doc_id": d["doc_id"], "row": i, "column": col,
                                   "printed": want, "both_read": va})
            cells["date"][_classify(ra.get("date"), rb.get("date"), t.get("date"))] += 1
            cells["description"][_classify(_norm(ra.get("description")),
                                           _norm(rb.get("description")),
                                           _norm(t.get("description")))] += 1

    def summary(c: Counter) -> dict[str, Any]:
        n = sum(c.values())
        agree = c["both_right"] + c["both_wrong_same"]
        lo, hi = wilson(c["both_wrong_same"], n) if n else (0.0, 0.0)
        return {"cells": n, **{k: c[k] for k in ("both_right", "one_wrong",
                                                 "both_wrong_differently", "both_wrong_same")},
                "shared_misreading_rate": round(c["both_wrong_same"] / n, 6) if n else None,
                "shared_misreading_rate_ci95": [round(lo, 6), round(hi, 6)],
                "readers_agree": agree,
                "correct_given_agreement": round(c["both_right"] / agree, 6) if agree else None}

    out = {"documents": len(docs), "compared_cell_by_cell": compared,
           "skipped_row_count_differs": skipped,
           **{k: summary(v) for k, v in cells.items()},
           "shared_amount_misreadings": shared[:200]}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(out, indent=1), encoding="utf-8")
    for k in cells:
        s = out[k]
        print(f"{k:16} cells {s['cells']:7}  both wrong the same way {s['both_wrong_same']:5} "
              f"({(s['shared_misreading_rate'] or 0) * 100:.3f}%)  "
              f"correct given agreement {s['correct_given_agreement']}")
    print(f"compared {compared} of {len(docs)} statements cell by cell; "
          f"{len(skipped)} skipped for a differing row count")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--first-cache", required=True)
    ap.add_argument("--second-cache", required=True)
    ap.add_argument("--subset", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    only = set(json.loads(Path(args.subset).read_text())) if args.subset else None
    run(args.manifest, args.first_cache, args.second_cache, args.out, only)


if __name__ == "__main__":
    main()
