# Verification report: Type2_00100-clean-T1

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 3 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 166 |
| Rule checks passed | 335 of 335 |
| Rows corrected | 3 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0435 |
| Document SHA-256 | `c79a8329810d245c` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 31 | 2 | credit | (blank) | 85,612.32 | DATE_ORDER, ROW_BAL | second reader |
| 31 | 2 | debit | 85,612.32 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 100 | 4 | credit | 6,351,967.36 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 100 | 4 | debit | (blank) | 6,351,967.36 | DATE_ORDER, ROW_BAL | second reader |
| 146 | 5 | credit | 651,614.01 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 146 | 5 | debit | (blank) | 651,614.01 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 166 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 166 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
