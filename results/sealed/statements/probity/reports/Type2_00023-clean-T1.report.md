# Verification report: Type2_00023-clean-T1

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:112, row:114.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 157 |
| Rule checks passed | 314 of 317 |
| Rows corrected | 17 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 4 |
| Model cost | $0.0470 |
| Document SHA-256 | `7f4aac752215693e` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 42 | 2 | credit | 133,350.98 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 42 | 2 | debit | (blank) | 133,350.98 | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | credit | 225,531.98 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | debit | (blank) | 225,531.98 | DATE_ORDER, ROW_BAL | second reader |
| 85 | 4 | credit | 299.37 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 85 | 4 | debit | (blank) | 299.37 | DATE_ORDER, ROW_BAL | second reader |
| 89 | 4 | credit | 115,606.44 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 89 | 4 | debit | (blank) | 115,606.44 | DATE_ORDER, ROW_BAL | second reader |
| 91 | 4 | credit | 1,541,718.45 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 91 | 4 | debit | (blank) | 1,541,718.45 | DATE_ORDER, ROW_BAL | second reader |
| 92 | 4 | credit | 2,818,526.26 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 92 | 4 | debit | (blank) | 2,818,526.26 | DATE_ORDER, ROW_BAL | second reader |
| 96 | 4 | credit | 167,776.75 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 96 | 4 | debit | (blank) | 167,776.75 | DATE_ORDER, ROW_BAL | second reader |
| 99 | 4 | credit | 433,012.69 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 99 | 4 | debit | (blank) | 433,012.69 | DATE_ORDER, ROW_BAL | second reader |
| 101 | 4 | credit | 53,329.33 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 101 | 4 | debit | (blank) | 53,329.33 | DATE_ORDER, ROW_BAL | second reader |
| 103 | 4 | credit | 2,317,687.96 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 103 | 4 | debit | (blank) | 2,317,687.96 | DATE_ORDER, ROW_BAL | second reader |
| 107 | 4 | credit | 2,693,342.54 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 107 | 4 | debit | (blank) | 2,693,342.54 | DATE_ORDER, ROW_BAL | second reader |
| 108 | 4 | credit | 18,290,352.58 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 108 | 4 | debit | (blank) | 18,290,352.58 | DATE_ORDER, ROW_BAL | second reader |
| 110 | 4 | credit | 8,343,116.23 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 110 | 4 | debit | (blank) | 8,343,116.23 | DATE_ORDER, ROW_BAL | second reader |
| 111 | 4 | credit | 402,991.88 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 111 | 4 | debit | (blank) | 402,991.88 | DATE_ORDER, ROW_BAL | second reader |
| 116 | 4 | credit | 15,970.00 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 116 | 4 | debit | (blank) | 15,970.00 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 4 | credit | 1,638,087.92 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 117 | 4 | debit | (blank) | 1,638,087.92 | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | credit | 636,138.45 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | debit | (blank) | 636,138.45 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 112, page 4, ROW_BAL: row 112: 662735059 + 83754963 = 746490022, but the balance column reads 746490222 (off by 200)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 07/03/2024 / (blank) / 837,549.63 / 7,464,902.22; second reader 07/03/2024 / (blank) / 837,549.63 / 7,464,900.22 (date / debit / credit / balance)
- row 114, page 4, ROW_BAL: row 114: 746490222 + 113234779 = 859725001, but the balance column reads 633255243 (off by -226469758)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 07/03/2024 / (blank) / 1,132,347.79 / 6,332,552.43; second reader 07/03/2024 / 1,132,347.79 / (blank) / 6,332,552.43 (date / debit / credit / balance)
- document, GLOBAL_BAL: opening 198944085 + movements 406498513 = 605442598, closing balance reads 378973040

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 155 | 2 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 157 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
