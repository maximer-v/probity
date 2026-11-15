# Reading the logs

A run can produce four artefacts. On the command line each is written only if its
option is given (`--explain` prints to the terminal); the benchmark runners write all
four for every document. They answer different questions and are produced whether the
document is confirmed or not.

| file | for | holds |
|---|---|---|
| `<doc>.explain.txt` | a human, first | the run as prose: each guard asked, its answer, and the evidence |
| `<doc>.trace.jsonl` | machines and diffs | one JSON object per event, replayable |
| `<doc>.certificate.json` | the consumer | what was checked, every value's provenance and box, what is *not* claimed |
| `<doc>.report.md` | a reviewer | the conclusion, the corrections, each inconsistent row with both readings (`probity verify --report`, or `probity report certificate.json`) |

The design rule is that **a failure must never require re-running the document to
understand**. If a statement is not confirmed, the arithmetic that failed, the
guards that were consulted and declined, the budget that ran out and the hash of every
model call are already on disk.

## The prose log

From the run recorded in
[`examples/scanned/outputs/altered_statement.explain.txt`](../examples/scanned/outputs/altered_statement.explain.txt),
abridged. The prices are those of the original requests; the copy in the repository was
regenerated from cached replies and shows `cached` in their place.

```
CLASSIFY
  ask  has_text_layer        no   <- no usable text layer; OCR will be required
  note starting at llm_small: the text-layer tiers cannot apply to a scan

EXTRACT
  call llm:google/gemini-3.1-flash-lite (transcribe) $0.00385      (x6, one per page)
  read llm_small proposed 167 rows, 0 unreadable cells

VERIFY
  chk  9 invariant failure(s):
  chk    [ROW_BAL/MISMATCH] row:69: row 69: 807096948 + -287011504 = 520085444,
  chk      but the balance column reads 520085440 (off by -4)
  chk    [ROW_BAL/MISMATCH] row:127: row 127: 451886831 + -2382371 = 449504460,
  chk      but the balance column reads 442504460 (off by -7000000)
  ask  accepts               no   <- 9 invariant failure(s): MISMATCH
  ask  repairable            yes  <- row:69 has 2 repair attempt(s) left
  go   VERIFY -> REPAIR (via repairable)

REPAIR
  note repair request for row:69
  call llm:qwen/qwen3.5-flash-02-23 (second_opinion) $0.00299
  fix  row:69: second_opinion -> accepted
  ask  repair_proposed       yes  <- the second reading has row(s) [69, 73, 77, 78]
                                     differently, and with it the rule passes and no
                                     other check fails (9 failure(s) before, 4 after)
  go   REPAIR -> GROUND (via repair_proposed)
```

Amounts in this log are integer minor units, so `442504460` is 4,425,044.60. The report
prints them as figures.

Three things in that log are deliberate.

**The arithmetic, not the verdict.** The line for row 127 is enough to act on.
"Validation failed" is not.

**Guards that answered no.** Each `ask` line records a question the machine put and the
reason for the answer. Without them, "went to a person" is unexplainable.

**Every model call, with its purpose and cost.** A `transcribe` call is the first
reader; a `second_opinion` call is the second. `cached` in place of a price means the
reply came from the content-keyed cache and nothing was spent.

## Corrections and second looks

When a second reader is configured, the prose log shows each look and what came of it.
Page 5 of the altered example yields three findings, one of each kind:

```
REPAIR
  note repair request for row:127
  call llm:qwen/qwen3.5-flash-02-23 (second_opinion) $0.00314
  call llm:google/gemini-3.1-flash-lite (reread) $0.00756
  fix  row:127: second_opinion -> both readers agree, the document is inconsistent here
  note repair request for row:135
  fix  row:135: second_opinion -> accepted
  ask  repair_proposed   yes  <- the second reading has row(s) [135] differently, and
                                 with it the rule passes and no other check fails
                                 (4 failure(s) before, 3 after)
...
REPAIR
  note repair request for row:148
  fix  row:148: second_opinion -> accepted
  ask  repair_proposed   yes  <- two readers had agreed on row 148, but a third reading
                                 at higher resolution has row(s) [148] differently, and
                                 with it the rule passes and no other check fails. The
                                 two earlier readings shared a misreading
```

- **Row 135:** the second reader differed and its reading tied. Corrected.
- **Row 127:** the two models agreed, so the page was read a third time (`reread`); it
  agreed too. Reported as inconsistent. This is the alteration.
- **Row 148:** the two models agreed, and the third reading did not: it had the amount
  in the other column, and with that the row tied. Corrected, and recorded as a
  `third_reading` correction.

The certificate carries the same information as data.

`corrections`: one entry per changed value.

| key | meaning |
|---|---|
| `row`, `page`, `field` | where; rows count from zero |
| `first_reading`, `corrected` | the characters each reader returned |
| `first_reader`, `second_reader` | the model names |
| `confirmed_by` | the rules that pass on this row with the new value |
| `method` | `second_reader`; `third_reading` when both models had agreed and the tie-break corrected the row; `same_reader_reread` when no second reader is configured |

