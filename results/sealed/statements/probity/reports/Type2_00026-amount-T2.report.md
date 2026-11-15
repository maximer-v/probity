# Verification report: Type2_00026-amount-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:114.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 168 |
| Rule checks passed | 337 of 339 |
| Rows corrected | 33 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0398 |
| Document SHA-256 | `6c7a7cc9a0b164be` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 87 | 4 | debit | (blank) | 111,281.59 | DATE_ORDER, ROW_BAL | second reader |
| 88 | 4 | credit | (blank) | 10,987,611.36 | DATE_ORDER, ROW_BAL | second reader |
| 89 | 4 | debit | (blank) | 10,932,216.53 | DATE_ORDER, ROW_BAL | second reader |
| 90 | 4 | credit | (blank) | 35,836.00 | DATE_ORDER, ROW_BAL | second reader |
| 91 | 4 | debit | (blank) | 177,091.82 | DATE_ORDER, ROW_BAL | second reader |
| 92 | 4 | credit | (blank) | 2,894.47 | DATE_ORDER, ROW_BAL | second reader |
| 93 | 4 | credit | (blank) | 58,379.27 | DATE_ORDER, ROW_BAL | second reader |
| 94 | 4 | credit | (blank) | 27,111.48 | DATE_ORDER, ROW_BAL | second reader |
| 95 | 4 | credit | (blank) | 43,423.45 | DATE_ORDER, ROW_BAL | second reader |
| 96 | 4 | credit | (blank) | 26,125.79 | DATE_ORDER, ROW_BAL | second reader |
| 97 | 4 | debit | (blank) | 11,479.12 | DATE_ORDER, ROW_BAL | second reader |
| 98 | 4 | debit | (blank) | 142,038.23 | DATE_ORDER, ROW_BAL | second reader |
| 99 | 4 | credit | (blank) | 279,435.66 | DATE_ORDER, ROW_BAL | second reader |
| 100 | 4 | debit | (blank) | 175,846.56 | DATE_ORDER, ROW_BAL | second reader |
| 101 | 4 | credit | (blank) | 13,618.11 | DATE_ORDER, ROW_BAL | second reader |
| 102 | 4 | credit | (blank) | 10,951,650.40 | DATE_ORDER, ROW_BAL | second reader |
| 103 | 4 | debit | (blank) | 10,882,857.85 | DATE_ORDER, ROW_BAL | second reader |
| 104 | 4 | credit | (blank) | 11,977.00 | DATE_ORDER, ROW_BAL | second reader |
| 105 | 4 | credit | (blank) | 112,281.33 | DATE_ORDER, ROW_BAL | second reader |
| 106 | 4 | credit | (blank) | 51,005.54 | DATE_ORDER, ROW_BAL | second reader |
| 107 | 4 | credit | (blank) | 150,390.96 | DATE_ORDER, ROW_BAL | second reader |
| 108 | 4 | credit | (blank) | 783,753.39 | DATE_ORDER, ROW_BAL | second reader |
| 109 | 4 | debit | (blank) | 18,371.38 | DATE_ORDER, ROW_BAL | second reader |
| 110 | 4 | credit | (blank) | 366,011.21 | DATE_ORDER, ROW_BAL | second reader |
| 111 | 4 | credit | (blank) | 9,421,430.77 | DATE_ORDER, ROW_BAL | second reader |
| 112 | 4 | debit | (blank) | 8,543,619.49 | DATE_ORDER, ROW_BAL | second reader |
| 113 | 4 | credit | (blank) | 149,834.04 | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | credit | (blank) | 473,648.64 | DATE_ORDER, ROW_BAL | second reader |
| 116 | 4 | credit | (blank) | 7,664,507.60 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 4 | debit | (blank) | 8,238,417.30 | DATE_ORDER, ROW_BAL | second reader |
| 118 | 4 | credit | (blank) | 616,185.93 | DATE_ORDER, ROW_BAL | second reader |
| 119 | 4 | credit | (blank) | 282,609.71 | DATE_ORDER, ROW_BAL | second reader |
| 120 | 4 | credit | (blank) | 33,873.19 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 114, page 4, ROW_BAL: row 114: 287464065 + 0 = 287464065, but the balance column reads 293249862 (off by 5785797)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 04/03/2024 / (blank) / (blank) / 2,932,498.62; second reader 04/03/2024 / (blank) / 57,857.79 / 2,932,498.62 (date / debit / credit / balance)
- document, GLOBAL_BAL: opening 343954892 + movements 1005571346 = 1349526238, closing balance reads 1355312035

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 167 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 168 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
