# Verification report: Type1_00077-row_removed-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:108.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 163 |
| Rule checks passed | 327 of 329 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0476 |
| Document SHA-256 | `0975c42236f6d7f8` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 132 | 5 | credit | Rs. 443,902.00 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 132 | 5 | debit | (blank) | Rs. 443,902.00 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 108, page 4, ROW_BAL: row 108: 64613424 + -14498870 = 50114554, but the balance column reads 52878283 (off by 2763729)
  - second look (DISPUTED): row 107, which this row's rule is computed from, could not be matched in the second reading
- document, GLOBAL_BAL: opening 37514801 + movements 32901642 = 70416443, closing balance reads 73180172

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 162 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 163 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
