# Verification report: Type2_00087-clean-T1

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 3 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 157 |
| Rule checks passed | 317 of 317 |
| Rows corrected | 3 |
| Calls to `google/gemini-3.1-flash-lite` | 5 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0420 |
| Document SHA-256 | `e9b54380e134399b` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 25 | 2 | credit | 1,279,294.62 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 25 | 2 | debit | (blank) | 1,279,294.62 | DATE_ORDER, ROW_BAL | second reader |
| 81 | 3 | credit | (blank) | 322,467.08 | DATE_ORDER, ROW_BAL | second reader |
| 81 | 3 | debit | 322,467.08 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | credit | 1,402,234.03 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | debit | (blank) | 1,402,234.03 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 157 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 157 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
