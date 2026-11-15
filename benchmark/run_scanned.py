"""Run the machine over a set of scanned statements and score it against the answer key.

    python -m benchmark.run_scanned --manifest data/scanned/manifest.json \\
        --model google/gemini-3.1-flash-lite \\
        --second-model qwen/qwen3.5-flash-02-23 \\
        --out benchmark/results/scanned

Leave out ``--second-model`` to measure the reader on its own, decided by the same
rules. Everything else is identical, and model replies are cached by content, so adding
the second reader to a finished run pays only for the second reader.

For each document it writes the certificate, the decision log, the trace and the
readable report, and appends one scored line to ``outcomes.jsonl``. Three things are
scored, separately:

* **conclusion** -- a clean document should be ``CONFIRMED``; an altered one should not;
* **location** -- for an altered document, the rows left failing should be exactly the
  altered row, with both readers agreeing on what is printed there;
* **reading** -- the final transcription against the answer key: every debit, credit,
  balance and date, plus the header balances and period dates. Descriptions are compared
  separately and are not part of this figure. For an altered document the answer key is
  the altered figure, because that is what the page says.

Model replies are not deterministic. ``--out`` with an empty cache is a fresh sample of
them; re-running into the same ``--out`` replays the cached sample.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from probity import (Document, DocumentSpec, Pipeline, default_proposers, render_report,
                     vlm_proposer)
from probity.openrouter import BudgetExhausted

from .convert import statement_to_reading
from .metrics import compare, wilson


def describe(doc: dict[str, Any]) -> dict[str, Any]:
    """What a manifest entry says should happen, in one shape for every manifest.

    ``expected_rows`` are the rows on which the running balance fails in a perfect
    transcription of the document: empty for a clean statement and for an alteration
    that keeps the arithmetic intact.
    """
    if "group" in doc and "expected_rows" in doc:
        group = doc["group"]
        return {"group": group, "tier": doc.get("tier", "T1"),
                "altered": group != "clean",
                "detectable": bool(doc.get("detectable_by_arithmetic")),
                "expected_rows": sorted(doc.get("expected_rows") or [])}
    row = ((doc.get("inconsistency") or {}).get("detail") or {}).get("row")
    return {"group": "amount" if row is not None else "clean", "tier": "T1",
            "altered": row is not None, "detectable": row is not None,
            "expected_rows": [] if row is None else [row]}


JSON_HINT = "\nReply with a single JSON object."


def run_one(doc: dict[str, Any], *, model: str, second_model: str | None, client,
            out: Path, cap_usd: float, json_hint: bool = False) -> dict[str, Any]:
    """One document through the machine, with its artefacts written and its score."""
    spec = DocumentSpec.load(doc["spec"])
    truth = json.loads(Path(doc["truth"]).read_text(encoding="utf-8"))
    what = describe(doc)
    # Reader objects are per document so documents can run side by side; they share the
    # client, and with it the cache and the spend cap.
    reader = vlm_proposer(model, client=client)
    if json_hint:
        # Some providers refuse a structured request unless the prompt says "json".
        reader.prompt_suffix = JSON_HINT
    second = (vlm_proposer(second_model, tier="checker", client=client)
              if second_model else None)
    t0 = time.perf_counter()
    result = Pipeline(spec, default_proposers(llm_small=reader, checker=second),
                      max_usd=cap_usd).run(
        Document(doc_id=doc["doc_id"], pdf_path=doc["document"]))
    seconds = time.perf_counter() - t0

    cert = result.certificate.to_json()
    stem = out / doc["doc_id"]
    Path(f"{stem}.certificate.json").write_text(result.certificate.dumps(), encoding="utf-8")
    Path(f"{stem}.explain.txt").write_text(result.trace.explain(), encoding="utf-8")
    Path(f"{stem}.trace.jsonl").write_text(result.trace.to_jsonl() + "\n", encoding="utf-8")
    Path(f"{stem}.report.md").write_text(render_report(cert), encoding="utf-8")

    reading = (statement_to_reading(result.statement) if result.statement
               else {"rows": []})
    cmp = compare(reading, truth, doc_id=doc["doc_id"])
    failing = sorted({f["location"]["row_index"]
                      for f in cert["invariants"].get("failures", [])
                      if f.get("location", {}).get("scope") == "row"})
    calls = cert["provenance"]["model_calls"]
    return {
        "doc_id": doc["doc_id"], "group": what["group"], "tier": what["tier"],
        "altered": what["altered"], "detectable": what["detectable"],
        "expected_rows": what["expected_rows"],
        "altered_row": what["expected_rows"][0] if what["expected_rows"] else None,
        "conclusion": result.conclusion,
        "conclusion_reason": result.conclusion_reason,
        "rows_failing": failing,
        "rows_corrected": sorted({c["row"] for c in result.corrections}),
        "corrected_by": sorted({c.get("method", "second_reader")
                                for c in result.corrections}),
        # every debit, credit, balance and date, and the header balances and dates
        "amounts_and_dates_exact": cmp.ledger_correct,
        "period_dates_exact": cmp.period_correct,
        "field_accuracy": round(cmp.field_accuracy, 4),
        "rows_matched": cmp.rows_matched, "rows_expected": cmp.rows_expected,
        "descriptions_wrong": cmp.description_wrong,
        "descriptions_total": cmp.description_total,
        "second_reader_calls": sum(c.get("purpose") == "second_opinion" for c in calls),
        "cached_calls": sum(bool(c.get("cached")) for c in calls),
        "cost_usd": round(result.trace.total_cost(), 6),
        "seconds": round(seconds, 1),
    }


def run(manifest_path: str, *, model: str, second_model: str | None, out_dir: str,
        limit: int | None = None, cap_usd: float = 5.0, workers: int = 1,
        json_hint: bool = False, only: set[str] | None = None) -> dict[str, Any]:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    docs = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["documents"]
    if only is not None:
        docs = [d for d in docs if d["doc_id"] in only]
    if limit:
        docs = docs[:limit]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = out / "outcomes.jsonl"
    done = ({json.loads(l)["doc_id"] for l in results.read_text().splitlines() if l.strip()}
            if results.exists() else set())
    todo = [d for d in docs if d["doc_id"] not in done]

    client = vlm_proposer(model, cap_usd=cap_usd, cache_dir=str(out / ".cache")).client
    print(f"reader        : {model}")
    print(f"second reader : {second_model or 'none'}\n")

    with results.open("a", encoding="utf-8") as fh, \
            ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        jobs = {pool.submit(run_one, d, model=model, second_model=second_model,
                            client=client, out=out, cap_usd=cap_usd,
                            json_hint=json_hint): d for d in todo}
        for n, job in enumerate(as_completed(jobs), start=1):
            d = jobs[job]
            try:
                rec = job.result()
            except Exception as exc:  # noqa: BLE001 - the document stays in the denominator
                what = describe(d)
                rec = {"doc_id": d["doc_id"], "group": what["group"], "tier": what["tier"],
                       "altered": what["altered"], "detectable": what["detectable"],
                       "expected_rows": what["expected_rows"],
                       "altered_row": what["expected_rows"][0] if what["expected_rows"] else None,
                       "conclusion": "UNRESOLVED",
                       "conclusion_reason": f"not processed: {type(exc).__name__}: {exc}"[:200],
                       "rows_failing": [], "rows_corrected": [], "corrected_by": [],
                       "amounts_and_dates_exact": False, "period_dates_exact": False,
                       "field_accuracy": 0.0, "rows_matched": 0, "rows_expected": 0,
                       "descriptions_wrong": 0, "descriptions_total": 0,
                       "second_reader_calls": 0, "cached_calls": 0, "cost_usd": 0.0,
                       "seconds": 0.0}
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"[{n}/{len(todo)}] {d['doc_id'][-34:]:34} "
                  f"{'altered' if rec['altered'] else 'clean':7} {rec['conclusion']:22} "
                  f"corrected {len(rec['rows_corrected']):3d}  ${rec['cost_usd']:.4f}")

    return summarise(results)


def _rate(k: int, n: int) -> dict[str, Any]:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "ci95": [round(lo, 3), round(hi, 3)]}


def tally(recs: list[dict[str, Any]]) -> dict[str, Any]:
    """The headline measures over a set of scored documents."""
    clean = [r for r in recs if not r["altered"]]
    det = [r for r in recs if r["altered"] and r["detectable"]]
    # The arithmetic blind spot proper: figures altered so that the statement still
    # ties. A text-only alteration is a different case and is counted on its own.
    undet = [r for r in recs if r["altered"] and not r["detectable"] and r["group"] != "text"]
    text = [r for r in recs if r["group"] == "text"]
    named = lambda r: r["conclusion"] == "DOCUMENT_INCONSISTENT"  # noqa: E731
    return {
        "documents": len(recs),
        "clean_confirmed": _rate(sum(r["conclusion"] == "CONFIRMED" for r in clean), len(clean)),
        "clean_unresolved": _rate(sum(r["conclusion"] == "UNRESOLVED" for r in clean), len(clean)),
        "clean_reported": _rate(sum(named(r) for r in clean), len(clean)),
        # alterations that break the arithmetic: none should be confirmed
        "detectable_confirmed": _rate(sum(r["conclusion"] == "CONFIRMED" for r in det), len(det)),
        "detectable_reported": _rate(sum(named(r) for r in det), len(det)),
        "detectable_located": _rate(
            sum(named(r) and set(r["expected_rows"]) <= set(r["rows_failing"]) for r in det),
            len(det)),
        "detectable_located_exactly": _rate(
            sum(named(r) and r["rows_failing"] == r["expected_rows"] for r in det), len(det)),
        "detectable_only_expected_rows_failing": _rate(
            sum(r["rows_failing"] == r["expected_rows"] for r in det), len(det)),
        # alterations that keep the arithmetic intact: the rules cannot see these
        "undetectable_confirmed": _rate(
            sum(r["conclusion"] == "CONFIRMED" for r in undet), len(undet)),
        "text_alteration_confirmed": _rate(
            sum(r["conclusion"] == "CONFIRMED" for r in text), len(text)),
        "ledger_exact": _rate(sum(bool(r["amounts_and_dates_exact"]) for r in recs), len(recs)),
        "conclusions": {c: sum(r["conclusion"] == c for r in recs)
                        for c in ("CONFIRMED", "DOCUMENT_INCONSISTENT", "UNRESOLVED")},
        "rows_corrected": sum(len(r["rows_corrected"]) for r in recs),
    }


def summarise(results: Path) -> dict[str, Any]:
    recs = [json.loads(l) for l in results.read_text().splitlines() if l.strip()]
    for r in recs:                      # outcome files written before groups existed
        r.setdefault("group", "amount" if r["altered"] else "clean")
        r.setdefault("tier", "T1")
        r.setdefault("detectable", r["altered"])
        r.setdefault("expected_rows", [] if r.get("altered_row") is None else [r["altered_row"]])
    cost = sum(r["cost_usd"] for r in recs)
    cached = sum(r.get("cached_calls", 0) for r in recs)
    summary = tally(recs)
    summary["by_group"] = {g: tally([r for r in recs if r["group"] == g])
                           for g in sorted({r["group"] for r in recs})}
    summary["by_tier"] = {t: tally([r for r in recs if r["tier"] == t])
                          for t in sorted({r["tier"] for r in recs})}
    summary.update({
        "descriptions_wrong": [sum(r.get("descriptions_wrong", 0) for r in recs),
                               sum(r.get("descriptions_total", 0) for r in recs)],
        "second_reader_calls": sum(r.get("second_reader_calls", 0) for r in recs),
        "cost_usd_as_run": round(cost, 4),
        "cost_per_document_usd_as_run": round(cost / len(recs), 4) if recs else 0.0,
        "model_calls_served_from_cache": cached,
        # kept under their earlier names for the 20-document record
        "clean_confirmed_legacy": [summary["clean_confirmed"]["k"], summary["clean_confirmed"]["n"]],
    })

    def show(label: str, key: str) -> None:
        v = summary[key]
        print(f"{label:46}: {v['k']} of {v['n']}")

    print()
    show("clean confirmed", "clean_confirmed")
    show("detectable alterations confirmed (want 0)", "detectable_confirmed")
    show("detectable alterations located exactly", "detectable_located_exactly")
    show("detectable alterations located", "detectable_located")
    show("undetectable alterations confirmed (expected)", "undetectable_confirmed")
    show("ledger exact", "ledger_exact")
    print(f"{'rows corrected':46}: {summary['rows_corrected']}")
    print(f"{'cost as run':46}: ${cost:.3f} (${summary['cost_per_document_usd_as_run']:.4f} "
          f"per document; {cached} calls from the cache)")
    (results.parent / "summary.json").write_text(json.dumps(summary, indent=1),
                                                 encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--model", default="google/gemini-3.1-flash-lite",
                    help="the first reader")
    ap.add_argument("--second-model", default=None,
                    help="a different model, asked only for pages where a rule failed")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--cap-usd", type=float, default=5.0)
    ap.add_argument("--out", default="benchmark/results/scanned")
    ap.add_argument("--workers", type=int, default=1,
                    help="documents to run side by side")
    ap.add_argument("--json-hint", action="store_true",
                    help="add a one-line JSON reminder to the first reader's prompt")
    ap.add_argument("--subset", default=None,
                    help="a JSON file listing the doc_ids to run")
    args = ap.parse_args()
    only = set(json.loads(Path(args.subset).read_text())) if args.subset else None
    run(args.manifest, model=args.model, second_model=args.second_model,
        out_dir=args.out, limit=args.limit, cap_usd=args.cap_usd, workers=args.workers,
        json_hint=args.json_hint, only=only)


if __name__ == "__main__":
    main()
