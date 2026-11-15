"""The baseline: one model asked to read, check and decide by itself.

    python -m benchmark.run_llm_alone --manifest data/scanned/manifest.json \\
        --model google/gemini-3.1-flash-lite --out benchmark/results/gemini_alone

What the model is given:

* **its own reading.** Pages are transcribed one per request with the instruction the
  framework's first reader uses, at the same resolution.
* **the pages again.** The verification request carries every page image alongside the
  transcription, at the reading resolution.
* **an explicit brief.** Correct any debit, credit or balance it misread; check the
  running balance on every row and the closing total exactly; say whether the statement
  is consistent; name the rows where the printed document itself does not add up. The
  answer format has no place for correcting a date or a header field; see
  docs/RESULTS.md for why that does not affect the scores reported. Rows are identified by the
  0-based ``index`` column of the transcription, and the prompt says so.
* **a second chance.** It is then shown its own answer and asked to re-examine it.

No rule is run as code on its behalf, and nothing overrules it: what the model says is
the verdict.

What this is, and is not. It compares two complete workflows. It does not isolate "who
decides", because the framework also differs in other ways: it re-reads one page at a
time at a higher resolution, and it consults a second model family. The experiment that
isolates the deciding step is ``benchmark/ablate_decider.py``.

Three answers are scored per document, and kept apart:

``one_pass``    the first answer;
``self_check``  the re-examined answer, and nothing else: if the model returned no
                usable second answer, the document has no answer in this column;
``final``       the re-examined answer where there is one, otherwise the first answer.
                It is a fallback rule, not a selection of the better answer, and is
                the one the README's headline table uses.

A document with no usable answer (reply cut off, provider error, or not valid JSON) is
never dropped: it stays in the denominator, is reported as "no answer" with the reason,
and counts as not certified.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from probity import Document, DocumentSpec, vlm_proposer
from probity.money import parse_amount_result
from probity.openrouter import OUTPUT_CEILING, BudgetExhausted, image_message

from .convert import statement_to_reading
from .metrics import compare, wilson

VARIANTS = ("one_pass", "self_check", "final")

ANSWER_SCHEMA: dict[str, Any] = {
    "name": "statement_verification",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["corrections", "consistent", "inconsistent_rows", "reason"],
        "properties": {
            "corrections": {
                "type": "array",
                "description": "cells of the transcription you misread, with what is "
                               "actually printed",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["row", "field", "value"],
                    "properties": {
                        "row": {"type": "integer"},
                        "field": {"type": "string",
                                  "enum": ["date", "debit", "credit", "balance"]},
                        "value": {"type": "string",
                                  "description": "the characters printed in that cell; "
                                                 "empty string if the cell is blank"},
                    },
                },
            },
            "opening_balance": {
                "type": ["string", "null"],
                "description": "the opening balance as printed, only if the "
                               "transcription has it wrong; otherwise null"},
            "closing_balance": {
                "type": ["string", "null"],
                "description": "the closing balance as printed, only if the "
                               "transcription has it wrong; otherwise null"},
            "consistent": {
                "type": "boolean",
                "description": "true only if, with your corrections applied, every row's "
                               "balance follows exactly and the closing balance agrees",
            },
            "inconsistent_rows": {
                "type": "array", "items": {"type": "integer"},
                "description": "row indices where the document as printed does not add "
                               "up; empty if the statement is consistent",
            },
            "reason": {"type": "string", "description": "one or two sentences"},
        },
    },
}

TASK = """You are verifying a bank statement for a credit committee.

Attached are the page images of the statement. Below them is a transcription of those
pages, one line per transaction, with the amounts as printed.

Do all of the following.

1. Compare the transcription with the pages. Wherever a date, debit, credit or balance
   was transcribed wrongly, or put in the wrong column, list it under `corrections`
   with the characters actually printed. If the opening or closing balance in the
   transcription is wrong, give the printed one in `opening_balance` or
   `closing_balance`.
2. With your corrections applied, check the arithmetic exactly, with no tolerance:
     - for every row, balance = previous balance + credit - debit
       (the first row starts from the opening balance)
     - opening balance + all movements = closing balance
3. If every row follows and the total agrees, set `consistent` to true and leave
   `inconsistent_rows` empty.
4. If the document as printed does not add up, set `consistent` to false and list under
   `inconsistent_rows` the index of every row where the printed figures break the
   arithmetic. List only rows where the page itself is wrong, not rows you corrected.

Row numbers. Every row is identified by the `index` column of the transcription, which
counts from 0. It is NOT the number printed in the statement's own "No." column, which
counts from 1. Use `index` everywhere in your answer.

