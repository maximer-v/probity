# Verification report: Type2_00038-clean-T2

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 2 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 165 |
| Rule checks passed | 333 of 333 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0417 |
| Document SHA-256 | `d74d4cc4856da3ac` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 5 | 1 | balance | 6,739,184.46 | 6,739,154.46 | DATE_ORDER, ROW_BAL | second reader |
| 75 | 3 | balance | 1,425,950.38 | 1,425,950.34 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 165 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 165 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
