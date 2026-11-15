# Verification report: Type2_00037-clean-T2

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 7 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 168 |
| Rule checks passed | 339 of 339 |
| Rows corrected | 7 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0392 |
| Document SHA-256 | `2fddf0fa34e2ad39` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 157 | 6 | debit | (blank) | 262.22 | DATE_ORDER, ROW_BAL | second reader |
| 158 | 6 | debit | (blank) | 15,541.67 | DATE_ORDER, ROW_BAL | second reader |
| 159 | 6 | debit | (blank) | 1,350.15 | DATE_ORDER, ROW_BAL | second reader |
| 160 | 6 | debit | (blank) | 661,280.18 | DATE_ORDER, ROW_BAL | second reader |
| 162 | 6 | debit | (blank) | 163.88 | DATE_ORDER, ROW_BAL | second reader |
| 163 | 6 | debit | (blank) | 1,864,147.91 | DATE_ORDER, ROW_BAL | second reader |
| 167 | 6 | debit | (blank) | 105.22 | DATE_ORDER, LAST_ROW_EQ_CLOSING, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 168 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 168 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
