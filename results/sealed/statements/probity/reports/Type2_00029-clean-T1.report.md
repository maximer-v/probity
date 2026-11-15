# Verification report: Type2_00029-clean-T1

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 4 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 158 |
| Rule checks passed | 319 of 319 |
| Rows corrected | 4 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0396 |
| Document SHA-256 | `6d46d29007b5c5fb` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 56 | 3 | credit | (blank) | 440,056.52 | DATE_ORDER, ROW_BAL | second reader |
| 56 | 3 | debit | 440,056.52 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 58 | 3 | balance | 41,276,638.85 | 41,276,638.38 | DATE_ORDER, ROW_BAL | second reader |
| 71 | 3 | credit | (blank) | 210,191.58 | DATE_ORDER, ROW_BAL | second reader |
| 71 | 3 | debit | 210,191.58 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 92 | 4 | balance | 5,173,262.67 | 5,173,262.83 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 158 | 0 |
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
