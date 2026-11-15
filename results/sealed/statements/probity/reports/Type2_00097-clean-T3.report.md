# Verification report: Type2_00097-clean-T3

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 4 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 160 |
| Rule checks passed | 323 of 323 |
| Rows corrected | 4 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0449 |
| Document SHA-256 | `2afe959f3fdbe022` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 14 | 1 | balance | 9,971,782.50 | 9,971,782.54 | DATE_ORDER, ROW_BAL | second reader |
| 26 | 2 | balance | 1,777,912.48 | 1,777,912.97 | DATE_ORDER, ROW_BAL | second reader |
| 108 | 4 | credit | 219,056.75 | 219,056.36 | DATE_ORDER, ROW_BAL | second reader |
| 118 | 4 | debit | 2,762,105.84 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 160 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 160 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
