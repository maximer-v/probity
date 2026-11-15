"""Receipts: the method and its baselines on a second document type.

    python -m benchmark.run_receipts --manifest data/receipts/manifest.json \\
        --condition probity --out benchmark/results/receipts_probity

Conditions:

``probity``        first reader, second reader, third reading, rules decide
``gemini_alone``   the first model transcribes, checks, re-examines and decides
``qwen_alone``     the second model does the same
``code_tool``      the first model with a Python interpreter
``ocr_rules``      conventional OCR, a keyword parser, and the same rules; no LLM

Scoring is the same for all of them:

* *confirmed*: the final word is that the receipt is consistent;
* *reported*: the final word is that it is not, with the rules that fail named;
* *located*: reported, and a rule that should fail is among those named;
* *reading exact*: the total, subtotal, tax, service, cash and change, and the line
  amounts in printed order, equal the answer key.

``ocr_rules`` has one deterministic reader and nothing to compare it with, so a receipt
on which a rule fails is scored as reported at that rule. That lets it earn credit for
finding an alteration, and costs it a false report whenever it misreads a clean receipt.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from probity.forms import (CONFIRMED, INCONSISTENT, FormPipeline, FormReader, FormSpec,
                           build_reading, check, parse_money, render_report)

from .metrics import wilson
from .receipts import SPEC_PATH

FIRST, SECOND = "google/gemini-3.1-flash-lite", "qwen/qwen3.5-flash-02-23"
MONEY_FIELDS = ("subtotal", "tax", "service", "total", "cash", "change")

ANSWER_SCHEMA = {"name": "receipt_verification", "schema": {
    "type": "object", "additionalProperties": False,
    "required": ["corrections", "items", "consistent", "failing_rules", "reason"],
    "properties": {
        "corrections": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["where", "value"],
            "properties": {"where": {"type": "string",
                                     "description": "a field name, or items[i].quantity, "
                                                    "items[i].unit_price or items[i].price"},
                           "value": {"type": ["string", "null"]}}}},
        "items": {"type": ["array", "null"],
                  "description": "only if the transcription has lines missing, extra or "
                                 "merged: the complete corrected list of lines; "
                                 "otherwise null",
                  "items": {"type": "object", "additionalProperties": False,
                            "required": ["name", "quantity", "unit_price", "price"],
                            "properties": {k: {"type": ["string", "null"]} for k in
                                           ("name", "quantity", "unit_price", "price")}}},
        "consistent": {"type": "boolean"},
        "failing_rules": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"}}}}


def brief(spec: FormSpec) -> str:
    rules = "\n".join(f"  - {r.id}: {r.check}" + (f"   (applies when {r.when})" if r.when else "")
                      + (f"   (for each line of {r.for_each})" if r.for_each else "")
                      for r in spec.rules)
    return f"""You are verifying a receipt.

Attached is the image of the receipt. Below it is a transcription of it.

Do all of the following.

1. Compare the transcription with the image. Wherever a value was transcribed wrongly,
   list it under `corrections`, with `where` set to the field name (for example `total`)
   or to `items[i].price`, `items[i].quantity` or `items[i].unit_price` for line i
   counted from 0, and the characters actually printed (null if nothing is printed). If
   lines are missing, extra or merged, give the complete corrected list in `items`
   instead; otherwise set `items` to null.
2. With your corrections applied, check these rules exactly, with no tolerance:
{rules}
3. If every rule that applies holds, set `consistent` to true and leave `failing_rules`
   empty. Otherwise set `consistent` to false and list the ids of the rules that fail.

