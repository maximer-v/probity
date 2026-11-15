# Verification report: Type2_00033-row_removed-T3

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:31, row:38, row:39, row:40.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 155 |
| Rule checks passed | 308 of 313 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0421 |
| Document SHA-256 | `fdcb64efad56a1e3` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 70 | 3 | balance | 2,576,698.20 | 2,576,698.29 | DATE_ORDER, ROW_BAL | second reader |
| 97 | 4 | balance | 28,596,792.16 | 28,596,972.16 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 31, page 2, ROW_BAL: row 31: 254568182 + -179299557 = 75268625, but the balance column reads 433867739 (off by 358599114)
  - second look (UNAVAILABLE): the model's reply was not valid JSON
- row 38, page 2, ROW_BAL: row 38: 1169371610 + -16585995 = 1152785615, but the balance column reads 1152785614 (off by -1)
  - second look (UNAVAILABLE): the model's reply was not valid JSON
- row 39, page 2, ROW_BAL: row 39: 1152785614 + -214000791 = 938784823, but the balance column reads 938784824 (off by 1)
  - second look (UNAVAILABLE): the model's reply was not valid JSON
- row 40, page 2, ROW_BAL: row 40: 938784824 + -136911773 = 801873051, but the balance column reads 969827572 (off by 167954521)
  - second look (UNAVAILABLE): the model's reply was not valid JSON
- document, GLOBAL_BAL: opening 400208509 + movements 144189914 = 544398423, closing balance reads 1070952058

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 151 | 4 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 155 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
