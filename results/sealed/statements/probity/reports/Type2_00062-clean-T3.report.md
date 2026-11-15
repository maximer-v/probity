# Verification report: Type2_00062-clean-T3

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: the document could not be accepted, and no rule is failing.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 159 |
| Rule checks passed | 321 of 321 |
| Rows corrected | 4 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0425 |
| Document SHA-256 | `9ecc8e1ccf38d1c7` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 42 | 2 | credit | 1,650,672.69 | 1,650,672.66 | DATE_ORDER, ROW_BAL | second reader |
| 137 | 5 | credit | (blank) | 538,374.67 | DATE_ORDER, ROW_BAL | second reader |
| 137 | 5 | debit | 538,374.67 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | balance | 2,480,233.04 | 2,480,233.03 | DATE_ORDER, ROW_BAL | second reader |
| 142 | 5 | credit | 202,767.38 | 202,767.30 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- the document could not be accepted, and no rule is failing

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 159 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