`second_opinions`: one entry per look, whatever its result.

| key | meaning |
|---|---|
| `finding` | `CORRECTED`, `DOCUMENT_INCONSISTENT`, `DISPUTED`, `UNALIGNED`, `UNAVAILABLE`, or `REPEATED` (no second reader, and the first reader read it the same way again) |
| `region`, `page` | the failing row that prompted the look |
| `rows` | the row and its neighbours as each reader transcribed them, with `agree` |
| `operands` | for `DOCUMENT_INCONSISTENT`: the figures the finding was made on |
| `reason` | one sentence |

`outcome.conclusion` and `outcome.conclusion_reason` summarise the document, and
`outcome.inconsistent_rows` lists the rows whose "both readers agree" finding still
stands on the final figures.

## The event stream

`trace.jsonl` is one object per line. The kinds:

| kind | written when | key fields |
|---|---|---|
| `run_start` | once | spec fingerprint, framework version, tier ladder |
| `state_enter` | each state | `state` |
| `guard` | each guard asked | `guard`, `answer`, `why`, `evidence` |
| `transition` | each move | `from`, `to`, `via`, `guards_asked` |
| `extraction` | a proposer returns | `tier`, `rows`, `parse_error_codes`, `region` |
| `grounding` | after GROUND | per-code counts and every failure |
| `invariant` | after VERIFY | the full report, with operands |
| `repair_attempt` | each strategy | `strategy`, `outcome`, candidates and verdicts |
| `tier_change` | on escalation | `old_tier`, `new_tier`, `reason` |
| `model_call` | each call | model, provider, params, prompt/output SHA-256, tokens, cost |
| `budget` | on a stop | what ran out |
| `run_end` | once | final state, total cost, call count |

### Failure vocabulary

Codes are fixed so logs can be counted, not just read.

*Amount parsing* (`probity/money.py`): `BAD_THOUSANDS_GROUPING`, `TOO_MANY_DECIMALS`,
`MULTIPLE_DECIMAL_SEPARATORS`, `UNEXPECTED_CHARS`, `NO_DIGITS`,
`THOUSANDS_SEP_IN_FRACTION`, `NON_DIGIT_INTEGER_PART`, `TRAILING_MINUS_NOT_ALLOWED`.

*Dates* (`probity/dates.py`): `FORMAT_MISMATCH`, `IMPOSSIBLE_DATE`, `UNKNOWN_MONTH_NAME`,
`EMPTY`.

*Invariants* (`probity/invariants.py`): `MISMATCH`, `UNREADABLE_OPERAND`,
`NOT_APPLICABLE`, `OUT_OF_ORDER`, `OUT_OF_PERIOD`, `COUNT_MISMATCH`, `DUPLICATE_ROW`,
`BOTH_SIDES_PRESENT`.

*Grounding* (`probity/grounding.py`): `GROUNDED`, `GROUNDED_NEARBY`, `NO_BBOX`,
`NOT_ON_PAGE`, `WRONG_PLACE`, `BOX_EMPTY`, `BOX_SAYS_OTHERWISE`, `NO_SOURCE`, `SKIPPED`.

`BOX_SAYS_OTHERWISE` and `NOT_ON_PAGE` are the ones to watch: they are the fingerprint of
a value that was produced rather than read.

## Privacy

A bank statement is personal data, and every artefact here carries some of it. Be
precise about which:

- **The trace** stores model prompts and outputs as SHA-256 hashes, not text. It does
  quote the transcribed figures of rows that were given a second look.
- **The certificate, the report and the CSV** contain the transcribed statement:
  amounts, dates, descriptions and the account number.
- **The model cache** (`--cache-dir`) stores full model replies, which are
  transcriptions of the pages.
- **Rendered page images** are written to the system temp directory and are not removed.

API keys are stripped from every log path, and neither the cache nor the spend ledger
receives one. Treat the output and cache directories as you would the documents.

## Comparing two runs

```python
from probity.trace import diff_traces

print(a.trace.replay_hash() == b.trace.replay_hash())
print(diff_traces(a.trace, b.trace))     # the first event where two runs parted
```

The hash covers the deterministic fields of the trace; timestamps and latencies are
excluded. With the same cached model replies, two runs of the same document take the
same path. Without the cache they may not: the models are not guaranteed to return the
same transcription twice. The trace does not hold the request payloads or the page
images, so it documents a run and cannot by itself re-execute one.

## The benchmark's logs

`python -m benchmark.run_scanned` writes, under its `--out` directory, the four files
above for every document, plus:

- `outcomes.jsonl`: one scored line per document, with the conclusion, the rows left
  failing, the rows corrected, field accuracy against the answer key, cost and time;
- `summary.json`: the totals printed at the end of the run.
