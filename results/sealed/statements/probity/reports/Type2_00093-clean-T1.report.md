# Verification report: Type2_00093-clean-T1

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 3 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 156 |
| Rule checks passed | 315 of 315 |
| Rows corrected | 3 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0436 |
| Document SHA-256 | `85aa28b5d79faef6` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 38 | 2 | credit | 416,911.73 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 38 | 2 | debit | (blank) | 416,911.73 | DATE_ORDER, ROW_BAL | second reader |
| 106 | 4 | credit | (blank) | 5,415,767.48 | DATE_ORDER, ROW_BAL | second reader |
| 106 | 4 | debit | 5,415,767.48 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 128 | 5 | debit | 17,720,114.84 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 156 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 156 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
