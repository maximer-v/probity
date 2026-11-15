# Changelog

## 0.2.0

- **First reader**: a low-cost vision model transcribes each page, one page per request,
  returning the characters as printed. Code parses them to exact amounts and dates.
- **Rules**: `ROW_BAL`, `GLOBAL_BAL`, `LAST_ROW_EQ_CLOSING`, `DATE_ORDER`, `NO_DUP_ROW`,
  `PAGE_SUBTOTAL`, `COUNT`, with exact integer equality and located failures.
- **Second reader**: a different model transcribes only the pages on which a rule
  failed, without seeing the first transcription. Code compares the two under six
  guards (docs/METHOD.md) and re-runs the rule.
- **Third reading**: when the two models agree and the rule still fails, the first
  model transcribes the page again at a higher resolution before the document is held
  responsible, so a misreading both models share is corrected and not reported.
- **Conclusions**: `CONFIRMED`, `DOCUMENT_INCONSISTENT` at named rows, or `UNRESOLVED`.
- **Corrections record**: every changed value with both readings, both model names, the
  passing rules and the method.
- **State machine**: 10 states and 16 transitions as data, with named guards, exported
  to Mermaid, XState JSON and DOT.
- **Input**: PDF, PNG, JPEG, TIFF, WebP, BMP, GIF; several images as the pages of one
  document; phone-photo rotation applied.
- **Output**: readable report, JSON certificate, prose decision log, JSONL trace, CSV.
- **Command line**: `probity verify | report | machine | specs`.
- **Other document types in YAML**: a spec of `kind: form` declares fields, a table and
  rules as formulas; `probity/forms.py` reads, checks, re-reads and concludes the same
  way. `examples/specs/receipt_cord.yaml` is the receipt type used in the evaluation.
- **Evaluation**: a protocol committed before the test set existed
  (`benchmark/protocol/PROTOCOL.md`), run once on the code tagged `sealed-run-1`: 120
  scanned statements and 100 real receipts, against each model alone, a model with a
  Python interpreter, and conventional OCR with the same rules. `docs/RESULTS.md` is
  the record and `results/sealed/` holds the scored outcomes.
- **Development sample**: the 20 statements the method was built on and the experiment
  on who decides, in `docs/DEVELOPMENT_SAMPLE.md` and `results/development/`.
- 163 tests.
