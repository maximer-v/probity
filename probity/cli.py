"""Command line: verify one document, render its report, or show the machine.

    probity verify statement.pdf --spec examples/specs/agami_type2.yaml
    probity verify statement.pdf --spec ... --explain --certificate out.json
    probity verify photo.jpg --spec ... --model google/gemini-3.1-flash-lite
    probity verify page1.png page2.png --spec ... --model ...
    probity verify scan.pdf --spec ... --model M1 --second-model M2 --report report.md
    probity report cert.json
    probity machine --format mermaid
    probity specs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _verify(args: argparse.Namespace) -> int:
    from . import Document, DocumentSpec, Pipeline, default_proposers

    try:
        spec = DocumentSpec.load(args.spec)
    except Exception as exc:
        print(f"cannot load the spec: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if args.second_model and args.second_model == args.model:
        print("--second-model must be a different model from --model: the same model "
              "reading a page twice is not a second opinion", file=sys.stderr)
        return 2
    proposers = default_proposers()
    if args.second_model and not args.model:
        print("--second-model needs --model: it re-reads pages the first model read",
              file=sys.stderr)
        return 2
    if args.model:
        from . import vlm_proposer
        try:
            reader = vlm_proposer(args.model, cap_usd=args.max_usd,
                                  cache_dir=args.cache_dir)
            proposers["llm_small"] = reader
            if args.second_model:
                proposers["checker"] = vlm_proposer(
                    args.second_model, tier="checker", client=reader.client)
        except Exception as exc:
            print(f"model tier unavailable: {exc}", file=sys.stderr)
            return 2

    first, source = args.pdf[0], str(args.pdf[0])
    if len(args.pdf) > 1:
        # Several files are the pages of one document, in the order given.
        from .images import images_to_pdf, is_image
        if not all(is_image(p) for p in args.pdf):
            print("several files are accepted only when every one is an image "
                  "(one page each)", file=sys.stderr)
            return 2
        try:
            source = images_to_pdf(args.pdf)
        except Exception as exc:
            print(f"cannot read the images: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2

    result = Pipeline(spec, proposers, max_usd=args.max_usd).run(
        Document(doc_id=first.stem, pdf_path=source))

    if args.explain:
        print(result.trace.explain())
        print()
    print(result.certificate.summary())

    if args.report:
        from .report import render_report
        Path(args.report).write_text(render_report(result.certificate.to_json()),
                                     encoding="utf-8")
        print(f"\nreport      -> {args.report}")
    if args.certificate:
        Path(args.certificate).write_text(result.certificate.dumps(), encoding="utf-8")
        print(f"\ncertificate -> {args.certificate}")
    if args.trace:
        result.trace.write(args.trace)
        print(f"trace       -> {args.trace}")
    if args.csv and result.statement:
        _write_csv(result, args.csv)
        print(f"rows        -> {args.csv}")

    return exit_code(result)


def exit_code(result) -> int:
    """0 confirmed, 1 not confirmed (inconsistent or unresolved), 2 could not be processed.

    Taken from the conclusion, not from the machine's final state: a spec with a
    permissive acceptance policy can reach ACCEPT while a rule fails, and that is not a
    confirmed reading.
    """
    if str(result.final_state) not in {"ACCEPT", "HUMAN_REVIEW"}:
        return 2
    return 0 if result.conclusion == "CONFIRMED" else 1


def _report(args: argparse.Namespace) -> int:
    from .report import render_report

    text = render_report(json.loads(Path(args.certificate).read_text(encoding="utf-8")))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"report -> {args.out}")
    else:
        print(text)
    return 0


def _write_csv(result, path: str) -> None:
    """Export rows. Text cells are escaped against formula injection; amounts are numeric.

    The escaping goes on text only. Prefixing an amount with an apostrophe would turn
    every negative number into a string in the spreadsheet, which is how a
    well-intentioned fix becomes a data error.
    """
    import csv

    def escape(text: str) -> str:
        if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "'" + text
        return text

    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "description", "debit", "credit", "balance", "status"])
        for row in result.statement.rows:
            def money(f):
                return str(f.value) if f.value is not None else ""
            w.writerow([
                row.date.value.isoformat() if row.date.value else "",
                escape(str(row.description.value or "")),
                money(row.debit), money(row.credit), money(row.balance),
                row.balance.status,
            ])


def _machine(args: argparse.Namespace) -> int:
    from .export import to_dot, to_markdown_table, to_mermaid, to_xstate
    from .machine import build_machine
    from .pipeline import build_guards

    m = build_machine(build_guards())
    if args.format == "mermaid":
        print(to_mermaid())
    elif args.format == "xstate":
        print(json.dumps(to_xstate(m), indent=2))
    elif args.format == "dot":
        print(to_dot())
    else:
        print(to_markdown_table(m))
    return 0


def _specs(args: argparse.Namespace) -> int:
    from .spec import DocumentSpec

    root = Path(args.dir)
    for path in sorted(root.glob("*.yaml")):
        try:
            spec = DocumentSpec.load(path)
        except Exception as exc:
            print(f"{path.name:22s} INVALID: {exc}")
            continue
        print(f"{path.name:22s} {spec.doc_type:34s} {spec.locale_name} "
              f"{spec.currency_default} {spec.verification_level():14s} "
              f"{spec.fingerprint()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="probity", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)

    v = sub.add_parser("verify", help="verify one document against a spec")
    v.add_argument("pdf", type=Path, nargs="+", metavar="FILE",
                   help="a PDF, an image (PNG, JPEG, TIFF, WebP), or several images "
                        "that are the pages of one document")
    v.add_argument("--spec", required=True)
    v.add_argument("--explain", action="store_true", help="print the full decision log")
    v.add_argument("--certificate", help="write the certificate here")
    v.add_argument("--trace", help="write the JSONL trace here")
    v.add_argument("--csv", help="export the rows here")
    v.add_argument("--model", default=None,
                   help="OpenRouter vision model to read scanned pages with, e.g. "
                        "google/gemini-3.1-flash-lite (needs OPENROUTER_API_KEY)")
    v.add_argument("--second-model", default=None,
                   help="a different vision model, asked to re-read only the pages "
                        "where a rule failed, e.g. qwen/qwen3.5-flash-02-23")
    v.add_argument("--report", help="write the human-readable report (Markdown) here")
    v.add_argument("--cache-dir", default=".probity-cache",
                   help="where model replies are cached, keyed by content")
    v.add_argument("--max-usd", type=float, default=0.50,
                   help="spend cap for all model calls on this document")
    v.set_defaults(fn=_verify)

    r = sub.add_parser("report", help="render a stored certificate as a readable report")
    r.add_argument("certificate")
    r.add_argument("--out", help="write here instead of printing")
    r.set_defaults(fn=_report)

    m = sub.add_parser("machine", help="print the state machine")
    m.add_argument("--format", choices=["mermaid", "xstate", "dot", "table"],
                   default="mermaid")
    m.set_defaults(fn=_machine)

    s = sub.add_parser("specs", help="list document specs in a directory")
    s.add_argument("--dir", default="examples/specs")
    s.set_defaults(fn=_specs)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
