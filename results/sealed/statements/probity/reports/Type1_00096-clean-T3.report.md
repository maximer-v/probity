# Verification report: Type1_00096-clean-T3

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:64, row:66.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 157 |
| Rule checks passed | 315 of 317 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0460 |
| Document SHA-256 | `84c3d4a2f25ba2b7` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 86 | 4 | balance | Rs. 1,998,348.18 | Rs. 1,998,348.16 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 64, page 3, ROW_BAL: row 64: 2920395740 + -126252264 = 2794143476, but the balance column reads 2794143474 (off by -2)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 08-02-2024 12:14:43 / Rs. 1,262,522.64 / (blank) / Rs. 27,941,434.74; second reader 08-02-2024 12:14:43 / Rs. 1,262,522.64 / (blank) / Rs. 27,941,434.76 (date / debit / credit / balance)
- row 66, page 3, ROW_BAL: row 66: 3929249341 + -617480648 = 3311768693, but the balance column reads 3311768695 (off by 2)
  - second look (DISPUTED): the two readers did not independently agree on the date and balance of row 65, which this row's rule is computed from

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 155 | 2 |
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