Set `consistent` to true only if you would certify this statement."""

#: Two rewordings of the brief, to see whether the result depends on its phrasing. Each
#: asks for exactly the same four things and the same answer format.
TASK_B = """A customer has submitted a bank statement and you must audit it before it is accepted.

You are given the scanned pages and a transcription of them (one line per transaction,
amounts as printed).

Step 1. Go through the transcription against the pages. Any date, debit, credit or
balance that was copied wrongly, or placed in the wrong column, goes in `corrections`
with what the page really shows; a wrong opening or closing balance goes in
`opening_balance` or `closing_balance`.
Step 2. Using the corrected figures, recompute the running balance line by line: each
balance must equal the previous balance plus the credit minus the debit, starting from
the opening balance, and the last balance must equal the closing balance. Exact
equality is required.
Step 3. Report the outcome. If everything reconciles, `consistent` is true and
`inconsistent_rows` is empty. If the page itself is wrong somewhere, `consistent` is
false and `inconsistent_rows` lists every row whose printed figures break the
arithmetic (not the rows you corrected).

Rows are referred to by the `index` column of the transcription, starting at 0. This is
not the "No." printed on the statement, which starts at 1.

Only answer `consistent: true` for a statement you would sign off."""

TASK_C = """Task: decide whether this bank statement adds up.

Inputs: the page images, and below them a transcription of the statement with one row
per transaction.

(a) Fix the transcription. List under `corrections` every date, debit, credit or
    balance that does not match the page, giving the printed characters, and put a
    corrected opening or closing balance in `opening_balance` or `closing_balance`.
(b) Check the sums with the fixed figures, to the last digit: for each row, previous
    balance + credit - debit = balance (the first row uses the opening balance); and
    the final balance = the closing balance.
(c) Conclude. `consistent` = true and `inconsistent_rows` = [] if all of it holds.
    Otherwise `consistent` = false and `inconsistent_rows` = the indexes of the rows
    where what is printed does not add up. Do not include rows that only needed a
    transcription fix.

Use the `index` column (which starts at 0) to refer to rows, not the printed "No."
column (which starts at 1).

`consistent` = true means you certify the statement."""

BRIEFS = {"a": None, "b": TASK_B, "c": TASK_C}      # "a" is TASK, defined above

RECHECK = """Below is the answer you gave. Re-examine it before it is final.

