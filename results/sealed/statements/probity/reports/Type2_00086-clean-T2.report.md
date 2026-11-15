# Verification report: Type2_00086-clean-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:164.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 165 |
| Rule checks passed | 331 of 333 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0436 |
| Document SHA-256 | `4f9c431be5d982a3` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 76 | 3 | credit | 980,625.81 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 76 | 3 | debit | (blank) | 980,625.81 | DATE_ORDER, ROW_BAL | second reader |
| 130 | 5 | balance | 8,285,096.72 | 8,285,096.43 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 164, page 6, ROW_BAL: cannot check row 164: unreadable row[164].debit/credit
  - second look (DISPUTED): the readers agree on this row, but agreement on a row cannot settle ['ROW_BAL/UNREADABLE_OPERAND']
- document, GLOBAL_BAL: 1 rows have no readable amount

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 164 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 165 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
