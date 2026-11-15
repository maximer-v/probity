"""Same reading, different decider.

Is a verdict computed by code worth anything once the reading is already correct? This
isolates that question. Every mode is handed the same reading of each document, taken
from the PDF's text layer and exact on every row, so no mode reads a page and reading is
not a variable. They differ only in who decides whether the document reconciles:

* **machine** -- the rules compute the verdict. What the framework does, and the control.
  Costs nothing.
* **shown** -- the rules are computed and their failures are handed to the model in
  full, naming the row and the amount it is off by. The model issues the verdict.
* **unaided** -- the model gets the same exact reading and no computed checks, and must
  decide for itself.

"unaided" removes every excuse: perfect input, one question, no tools to misuse, no
pages to misread.

    python -m benchmark.ablate_decider --manifest <built digital manifest> \\
        --model google/gemini-3.1-flash-lite
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from probity import Document, DocumentSpec, Pipeline, default_proposers
from probity.openrouter import (OUTPUT_CEILING, BudgetExhausted, ModelSpec,
                                OpenRouterClient, build_panel, load_api_key)

from .convert import statement_to_reading
from .metrics import compare

MODES = ("machine", "shown", "unaided")

VERDICT_SCHEMA: dict[str, Any] = {
    "name": "reconciliation_verdict",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["reconciled", "reason"],
        "properties": {
            "reconciled": {
                "type": "boolean",
                "description": "true only if the statement's arithmetic is internally "
                               "consistent and you would certify it",
            },
            "reason": {"type": "string", "description": "one or two sentences"},
        },
    },
}

TASK = """You are deciding whether a bank statement's arithmetic is internally consistent.

The statement below has already been transcribed for you, exactly as printed, to the
minor unit. The transcription is not in question: do not consider misreading as a
possibility.

A statement reconciles when both of these hold, exactly, with no tolerance:

  * for every row, balance = previous balance + credit - debit
  * opening balance + all movements = closing balance

