# Verification report: agami-Digital_Type2_00007-scan-repaired

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:93.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 160 |
| Rule checks passed | 321 of 323 |
| Rows corrected | 35 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0000 |
| Document SHA-256 | `7b1148e99d78e941` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 22 | 2 | credit | 73,791.10 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 22 | 2 | debit | (blank) | 73,791.10 | DATE_ORDER, ROW_BAL | second reader |
| 85 | 4 | debit | (blank) | 16,257.71 | DATE_ORDER, ROW_BAL | second reader |
| 86 | 4 | debit | (blank) | 68,160.94 | DATE_ORDER, ROW_BAL | second reader |
| 87 | 4 | credit | (blank) | 5,400.66 | DATE_ORDER, ROW_BAL | second reader |
| 88 | 4 | debit | (blank) | 15,037.68 | DATE_ORDER, ROW_BAL | second reader |
| 89 | 4 | credit | (blank) | 12,637.58 | DATE_ORDER, ROW_BAL | second reader |
| 90 | 4 | credit | (blank) | 14,817.22 | DATE_ORDER, ROW_BAL | second reader |
| 91 | 4 | credit | (blank) | 49,787.83 | DATE_ORDER, ROW_BAL | second reader |
| 92 | 4 | debit | (blank) | 45,288.96 | DATE_ORDER, ROW_BAL | second reader |
| 94 | 4 | credit | (blank) | 51,314.22 | DATE_ORDER, ROW_BAL | second reader |
| 95 | 4 | debit | (blank) | 83,469.48 | DATE_ORDER, ROW_BAL | second reader |
| 96 | 4 | debit | (blank) | 17,124.82 | DATE_ORDER, ROW_BAL | second reader |
| 97 | 4 | credit | (blank) | 18,157.36 | DATE_ORDER, ROW_BAL | second reader |
| 98 | 4 | credit | (blank) | 5,848.54 | DATE_ORDER, ROW_BAL | second reader |
| 99 | 4 | credit | (blank) | 5,856.11 | DATE_ORDER, ROW_BAL | second reader |
| 100 | 4 | credit | (blank) | 22,256.55 | DATE_ORDER, ROW_BAL | second reader |
| 101 | 4 | debit | (blank) | 159,519.66 | DATE_ORDER, ROW_BAL | second reader |
| 102 | 4 | credit | (blank) | 776.85 | DATE_ORDER, ROW_BAL | second reader |
| 103 | 4 | debit | (blank) | 445.26 | DATE_ORDER, ROW_BAL | second reader |
| 104 | 4 | credit | (blank) | 95,258.20 | DATE_ORDER, ROW_BAL | second reader |
| 105 | 4 | credit | (blank) | 17,856.35 | DATE_ORDER, ROW_BAL | second reader |
| 106 | 4 | debit | (blank) | 1,788.92 | DATE_ORDER, ROW_BAL | second reader |
| 107 | 4 | credit | (blank) | 526.77 | DATE_ORDER, ROW_BAL | second reader |
| 108 | 4 | debit | (blank) | 56,310.19 | DATE_ORDER, ROW_BAL | second reader |
| 109 | 4 | credit | (blank) | 3,607.04 | DATE_ORDER, ROW_BAL | second reader |
| 110 | 4 | debit | (blank) | 98,646.15 | DATE_ORDER, ROW_BAL | second reader |
| 111 | 4 | credit | (blank) | 76,608.59 | DATE_ORDER, ROW_BAL | second reader |
| 112 | 4 | credit | (blank) | 713.90 | DATE_ORDER, ROW_BAL | second reader |
| 113 | 4 | credit | (blank) | 242.04 | DATE_ORDER, ROW_BAL | second reader |
| 114 | 4 | credit | (blank) | 1,101.28 | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | debit | (blank) | 12,413.99 | DATE_ORDER, ROW_BAL | second reader |
| 116 | 4 | credit | (blank) | 3,497.16 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 4 | credit | (blank) | 36,203.59 | DATE_ORDER, ROW_BAL | second reader |
| 118 | 4 | credit | (blank) | 30,375.21 | DATE_ORDER, ROW_BAL | second reader |
| 119 | 4 | credit | (blank) | 4,005.01 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 93, page 4, ROW_BAL: row 93: 17251512 + 0 = 17251512, but the balance column reads 15742375 (off by -1509137)
  - second look (UNALIGNED): the second reading of page 4 has 35 rows against 35, and no row in it could be shown to be the row in question
- document, GLOBAL_BAL: opening 39385089 + movements -24380354 = 15004735, closing balance reads 13495598

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 160 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
