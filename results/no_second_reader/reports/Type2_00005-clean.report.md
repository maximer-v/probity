# Verification report: agami-Digital_Type2_00005-scan-repaired

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 4 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 156 |
| Rule checks passed | 315 of 315 |
| Rows corrected | 4 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `a015bdbc6041c0f4` |

## Corrections

8 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 103 | 4 | credit | 200,901.51 CR | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 103 | 4 | debit | (blank) | 200,901.51 | DATE_ORDER, ROW_BAL | same reader |
| 128 | 5 | credit | 91,841.60 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 128 | 5 | debit | (blank) | 91,841.60 | DATE_ORDER, ROW_BAL | same reader |
| 135 | 5 | credit | 370,346.93 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 135 | 5 | debit | (blank) | 370,346.93 | DATE_ORDER, ROW_BAL | same reader |
| 147 | 5 | credit | 2,027,999.29 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 147 | 5 | debit | (blank) | 2,027,999.29 | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 156 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 156 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