All amounts are given in integer minor units (so 1234 means 12.34). Set `reconciled` to
true only if you would certify this statement to a credit committee."""

SHOWN_NOTE = """These checks have already been run against the transcription by an exact
integer arithmetic engine. Its findings are authoritative and complete:"""

UNAIDED_NOTE = """No checks have been run. Decide for yourself."""


def reading_as_text(reading: dict[str, Any]) -> str:
    """The reading in a compact form, every row present, nothing summarised away."""
    head = reading.get("header", reading)
    lines = [
        f"opening_balance: {head.get('opening_balance')}",
        f"closing_balance: {head.get('closing_balance')}",
        f"rows: {len(reading.get('rows') or [])}",
        "",
        "index | date | debit | credit | balance",
    ]
    for i, r in enumerate(reading.get("rows") or []):
        lines.append(f"{i} | {r.get('date')} | {r.get('debit')} | "
                     f"{r.get('credit')} | {r.get('balance')}")
    return "\n".join(lines)


def failures_as_text(cert: dict[str, Any]) -> str:
    fails = cert["invariants"]["failures"]
    if not fails:
        return "No check failed. Every row's balance follows, and the closing balance agrees."
    out = []
    for f in fails:
        loc = f.get("location") or {}
        where = (f"row {loc['row_index']}" if loc.get("row_index") is not None
                 else "document")
        out.append(f"- [{f['invariant']}/{f['code']}] {where}: {f.get('message') or ''}")
    return "\n".join(out)


def run(manifest_path: str, *, limit: int | None = None,
        model_id: str = "google/gemini-3.1-flash-lite",
        cap_usd: float = 2.0, out_dir: str = "benchmark/results/decider") -> dict[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    docs = manifest["documents"]
    if limit:
        docs = docs[:limit]

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    client = OpenRouterClient(cache_dir=str(out / "cache"),
                              ledger_path=str(out / "spend_ledger.jsonl"),
                              cap_usd=cap_usd)
    ledger = client.ledger
    panel = build_panel([("decider", model_id, None)])
    model: ModelSpec = panel[0]

    specs: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []

    for i, d in enumerate(docs, start=1):
        spec = specs.setdefault(d["spec"], DocumentSpec.load(d["spec"]))
        truth = json.loads(Path(d["truth"]).read_text(encoding="utf-8"))
        should_accept = truth.get("inconsistency") is None

        # One reading, shared by every mode, so the only variable is the decider.
        result = Pipeline(spec, default_proposers()).run(
            Document(doc_id=d["doc_id"], pdf_path=d["document"]))
        reading = statement_to_reading(result.statement) if result.statement else {"rows": []}
        cert = result.certificate.to_json()
        n_rows_read = len(reading.get("rows") or [])
        # "Exact" means every amount, balance and date matches the answer key, not
        # merely that the right number of rows came back.
        reading_exact = compare(reading, truth, doc_id=d["doc_id"]).correct  # incl. period

        record = {
            "doc_id": d["doc_id"], "kind": d.get("kind"),
            "should_accept": should_accept,
            "rows_read": n_rows_read, "rows_printed": d["n_rows_ledger"],
            "reading_exact": reading_exact,
            "verdicts": {},
        }

        # The control: no model involved at all.
        record["verdicts"]["machine"] = {
            "reconciled": bool(result.accepted),
            "correct": bool(result.accepted) == should_accept,
            "cost_usd": 0.0, "reason": cert["invariants"].get("summary", ""),
        }

        for mode in ("shown", "unaided"):
            note = SHOWN_NOTE if mode == "shown" else UNAIDED_NOTE
            body = [TASK, "", note]
            if mode == "shown":
                body += [failures_as_text(cert)]
            body += ["", "TRANSCRIPTION", reading_as_text(reading)]
            prompt = "\n".join(body)
            try:
                t0 = time.perf_counter()
                resp = client.chat(model, [{"role": "user", "content": prompt}],
                                   json_schema=VERDICT_SCHEMA,
                                   max_tokens=OUTPUT_CEILING,
                                   purpose=f"decider:{mode}")
                elapsed = (time.perf_counter() - t0) * 1000
            except BudgetExhausted:
                record["verdicts"][mode] = {"error": "budget exhausted"}
                rows.append(record)
                _write(out, rows, manifest_path, model.model, ledger)
                return _summarise(rows, ledger, out)
            except Exception as exc:  # noqa: BLE001
                record["verdicts"][mode] = {"error": f"{type(exc).__name__}: {exc}"}
                continue

            truncated = (resp.finish_reason or "").lower() in {"length", "max_tokens"}
            # The same tolerant parser the framework's reader gets, and a verdict that
            # counts only if it is a real boolean: "false" must not become acceptance.
            from probity.proposers.vlm import _parse
            parsed = None if truncated else _parse(resp.text or "")
            said = (parsed.get("reconciled")
                    if parsed and isinstance(parsed.get("reconciled"), bool) else None)
            record["verdicts"][mode] = {
                "reconciled": said,
                "correct": (said == should_accept) if said is not None else None,
                "reason": (parsed or {}).get("reason", "")[:400],
                "truncated": truncated,
                "cost_usd": round(resp.cost_usd, 6),
                "latency_ms": round(elapsed, 1),
            }

        rows.append(record)
        line = "  ".join(
            f"{m}:{'ACCEPT' if record['verdicts'][m].get('reconciled') else 'refuse'}"
            f"{'' if record['verdicts'][m].get('correct') else '!'}"
            for m in MODES)
        print(f"  [{i}/{len(docs)}] {d['doc_id']:44s} "
              f"{'clean ' if should_accept else 'altered'} "
              f"rows {n_rows_read}/{d['n_rows_ledger']}  {line}")

    _write(out, rows, manifest_path, model.model, ledger)
    return _summarise(rows, ledger, out)


def _write(out: Path, rows: list[dict[str, Any]], manifest_path: str,
           model: str, ledger: Ledger) -> None:
    (out / "decider.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _summarise(rows: list[dict[str, Any]], ledger: Ledger, out: Path) -> dict[str, Any]:
    clean = [r for r in rows if r["should_accept"]]
    altered = [r for r in rows if not r["should_accept"]]
    per: dict[str, Any] = {}
    for mode in MODES:
        got = [r for r in rows if r["verdicts"].get(mode, {}).get("reconciled") is not None]
        acc = [r for r in got if r["verdicts"][mode]["reconciled"]]
        per[mode] = {
            "documents_judged": len(got),
            "clean_accepted": sum(1 for r in clean
                                  if r["verdicts"].get(mode, {}).get("reconciled")),
            "clean_total": len(clean),
            "altered_accepted": sum(1 for r in altered
                                   if r["verdicts"].get(mode, {}).get("reconciled")),
            "altered_total": len(altered),
            # The headline: of everything this decider certified, how much was wrong.
            "false_certification_rate": (
                round(100 * sum(1 for r in acc if not r["should_accept"]) / len(acc), 1)
                if acc else 0.0),
            "cost_usd": round(sum(r["verdicts"].get(mode, {}).get("cost_usd", 0.0)
                                  for r in rows), 4),
        }
    summary = {
        "experiment": "same reading, different decider",
        "note": ("Every mode is handed the framework's own text-layer reading, so no mode "
                 "reads a page and reading is not a variable. 'machine' is the control."),
        "n_documents": len(rows),
        "readings_exact": sum(1 for r in rows if r["reading_exact"]),
        "by_mode": per,
        "spend_usd": round(ledger.spent, 4),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--model", default="google/gemini-3.1-flash-lite")
    ap.add_argument("--cap-usd", type=float, default=2.0)
    ap.add_argument("--out", default="benchmark/results/decider")
    args = ap.parse_args()
    s = run(args.manifest, limit=args.limit, model_id=args.model,
            cap_usd=args.cap_usd, out_dir=args.out)
    print()
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
