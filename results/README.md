# Results on disk

| folder | what it holds | written up in |
|---|---|---|
| [`sealed/`](sealed/) | the evaluation on documents never seen in development: 120 statements and 100 receipts | [docs/RESULTS.md](../docs/RESULTS.md) |
| [`development/`](development/) | the 20 statements the method was built on, and the who-decides experiment on 191 digital statements | [docs/DEVELOPMENT_SAMPLE.md](../docs/DEVELOPMENT_SAMPLE.md) |

## `sealed/`

```bash
python results/sealed/tables.py      # every table of docs/RESULTS.md, with intervals
```

| path | condition | contents |
|---|---|---|
| `statements/manifest.json` | | the 120 test statements: source, group, scan tier, the alteration made, the rows expected to fail, a checksum of the scan |
| `statements/probity/` | Probity | `outcomes.jsonl`, `summary.json`, `reports/` (one report per statement) |
| `statements/gemini_alone/` | Gemini reads, checks and decides | `outcomes.jsonl`, `summary.json` |
| `statements/qwen_alone/` | Qwen reads, checks and decides, on `subset_60.json` | the same |
| `statements/gemini_with_interpreter/` | Gemini with a Python interpreter | the same |
| `statements/ocr_rules/` | conventional OCR and the same rules | the same |
| `statements/factorial_gemini_rereads_itself/` | code decides, the first reader re-reads its own pages, on `subset_40.json` | the same |
| `statements/factorial_qwen_first_gemini_second/` | code decides, the two models in the reverse order, on `subset_40.json` | the same |
| `statements/gemini_alone_paraphrase_b/`, `_c/` | Gemini alone under two rewordings of the instructions, on `subset_30.json` | the same |
| `statements/probity_replicate_1/`, `_2/` | Probity again from scratch, on `subset_30.json` | the same |
| `statements/reader_agreement.json` | | cell-by-cell comparison of the two models' first transcriptions with the answer key |
| `receipts/manifest.json` | | the 100 test receipts: source split, group, the alteration made |
| `receipts/probity/` … `receipts/ocr_rules/` | the five conditions on receipts | `outcomes.jsonl`, `summary.json`; `reports/` for Probity |

The scanned documents themselves are not stored here. They are rebuilt from the public
sources by the commands in [docs/RESULTS.md](../docs/RESULTS.md#9-reproducing), and the
checksums in the manifests identify the files that were used.

### Reading an outcome line

**Probity, the factorial cells, the replicates and OCR:** `group`, `tier`, `altered`,
`detectable`, `expected_rows` (the rows that should be named), `conclusion`,
`conclusion_reason`, `rows_failing` (rows on which a rule still fails at the end),
`rows_corrected`, `amounts_and_dates_exact`, `period_dates_exact`, `descriptions_wrong`,
`second_reader_calls`, `cost_usd`, `seconds`.

**A model deciding alone:** three blocks, `one_pass` (first answer), `self_check` (the
re-examined answer) and `final` (re-examined where there is one, otherwise the first).
Each has `answered`, `no_answer_reason`, `certified` (it said the statement is
consistent), `rows_named`, `named_exactly`, `target_named`, `amounts_exact`.

**Receipts:** `altered`, `expected_rules`, `answered`, `confirmed`, `reported`,
`rules_named`, `located`, `reading_exact`, `corrections`, `cost_usd`, `note`.

Rows are numbered from 0. The statements print their own numbers from 1.

## `development/`

| folder | condition | contents |
|---|---|---|
| `probity_sample_a/`, `probity_sample_b/` | Probity, two independent samples of model replies | `outcomes.jsonl`, `summary.json`, `reports/` |
| `no_second_reader/` | the first reader re-reading its own pages | the same |
| `gemini_alone/`, `qwen_alone/` | each model reads, checks and decides | `outcomes.jsonl`, `summary.json`, `answers/` |
| `decider/` | the same perfect reading judged three ways, 191 digital statements | `summary.json`, `decider.jsonl` |
| `corpus/` | where the documents come from | `source_audit.json`, `build_manifest.json`, `sample_20.json` |
| `answer_keys/` | the ledger each of the 20 documents should be read as | one `.json` per document |
| `second_reader_probe/` | the single-document probe used to choose the second reader | two logs |
| `ledgers/` | one line per paid model request | `.jsonl` |

Inside these `.jsonl` files the document ids are the corpus builder's: `-scan-repaired`
is a clean document and `-scan-tampered` an altered one. Every outcome file in this
folder was produced by replaying stored replies, so its `cost_usd` and `seconds` are
replay figures; the paid requests are in `ledgers/`.