Set `consistent` to true only if you would certify this receipt.
Reply with a single JSON object."""


RECHECK = """Below is the answer you gave. Re-examine it before it is final: look at the
image again, redo the sums, and confirm or revise every part. Return the complete final
answer in the same form."""


# ---------------------------------------------------------------------- scoring

def exact(form: dict[str, Any], truth: dict[str, Any], spec: FormSpec) -> bool:
    a, b = build_reading(form, spec), build_reading(truth, spec)
    if any(a.fields.get(f) != b.fields.get(f) for f in MONEY_FIELDS):
        return False
    # In printed order: the same amounts on different lines is not the same reading.
    return [r.get("price") for r in a.tables["items"]] == \
        [r.get("price") for r in b.tables["items"]]


def record(doc: dict[str, Any], truth: dict[str, Any], spec: FormSpec, *, confirmed: bool,
           reported: bool, rules_named: list[str], form: dict[str, Any] | None,
           answered: bool = True, cost: float = 0.0, note: str = "",
           corrections: int = 0) -> dict[str, Any]:
    expected = sorted((truth.get("alteration") or {}).get("expected_rules") or [])
    return {"doc_id": doc["doc_id"], "altered": doc["group"] == "altered",
            "expected_rules": expected, "answered": answered,
            "confirmed": bool(confirmed), "reported": bool(reported),
            "rules_named": sorted(set(rules_named)),
            "located": bool(reported and set(expected) & set(rules_named)),
            "reading_exact": bool(form is not None and exact(form, truth["form"], spec)),
            "corrections": corrections, "cost_usd": round(cost, 6), "note": note[:300]}


def _as_form(reading) -> dict[str, Any]:
    return {**reading.fields, "items": reading.tables.get("items", [])}


# ------------------------------------------------------------------- conditions

def run_probity(doc, truth, spec, client, models, out) -> dict[str, Any]:
    first, second = FormReader(client, models[FIRST]), FormReader(client, models[SECOND])
    pipeline = FormPipeline(spec, first, second, FormReader(client, models[FIRST], scale=1.6))
    result = pipeline.run(doc["doc_id"], doc["document"])
    (out / f"{doc['doc_id']}.report.md").write_text(render_report(result, spec), encoding="utf-8")
    (out / f"{doc['doc_id']}.result.json").write_text(
        json.dumps(result.to_json(), indent=1, ensure_ascii=False), encoding="utf-8")
    return record(doc, truth, spec, confirmed=result.conclusion == CONFIRMED,
                  reported=result.conclusion == INCONSISTENT,
                  rules_named=[f.rule for f in result.failures], form=_as_form(result.reading),
                  cost=result.cost_usd, note=result.reason, corrections=len(result.corrections))


def _apply_answer(form: dict[str, Any], answer: dict[str, Any]) -> int:
    import re

    changed = 0
    if isinstance(answer.get("items"), list) and all(
            isinstance(r, dict) for r in answer["items"]):
        form["items"] = [dict(r) for r in answer["items"]]
        changed += 1
    for c in answer.get("corrections") or []:
        where, value = str(c.get("where", "")), c.get("value")
        m = re.fullmatch(r"items\[(\d+)\]\.(price|quantity|unit_price)", where)
        if m and int(m.group(1)) < len(form["items"]):
            form["items"][int(m.group(1))][m.group(2)] = value
            changed += 1
        elif where in MONEY_FIELDS or where == "discount":
            form[where] = value
            changed += 1
    return changed


def _valid(answer: Any) -> dict | None:
    if not isinstance(answer, dict) or not isinstance(answer.get("consistent"), bool):
        return None
    if not isinstance(answer.get("failing_rules"), list) or not isinstance(
            answer.get("corrections"), list):
        return None
    if not all(isinstance(c, dict) for c in answer["corrections"]):
        return None
    return answer


def run_alone(doc, truth, spec, client, models, out, *, model: str,
              code_tool: bool = False) -> dict[str, Any]:
    from probity.openrouter import OUTPUT_CEILING, image_message
    from probity.proposers.vlm import _parse

    reading = FormReader(client, models[model]).read(doc["document"], spec)
    cost = reading.cost_usd
    if reading.error:
        return record(doc, truth, spec, confirmed=False, reported=False, rules_named=[],
                      form=None, answered=False, cost=cost, note=reading.error)
    printed = {k: reading.raw.get(k) for k in list(spec.fields) + list(spec.tables)}
    prompt = brief(spec) + "\n\nTRANSCRIPTION\n" + json.dumps(printed, ensure_ascii=False, indent=1)
    budget = 65536 if "qwen" in model else OUTPUT_CEILING

    def ask(text: str, purpose: str) -> tuple[dict | None, float, str]:
        try:
            resp = client.chat(models[model], image_message(text, [doc["document"]]),
                               json_schema=ANSWER_SCHEMA, max_tokens=budget, purpose=purpose)
        except Exception as exc:  # noqa: BLE001
            return None, 0.0, f"request failed: {type(exc).__name__}"
        if (resp.finish_reason or "").lower() in {"length", "max_tokens", "error"}:
            return None, resp.cost_usd, f"reply ended with {resp.finish_reason}"
        answer = _valid(_parse(resp.text or ""))
        return answer, resp.cost_usd, "" if answer else "reply was not a valid answer"

    if code_tool:
        from .code_tool import converse

        data = {**{k: reading.fields.get(k) for k in spec.fields},
                "items": reading.tables.get("items", []), "printed": printed}
        note = ("\n\nYou have a Python interpreter (`run_python`). The variable `data` holds "
                "your transcription with amounts as integers (`data['total']`, "
                "`data['items'][i]['price']`, ...; null where nothing was printed) and "
                "`data['printed']` with the characters as printed. Use it to do the sums "
                "exactly. You may call it up to six times, then answer.")
        try:
            text, c, _calls, why = converse(client, models[model], prompt + note,
                                            [doc["document"]], data,
                                            answer_schema=ANSWER_SCHEMA, purpose="code_tool")
        except Exception as exc:  # noqa: BLE001
            text, c, why = None, 0.0, f"request failed: {type(exc).__name__}"
        cost += c
        final = _valid(_parse(text or "")) if text else None
        if text and final is None:
            why = "reply was not a valid answer"
    else:
        first, c1, why = ask(prompt, "llm_alone:one_pass")
        cost += c1
        final = first
        if first is not None:
            again = prompt + "\n\n" + RECHECK + "\n\nYOUR ANSWER\n" + json.dumps(first, ensure_ascii=False)
            second, c2, why2 = ask(again, "llm_alone:self_check")
            cost += c2
            if second is not None:
                final = second
    (out / f"{doc['doc_id']}.answer.json").write_text(
        json.dumps(final, indent=1, ensure_ascii=False), encoding="utf-8")
    form = {**{k: printed.get(k) for k in spec.fields},
            "items": [dict(r) for r in (printed.get("items") or []) if isinstance(r, dict)]}
    if final is None:
        return record(doc, truth, spec, confirmed=False, reported=False, rules_named=[],
                      form=form, answered=False, cost=cost, note=why)
    n = _apply_answer(form, final)
    return record(doc, truth, spec, confirmed=final["consistent"],
                  reported=not final["consistent"],
                  rules_named=[str(r) for r in final["failing_rules"]], form=form,
                  cost=cost, note=str(final.get("reason", "")), corrections=n)


#: Label keywords, in the order they are tested. "sub total" before "total", and
#: "total" before the payment words, because receipts print "TOTAL BAYAR" (total to pay).
_KEYS = (("subtotal", ("sub total", "subtotal", "sub-total", "net sales", "jumlah")),
         ("total", ("grand total", "total")),
         ("tax", ("tax", "pajak", "ppn", "pb1", "pb 1", "vat")),
         ("service", ("service", "serv.", "svc")),
         ("change", ("change", "kembali", "kembalian")),
         ("cash", ("cash", "tunai", "bayar", "paid", "payment")))


def classify(label: str) -> str | None:
    label = " ".join(label.lower().split())
    for field, words in _KEYS:
        if any(w in label for w in words):
            return field
    return None


def parse_ocr_lines(lines: list[str]) -> dict[str, Any]:
    """Receipt lines to the form, by keywords: the last number on a line is its amount."""
    import re

    form: dict[str, Any] = {k: None for k in MONEY_FIELDS}
    form.update({"discount": None, "items": []})
    amount = re.compile(r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?")
    in_totals = False
    for text in lines:
        found = amount.findall(text)
        if not found:
            continue
        label = amount.sub(" ", text)
        field = classify(label)
        if field:
            in_totals = True
            if form[field] is None:
                form[field] = found[-1]
        elif not in_totals and any(ch.isalpha() for ch in label):
            form["items"].append({"name": " ".join(label.split()), "quantity": None,
                                  "unit_price": None, "price": found[-1]})
    return form


def ocr_form(image_path: str) -> dict[str, Any]:
    """A receipt read by conventional OCR and keywords. No model, no learning."""
    from rapidocr_onnxruntime import RapidOCR

    global _OCR
    try:
        _OCR
    except NameError:
        _OCR = RapidOCR()
    result, _ = _OCR(image_path)
    boxes = [(sum(p[1] for p in b) / 4.0, min(p[0] for p in b), str(t)) for b, t, _c in result or []]
    boxes.sort()
    lines: list[list[tuple[float, str]]] = []
    last_y = None
    for y, x, text in boxes:
        if last_y is None or abs(y - last_y) > 9:
            lines.append([])
        lines[-1].append((x, text))
        last_y = y
    return parse_ocr_lines([" ".join(t for _x, t in sorted(line)) for line in lines])


def run_ocr(doc, truth, spec, client, models, out) -> dict[str, Any]:
    form = ocr_form(doc["document"])
    reading = build_reading(form, spec)
    failures = check(reading, spec)
    unread = reading.fields.get("total") is None or not reading.tables["items"]
    return record(doc, truth, spec, confirmed=not failures and not unread,
                  reported=bool(failures) and not unread,
                  rules_named=[f.rule for f in failures], form=form,
                  note="nothing usable was read" if unread else "")


CONDITIONS = {
    "probity": run_probity,
    "gemini_alone": lambda *a: run_alone(*a, model=FIRST),
    "qwen_alone": lambda *a: run_alone(*a, model=SECOND),
    "code_tool": lambda *a: run_alone(*a, model=FIRST, code_tool=True),
    "ocr_rules": run_ocr,
}


def _rate(k: int, n: int) -> dict[str, Any]:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "ci95": [round(lo, 3), round(hi, 3)]}


def summarise(results: Path) -> dict[str, Any]:
    recs = [json.loads(l) for l in results.read_text().splitlines() if l.strip()]
    clean = [r for r in recs if not r["altered"]]
    altered = [r for r in recs if r["altered"]]
    cost = sum(r["cost_usd"] for r in recs)
    s = {"documents": len(recs),
         "no_answer": sum(not r["answered"] for r in recs),
         "clean_confirmed": _rate(sum(r["confirmed"] for r in clean), len(clean)),
         "altered_confirmed": _rate(sum(r["confirmed"] for r in altered), len(altered)),
         "altered_reported": _rate(sum(r["reported"] for r in altered), len(altered)),
         "altered_located": _rate(sum(r["located"] for r in altered), len(altered)),
         "clean_reported": _rate(sum(r["reported"] for r in clean), len(clean)),
         "reading_exact": _rate(sum(r["reading_exact"] for r in recs), len(recs)),
         "cost_usd": round(cost, 4),
         "cost_per_document_usd": round(cost / len(recs), 4) if recs else 0.0}
    for label, key in (("clean confirmed", "clean_confirmed"),
                       ("altered confirmed (want 0)", "altered_confirmed"),
                       ("altered reported", "altered_reported"),
                       ("altered located (a failing rule named)", "altered_located"),
                       ("clean reported (want 0)", "clean_reported"),
                       ("reading exact", "reading_exact")):
        print(f"{label:40}: {s[key]['k']} of {s[key]['n']}")
    print(f"{'no answer':40}: {s['no_answer']}   cost ${cost:.3f} "
          f"(${s['cost_per_document_usd']:.4f} per receipt)")
    (results.parent / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    return s


def run(manifest_path: str, condition: str, out_dir: str, *, limit: int | None = None,
        cap_usd: float = 2.0, workers: int = 4) -> dict[str, Any]:
    from probity.openrouter import OpenRouterClient, build_panel

    docs = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["documents"]
    if limit:
        docs = docs[:limit]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = out / "outcomes.jsonl"
    done = ({json.loads(l)["doc_id"] for l in results.read_text().splitlines() if l.strip()}
            if results.exists() else set())
    todo = [d for d in docs if d["doc_id"] not in done]
    spec = FormSpec.load(SPEC_PATH)
    client, models = None, {}
    if condition != "ocr_rules":
        client = OpenRouterClient(cap_usd=cap_usd, cache_dir=str(out / ".cache"),
                                  ledger_path=str(out / ".cache" / "spend_ledger.jsonl"))
        panel = build_panel([("first", FIRST, None), ("second", SECOND, None)])
        models = {FIRST: panel[0], SECOND: panel[1]}
    fn = CONDITIONS[condition]

    def one(doc):
        truth = json.loads(Path(doc["truth"]).read_text(encoding="utf-8"))
        try:
            return fn(doc, truth, spec, client, models, out)
        except Exception as exc:  # noqa: BLE001 - the receipt stays in the denominator
            return record(doc, truth, spec, confirmed=False, reported=False, rules_named=[],
                          form=None, answered=False, note=f"{type(exc).__name__}: {exc}")

    with results.open("a", encoding="utf-8") as fh, \
            ThreadPoolExecutor(max_workers=1 if condition == "ocr_rules" else workers) as pool:
        for n, job in enumerate(as_completed([pool.submit(one, d) for d in todo]), start=1):
            rec = job.result()
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            verdict = "confirmed" if rec["confirmed"] else "reported" if rec["reported"] else "unresolved"
            print(f"[{n}/{len(todo)}] {rec['doc_id']:32} {verdict:10} "
                  f"named {str(rec['rules_named'])[:44]}")
    return summarise(results)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--condition", required=True, choices=list(CONDITIONS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--cap-usd", type=float, default=2.0)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    run(args.manifest, args.condition, args.out, limit=args.limit, cap_usd=args.cap_usd,
        workers=args.workers)


if __name__ == "__main__":
    main()