Look at the pages again, recompute the running balance row by row, and confirm or revise
every part of your answer: the corrections, the verdict and the rows you named. Return
the complete final answer in the same form."""


def transcription_as_text(statement) -> str:
    h = statement.header
    lines = [f"opening_balance: {h.opening_balance.raw or ''}",
             f"closing_balance: {h.closing_balance.raw or ''}",
             f"rows: {len(statement.rows)}", "",
             "index | page | date | debit | credit | balance"]
    for r in statement.rows:
        lines.append(f"{r.index} | {r.page} | {r.date.raw or ''} | {r.debit.raw or ''} | "
                     f"{r.credit.raw or ''} | {r.balance.raw or ''}")
    return "\n".join(lines)


def apply_corrections(reading: dict[str, Any], corrections: list[dict], spec,
                      answer: dict[str, Any] | None = None) -> int:
    """Put the model's corrections onto the reading. Returns how many rows it changed.

    Dates, amounts, balances and the two header balances can all be corrected, so the
    model can repair everything the accuracy measure scores.
    """
    from probity.dates import parse_date_result

    touched = set()
    for c in corrections or []:
        i, field = c.get("row"), c.get("field")
        if not isinstance(i, int) or not 0 <= i < len(reading["rows"]):
            continue
        text = str(c.get("value") or "").strip()
        if field == "date":
            got = parse_date_result(text, spec.date_fmt) if text else (None, "empty")
            value = got[0]
            if value is None:
                continue
            new = value.isoformat()
        elif field in ("debit", "credit", "balance"):
            if not text:
                new = None
            else:
                money, err = parse_amount_result(text, spec.locale, spec.currency_default)
                if err or money is None:
                    continue
                new = abs(money.minor) if field in ("debit", "credit") else money.minor
        else:
            continue
        if reading["rows"][i].get(field) != new:
            reading["rows"][i][field] = new
            touched.add(i)
    for name in ("opening_balance", "closing_balance"):
        text = str((answer or {}).get(name) or "").strip()
        if text:
            money, err = parse_amount_result(text, spec.locale, spec.currency_default)
            if not err and money is not None:
                reading[name] = money.minor
    return len(touched)


def _valid(answer: Any) -> dict | None:
    """Accept an answer only if it has the shape that was asked for.

    ``"consistent": "false"`` must not become a certification through ``bool()``.
    """
    if not isinstance(answer, dict) or not isinstance(answer.get("consistent"), bool):
        return None
    rows = answer.get("inconsistent_rows")
    corrections = answer.get("corrections")
    if not isinstance(rows, list) or not isinstance(corrections, list):
        return None
    if not all(isinstance(r, int) and not isinstance(r, bool) for r in rows):
        return None
    for c in corrections:
        if not (isinstance(c, dict) and isinstance(c.get("row"), int)
                and not isinstance(c.get("row"), bool)
                and c.get("field") in ("date", "debit", "credit", "balance")
                and isinstance(c.get("value"), str)):
            return None
    return answer


def ask(client, model, prompt: str, images: list[str], purpose: str,
        max_tokens: int = OUTPUT_CEILING) -> tuple[dict | None, float, str]:
    """One verification request. Returns (answer or None, cost, why there is none)."""
    from probity.proposers.vlm import _parse

    resp = client.chat(model, image_message(prompt, images), json_schema=ANSWER_SCHEMA,
                       max_tokens=max_tokens, purpose=purpose)
    reason = (resp.finish_reason or "").lower()
    if reason in {"length", "max_tokens"}:
        return None, resp.cost_usd, "reply cut off at the token limit"
    if reason == "error":
        return None, resp.cost_usd, "provider error"
    # The same tolerant parser the framework's reader gets: fenced JSON and surrounding
    # prose are accepted.
    answer = _valid(_parse(resp.text or ""))
    if answer is None:
        return None, resp.cost_usd, "reply was not a valid answer"
    return answer, resp.cost_usd, ""


def expected_of(d: dict[str, Any]) -> dict[str, Any]:
    """Group, tier and expected failing rows of a manifest entry (any manifest version)."""
    from .run_scanned import describe

    what = describe(d)
    what["altered_row"] = what["expected_rows"][0] if what["expected_rows"] else None
    return what


def score(answer: dict | None, statement, truth, spec, what: dict[str, Any],
          why: str = "") -> dict[str, Any]:
    reading = statement_to_reading(statement)
    if answer is None:
        # No verdict was given. The reading is scored as transcribed, and reported as
        # the reading only; it is not a verified result.
        cmp = compare(reading, truth)
        return {"answered": False, "no_answer_reason": why, "certified": False,
                "rows_named": [], "named_exactly": False, "target_named": False,
                "rows_changed": 0, "amounts_exact": cmp.ledger_correct,
                "period_dates_exact": cmp.period_correct,
                "field_accuracy": round(cmp.field_accuracy, 4)}
    changed = apply_corrections(reading, answer.get("corrections") or [], spec, answer)
    cmp = compare(reading, truth)
    named = sorted(set(answer.get("inconsistent_rows") or []))
    certified = answer["consistent"] is True
    # Either numbering is accepted for the rows that fail: the 0-based index the prompt
    # asks for, or the 1-based number printed on the page.
    expected = sorted(what["expected_rows"])
    shifted = [r + 1 for r in expected]
    return {"answered": True, "no_answer_reason": "", "certified": certified,
            "rows_named": named,
            # refused, and named exactly the rows that fail and no other
            "named_exactly": (not certified) and bool(expected)
                             and named in (expected, shifted),
            # refused, and every row that fails is among the rows named
            "target_named": (not certified) and bool(expected)
                            and (set(expected) <= set(named) or set(shifted) <= set(named)),
            "rows_changed": changed, "amounts_exact": cmp.ledger_correct,
            "period_dates_exact": cmp.period_correct,
            "field_accuracy": round(cmp.field_accuracy, 4),
            "reason": str(answer.get("reason") or "")[:400]}


JSON_HINT = "\nReply with a single JSON object."


def run_one(d: dict[str, Any], *, model: str, client, json_hint: bool,
            out: Path, max_tokens: int = OUTPUT_CEILING, brief: str = "a") -> dict[str, Any]:
    """One document: transcribe, verify, self-check. Never raises for a model failure."""
    spec = DocumentSpec.load(d["spec"])
    truth = json.loads(Path(d["truth"]).read_text(encoding="utf-8"))
    what = expected_of(d)
    doc = Document(doc_id=d["doc_id"], pdf_path=d["document"])
    # One reader object per document, so documents can run side by side; they share
    # the client, and with it the cache and the spend cap.
    reader = vlm_proposer(model, client=client)
    hint = JSON_HINT if json_hint else ""
    reader.prompt_suffix = hint

    proposal = reader.propose(doc, spec)
    cost = sum(c.cost_usd for c in proposal.model_calls)
    st = proposal.statement
    images = reader._page_images(doc)
    prompt = (BRIEFS[brief] or TASK) + hint + "\n\nTRANSCRIPTION\n" + transcription_as_text(st)

    def safe(text: str, purpose: str) -> tuple[dict | None, float, str]:
        try:
            return ask(client, reader.model, text, images, purpose, max_tokens)
        except BudgetExhausted:
            raise
        except Exception as exc:  # noqa: BLE001 - a failed call is "no answer"
            return None, 0.0, f"request failed: {type(exc).__name__}"

    first, c1, why1 = safe(prompt, "llm_alone:one_pass")
    second, c2, why2 = (None, 0.0, "no first answer to re-examine")
    if first is not None:
        again = (prompt + "\n\n" + RECHECK + "\n\nYOUR ANSWER\n"
                 + json.dumps(first, ensure_ascii=False))
        second, c2, why2 = safe(again, "llm_alone:self_check")

    (out / f"{d['doc_id']}.answers.json").write_text(
        json.dumps({"one_pass": first, "self_check": second}, indent=1,
                   ensure_ascii=False), encoding="utf-8")
    final, why_final = (second, why2) if second is not None else (first, why1)
    return {"doc_id": d["doc_id"], **what, "rows": len(st.rows),
            "one_pass": {**score(first, st, truth, spec, what, why1),
                         "cost_usd": round(cost + c1, 6)},
            "self_check": {**score(second, st, truth, spec, what, why2),
                           "cost_usd": round(cost + c1 + c2, 6)},
            "final": {**score(final, st, truth, spec, what, why_final),
                      "cost_usd": round(cost + c1 + c2, 6)}}


def _failed(d: dict[str, Any], why: str) -> dict[str, Any]:
    """A document the harness could not process still counts, as no answer."""
    what = expected_of(d)
    blank = {"answered": False, "no_answer_reason": why, "certified": False,
             "rows_named": [], "named_exactly": False, "target_named": False,
             "rows_changed": 0, "amounts_exact": False, "period_dates_exact": False,
             "field_accuracy": 0.0,
             "cost_usd": 0.0}
    return {"doc_id": d["doc_id"], **what, "rows": 0,
            **{v: dict(blank) for v in VARIANTS}}


def run(manifest_path: str, *, model: str, out_dir: str, limit: int | None = None,
        cap_usd: float = 3.0, json_hint: bool = False, workers: int = 1,
        max_tokens: int = OUTPUT_CEILING, brief: str = "a",
        only: set[str] | None = None) -> dict[str, Any]:
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
    print(f"model: {model}  (reads, checks and decides; brief {brief})\n")

    with results.open("a", encoding="utf-8") as fh, \
            ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        jobs = {pool.submit(run_one, d, model=model, client=client,
                            json_hint=json_hint, out=out, max_tokens=max_tokens,
                            brief=brief): d
                for d in todo}
        for n, job in enumerate(as_completed(jobs), start=1):
            d = jobs[job]
            try:
                rec = job.result()
            except BudgetExhausted as exc:
                # Every document stays in the denominator, including the ones the
                # budget did not reach.
                print(f"[{n}/{len(todo)}] {d['doc_id'][-27:]} budget exhausted: {exc}"[:200])
                rec = _failed(d, "spend cap reached before this document was answered")
            except Exception as exc:  # noqa: BLE001
                print(f"[{n}/{len(todo)}] {d['doc_id'][-27:]} FAILED: "
                      f"{type(exc).__name__}: {exc}"[:200])
                rec = _failed(d, f"harness error: {type(exc).__name__}")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            line = "  ".join(
                f"{v}: {'CERTIFIED' if rec[v]['certified'] else 'refused':9} "
                f"named {str(rec[v]['rows_named'])[:18]:18}"
                for v in ("one_pass", "final"))
            print(f"[{n}/{len(todo)}] {d['doc_id'][-27:]:27} "
                  f"{'altered@' + str(rec['altered_row']) if rec['altered'] else 'clean':12} "
                  f"{line}")

    return summarise(results)


def _rate(k: int, n: int) -> dict[str, Any]:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "ci95": [round(lo, 3), round(hi, 3)]}


def tally(recs: list[dict[str, Any]], v: str) -> dict[str, Any]:
    """The headline measures for one answer variant over a set of documents."""
    from collections import Counter

    clean = [r for r in recs if not r["altered"]]
    det = [r for r in recs if r["altered"] and r["detectable"]]
    undet = [r for r in recs if r["altered"] and not r["detectable"] and r["group"] != "text"]
    text = [r for r in recs if r["group"] == "text"]
    silent = [r for r in recs if not r[v]["answered"]]
    return {
        "documents": len(recs),
        "no_answer": len(silent),
        "no_answer_reasons": dict(Counter(r[v]["no_answer_reason"] for r in silent)),
        "clean_confirmed": _rate(sum(r[v]["certified"] for r in clean), len(clean)),
        "detectable_confirmed": _rate(sum(r[v]["certified"] for r in det), len(det)),
        "detectable_confirmed_among_answered": _rate(
            sum(r[v]["certified"] for r in det), sum(r[v]["answered"] for r in det)),
        "detectable_located": _rate(sum(r[v]["target_named"] for r in det), len(det)),
        "detectable_located_exactly": _rate(sum(r[v]["named_exactly"] for r in det), len(det)),
        "undetectable_confirmed": _rate(sum(r[v]["certified"] for r in undet), len(undet)),
        "text_alteration_confirmed": _rate(sum(r[v]["certified"] for r in text), len(text)),
        "ledger_exact": _rate(sum(bool(r[v]["amounts_exact"]) for r in recs), len(recs)),
        "period_exact": _rate(sum(bool(r[v].get("period_dates_exact")) for r in recs), len(recs)),
        "cost_per_document_usd": round(sum(r[v]["cost_usd"] for r in recs) / len(recs), 4)
        if recs else 0.0,
    }


def summarise(results: Path) -> dict[str, Any]:
    recs = [json.loads(l) for l in results.read_text().splitlines() if l.strip()]
    for r in recs:                      # outcome files written before groups existed
        r.setdefault("group", "amount" if r["altered"] else "clean")
        r.setdefault("tier", "T1")
        r.setdefault("detectable", r["altered"])
        r.setdefault("expected_rows", [] if r.get("altered_row") is None else [r["altered_row"]])
    summary: dict[str, Any] = {"documents": len(recs)}
    for v in VARIANTS:
        m = tally(recs, v)
        m["by_group"] = {g: tally([r for r in recs if r["group"] == g], v)
                         for g in sorted({r["group"] for r in recs})}
        m["by_tier"] = {t: tally([r for r in recs if r["tier"] == t], v)
                        for t in sorted({r["tier"] for r in recs})}
        summary[v] = m
        show = lambda key: f"{m[key]['k']} of {m[key]['n']}"  # noqa: E731
        print(f"\n{v}")
        print(f"  no usable answer                              : {m['no_answer']} of "
              f"{len(recs)} {m['no_answer_reasons'] or ''}")
        print(f"  clean confirmed                               : {show('clean_confirmed')}")
        print(f"  detectable alterations confirmed (want 0)     : {show('detectable_confirmed')}")
        print(f"  detectable alterations located exactly        : {show('detectable_located_exactly')}")
        print(f"  detectable alterations located                : {show('detectable_located')}")
        print(f"  undetectable alterations confirmed            : {show('undetectable_confirmed')}")
        print(f"  ledger exact                                  : {show('ledger_exact')}")
        print(f"  cost per document (as run)                    : ${m['cost_per_document_usd']:.4f}")
    (results.parent / "summary.json").write_text(json.dumps(summary, indent=1),
                                                 encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--model", default="google/gemini-3.1-flash-lite")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--cap-usd", type=float, default=3.0)
    ap.add_argument("--out", default="benchmark/results/llm_alone")
    ap.add_argument("--max-tokens", type=int, default=OUTPUT_CEILING,
                    help="reply budget for the verification requests; raise it for a "
                         "model that reasons at length before answering")
    ap.add_argument("--workers", type=int, default=1,
                    help="documents to run side by side")
    ap.add_argument("--json-hint", action="store_true",
                    help="append a one-line reminder to reply in JSON, which some "
                         "providers require before they accept a structured request")
    ap.add_argument("--brief", choices=list(BRIEFS), default="a",
                    help="which wording of the brief to use")
    ap.add_argument("--subset", default=None, help="a JSON file listing the doc_ids to run")
    args = ap.parse_args()
    only = set(json.loads(Path(args.subset).read_text())) if args.subset else None
    run(args.manifest, model=args.model, out_dir=args.out, limit=args.limit,
        cap_usd=args.cap_usd, json_hint=args.json_hint, workers=args.workers,
        max_tokens=args.max_tokens, brief=args.brief, only=only)


if __name__ == "__main__":
    main()
