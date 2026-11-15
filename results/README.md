# Results on disk

The scored record behind [docs/RESULTS.md](../docs/RESULTS.md).

| folder | condition | contents |
|---|---|---|
| `probity_sample_a/` | Probity, first sample of model replies | `outcomes.jsonl`, `summary.json`, `reports/` (one report per document) |
| `probity_sample_b/` | Probity, a second, independent sample of model replies | the same |
| `no_second_reader/` | the first reader re-reading its own pages, same guards | the same |
| `gemini_alone/` | `google/gemini-3.1-flash-lite` reads, checks and decides | `outcomes.jsonl`, `summary.json`, `answers/` (the model's raw first and re-examined answers) |
| `qwen_alone/` | `qwen/qwen3.5-flash-02-23` reads, checks and decides | the same |
| `decider/` | same reading, three deciders, 191 digital statements | `summary.json`, `decider.jsonl` (one line per document with each decider's verdict) |
| `corpus/` | where the documents come from | `source_audit.json` (the 200 published digital statements), `build_manifest.json` (the 191 built and the 9 not built, with reasons), `sample_20.json` (the 20 used here) |
| `answer_keys/` | the ledger each of the 20 documents should be read as, and the alteration if any | one `.json` per document |
| `second_reader_probe/` | the single-document probe used to choose the second reader | two logs |
| `ledgers/` | one line per paid model request: model, purpose, tokens, cost, latency | `.jsonl` |

## What can be recomputed from here, and what cannot

- **Every count in the tables of RESULTS.md sections 4.1 to 4.6** can be recomputed from
  the `outcomes.jsonl` and `decider.jsonl` files, which hold one scored line per
  document.
- **The scores themselves** (whether a final transcription matches its answer key)
  were computed when each run was made. The answer keys are here; the full
  transcriptions are not, because the certificates that hold them are about 400 kB per
  document. Re-scoring from scratch means re-running the experiment, or replaying it
  from a cache of model replies.
- **Costs** come from the ledgers. The ledgers of the no-second-reader run and of the
  decider run are not included; RESULTS.md section 4.8 says which figures are estimates.
- **The corpus figures** come from `corpus/`.

## Reading the files

**Document ids.** `Type1_00004-altered` is the fourth statement of layout Type 1.
Inside the `.jsonl` files the ids are the corpus builder's: `-scan-repaired` is a clean
document and `-scan-tampered` an altered one.

**`outcomes.jsonl`**, one line per document.

- Probity and `no_second_reader`: `conclusion`, `conclusion_reason`, `rows_failing`
  (rows on which a rule still fails at the end), `rows_corrected`, `corrected_by`,
  `altered_row` (the answer; `null` for a clean document), `amounts_and_dates_exact`
  (the "ledger exact" measure), `period_dates_exact`, `descriptions_wrong`,
  `second_reader_calls`, `cost_usd`, `seconds`.
- Model alone: three blocks, `one_pass` (first answer), `self_check` (re-examined
  answer only) and `final` (re-examined where there is one, otherwise the first). Each
  has `answered`, `no_answer_reason`, `certified`, `rows_named`, `named_exactly`,
  `target_named`, `amounts_exact` (ledger exact), `period_dates_exact`.

**Rows are numbered from 0.** The statements print their own numbers from 1.

**Costs and times in the outcome files.** `cost_usd` is what that particular run paid.
Every outcome file here was produced by replaying cached replies through the final
code, so `cost_usd` is zero or partial and `seconds` is replay time. The paid requests
are in `ledgers/`: `sample_b_both_readers.jsonl` and `sample_b_third_readings.jsonl`
together are one complete Probity run and are the source of the cost and time figures.

**The probe logs.** `probe_1.log` shows zero rows for three models. Those requests were
rejected by the provider for their parameters and returned nothing; they are not
readings. One of them, Qwen, succeeded in `probe_2.log` once the request was adjusted.

## Recomputing a headline number

```python
import json
rows = [json.loads(l) for l in open("results/probity_sample_b/outcomes.jsonl")]
altered = [r for r in rows if r["altered"]]
print(sum(r["conclusion"] == "CONFIRMED" for r in altered), "of", len(altered))
print(sum(r["conclusion"] == "DOCUMENT_INCONSISTENT"
          and r["rows_failing"] == [r["altered_row"]] for r in altered), "of", len(altered))
```
