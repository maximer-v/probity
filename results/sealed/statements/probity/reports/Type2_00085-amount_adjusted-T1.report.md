# Verification report: Type2_00085-amount_adjusted-T1

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 16 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 157 |
| Rule checks passed | 317 of 317 |
| Rows corrected | 16 |
| Calls to `google/gemini-3.1-flash-lite` | 5 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0353 |
| Document SHA-256 | `d2db166dd6f16dfa` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 0 | 1 | debit | (blank) | 48,673.72 | DATE_ORDER, ROW_BAL | second reader |
| 1 | 1 | credit | (blank) | 103,405.77 | DATE_ORDER, ROW_BAL | second reader |
| 2 | 1 | credit | (blank) | 286,607.51 | DATE_ORDER, ROW_BAL | second reader |
| 3 | 1 | debit | (blank) | 250,475.81 | DATE_ORDER, ROW_BAL | second reader |
| 4 | 1 | debit | (blank) | 168,882.90 | DATE_ORDER, ROW_BAL | second reader |
| 5 | 1 | debit | (blank) | 3,042.61 | DATE_ORDER, ROW_BAL | second reader |
| 7 | 1 | debit | (blank) | 80.54 | DATE_ORDER, ROW_BAL | second reader |
| 8 | 1 | debit | (blank) | 454.70 | DATE_ORDER, ROW_BAL | second reader |
| 9 | 1 | debit | (blank) | 289,318.86 | DATE_ORDER, ROW_BAL | second reader |
| 10 | 1 | debit | (blank) | 300,296.58 | DATE_ORDER, ROW_BAL | second reader |
| 11 | 1 | credit | (blank) | 185,415.83 | DATE_ORDER, ROW_BAL | second reader |
| 12 | 1 | debit | (blank) | 6,122.53 | DATE_ORDER, ROW_BAL | second reader |
| 13 | 1 | credit | (blank) | 9,480.20 | DATE_ORDER, ROW_BAL | second reader |
| 14 | 1 | debit | (blank) | 131,521.94 | DATE_ORDER, ROW_BAL | second reader |
| 15 | 1 | credit | (blank) | 20,819.97 | DATE_ORDER, ROW_BAL | second reader |
| 16 | 1 | credit | (blank) | 16,785.88 | DATE_ORDER, ROW_BAL | second reader |

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
