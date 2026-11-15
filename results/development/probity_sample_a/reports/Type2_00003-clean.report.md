# Verification report: agami-Digital_Type2_00003-scan-repaired

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 2 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 163 |
| Rule checks passed | 329 of 329 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0000 |
| Document SHA-256 | `1bf0676a5c042b3a` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 151 | 5 | credit | 2,021,787.51 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 151 | 5 | debit | (blank) | 2,021,787.51 | DATE_ORDER, ROW_BAL | second reader |
| 155 | 5 | credit | (blank) | 6.12 | DATE_ORDER, ROW_BAL | second reader |
| 155 | 5 | debit | 6.12 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 163 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 163 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
