"""The baseline with an interpreter: one model reads, computes what it likes, and decides.

    python -m benchmark.run_code_tool --manifest data/sealed/manifest.json \\
        --model google/gemini-3.1-flash-lite --out benchmark/results/gemini_code_tool

The model transcribes the statement exactly as in ``run_llm_alone``. It is then given
the page images, its transcription (both as printed and as integers in minor units, so
that parsing is not what is being tested), the same brief, and a Python interpreter it
may call up to six times. Its final answer has the same form and is scored the same way.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from probity import Document, DocumentSpec, vlm_proposer
from probity.openrouter import BudgetExhausted
from probity.proposers.vlm import _parse

from .code_tool import converse
from .run_llm_alone import (ANSWER_SCHEMA, JSON_HINT, TASK, _valid, expected_of, score,
                            summarise, transcription_as_text)

TOOL_NOTE = """

You have a Python interpreter (`run_python`). The variable `data` holds your
transcription: `data["opening_balance"]`, `data["closing_balance"]` and `data["rows"]`,
a list with `index`, `page`, `date`, and for each of `debit`, `credit` and `balance` both
the characters as printed and an integer in minor units (`debit_minor`, `credit_minor`,
`balance_minor`; null where the cell is blank). Use it to do the arithmetic exactly. You
may call it up to six times, then answer."""


def as_data(statement) -> dict[str, Any]:
    def minor(f):
        return getattr(getattr(f, "value", None), "minor", None)

    h = statement.header
    return {"opening_balance": h.opening_balance.raw, "opening_balance_minor": minor(h.opening_balance),
            "closing_balance": h.closing_balance.raw, "closing_balance_minor": minor(h.closing_balance),
            "rows": [{"index": r.index, "page": r.page, "date": r.date.raw,
                      "debit": r.debit.raw, "debit_minor": minor(r.debit),
                      "credit": r.credit.raw, "credit_minor": minor(r.credit),
                      "balance": r.balance.raw, "balance_minor": minor(r.balance)}
                     for r in statement.rows]}


def run_one(d: dict[str, Any], *, model: str, client, json_hint: bool, out: Path) -> dict[str, Any]:
    spec = DocumentSpec.load(d["spec"])
    truth = json.loads(Path(d["truth"]).read_text(encoding="utf-8"))
    what = expected_of(d)
    doc = Document(doc_id=d["doc_id"], pdf_path=d["document"])
    reader = vlm_proposer(model, client=client)
    hint = JSON_HINT if json_hint else ""
    reader.prompt_suffix = hint
    proposal = reader.propose(doc, spec)
    cost = sum(c.cost_usd for c in proposal.model_calls)
    st = proposal.statement
    prompt = TASK + TOOL_NOTE + hint + "\n\nTRANSCRIPTION\n" + transcription_as_text(st)
    try:
        text, c, calls, why = converse(client, reader.model, prompt, reader._page_images(doc),
                                       as_data(st), answer_schema=ANSWER_SCHEMA,
                                       purpose="code_tool")
    except BudgetExhausted:
        raise
    except Exception as exc:  # noqa: BLE001
        text, c, calls, why = None, 0.0, 0, f"request failed: {type(exc).__name__}"
    answer = _valid(_parse(text or "")) if text else None
    if text and answer is None:
        why = "reply was not a valid answer"
    (out / f"{d['doc_id']}.answer.json").write_text(
        json.dumps({"answer": answer, "interpreter_calls": calls}, indent=1,
                   ensure_ascii=False), encoding="utf-8")
    block = {**score(answer, st, truth, spec, what, why), "cost_usd": round(cost + c, 6),
             "interpreter_calls": calls}
    return {"doc_id": d["doc_id"], **what, "rows": len(st.rows),
            "one_pass": block, "self_check": block, "final": block}


def run(manifest_path: str, *, model: str, out_dir: str, limit: int | None = None,
        cap_usd: float = 3.0, json_hint: bool = False, workers: int = 1) -> dict[str, Any]:
    docs = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["documents"]
    if limit:
        docs = docs[:limit]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = out / "outcomes.jsonl"
    done = ({json.loads(l)["doc_id"] for l in results.read_text().splitlines() if l.strip()}
            if results.exists() else set())
    todo = [d for d in docs if d["doc_id"] not in done]
    client = vlm_proposer(model, cap_usd=cap_usd, cache_dir=str(out / ".cache")).client
    print(f"model with an interpreter: {model}\n")
    with results.open("a", encoding="utf-8") as fh, \
            ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        jobs = {pool.submit(run_one, d, model=model, client=client, json_hint=json_hint,
                            out=out): d for d in todo}
        for n, job in enumerate(as_completed(jobs), start=1):
            d = jobs[job]
            try:
                rec = job.result()
            except Exception as exc:  # noqa: BLE001 - the document stays in the denominator
                from .run_llm_alone import _failed
                rec = _failed(d, f"{type(exc).__name__}"[:60])
                rec["final"]["interpreter_calls"] = 0
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            f = rec["final"]
            print(f"[{n}/{len(todo)}] {d['doc_id'][-34:]:34} "
                  f"{'CERTIFIED' if f['certified'] else 'refused':9} named {str(f['rows_named'])[:22]:22} "
                  f"calls {f.get('interpreter_calls', 0)}")
    return summarise(results)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--model", default="google/gemini-3.1-flash-lite")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--cap-usd", type=float, default=3.0)
    ap.add_argument("--out", default="benchmark/results/code_tool")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--json-hint", action="store_true")
    args = ap.parse_args()
    run(args.manifest, model=args.model, out_dir=args.out, limit=args.limit,
        cap_usd=args.cap_usd, json_hint=args.json_hint, workers=args.workers)


if __name__ == "__main__":
    main()
