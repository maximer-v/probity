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
- **Experiments**: `benchmark/run_scanned.py` (the method, with or without the second
  reader), `benchmark/run_llm_alone.py` (a model doing the whole job alone),
  `benchmark/ablate_decider.py` (same reading, three deciders), over statements built
  by `benchmark/external/agami_patch.py` and `rasterise.py`.
- **Results**: `results/` holds the scored outcomes, reports, raw model answers and cost
  ledgers; `docs/RESULTS.md` is the experimental record.
- 143 tests.
