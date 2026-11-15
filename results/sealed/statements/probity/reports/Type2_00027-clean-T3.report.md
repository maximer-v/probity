# Verification report: Type2_00027-clean-T3

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:134, row:155.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 158 |
| Rule checks passed | 317 of 319 |
| Rows corrected | 3 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 4 |
| Model cost | $0.0491 |
| Document SHA-256 | `5da5b193ca99292b` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 25 | 2 | balance | 5,993,748.58 | 5,993,748.52 | DATE_ORDER, ROW_BAL | second reader |
| 101 | 4 | credit | (blank) | 394,506.09 | DATE_ORDER, ROW_BAL | second reader |
| 101 | 4 | debit | 394,506.09 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 112 | 4 | balance | 13,216,906.51 | 13,216,906.14 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 134, page 5, ROW_BAL: row 134: 708800615 + 34472924 = 743273539, but the balance column reads 743273534 (off by -5)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 19/03/2024 / (blank) / 344,729.24 / 7,432,735.34; second reader 19/03/2024 / (blank) / 344,729.24 / 7,432,735.39 (date / debit / credit / balance)
- row 155, page 6, ROW_BAL: row 155: 170564224 + 37369 = 170601593, but the balance column reads 170601598 (off by 5)
  - second look (DISPUTED): the two readers did not independently agree on the date and balance of row 154, which this row's rule is computed from

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 156 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 158 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
