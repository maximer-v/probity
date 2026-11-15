# Verification report: Type1_00086-clean-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:112, row:122, row:126, row:139, row:140, row:142.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 157 |
| Rule checks passed | 311 of 317 |
| Rows corrected | 27 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0420 |
| Document SHA-256 | `1ce45f708aa2e151` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 113 | 5 | date | 07 Mar 2024 | 07-03-2024 11:57:10 | DATE_ORDER, ROW_BAL | second reader |
| 114 | 5 | date | 07 Mar 2024 | 07-03-2024 15:49:30 | DATE_ORDER, ROW_BAL | second reader |
| 115 | 5 | date | 07 Mar 2024 | 07-03-2024 19:09:29 | DATE_ORDER, ROW_BAL | second reader |
| 116 | 5 | date | 09 Mar 2024 | 09-03-2024 09:21:01 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 5 | date | 09 Mar 2024 | 09-03-2024 19:48:51 | DATE_ORDER, ROW_BAL | second reader |
| 118 | 5 | date | 11 Mar 2024 | 11-03-2024 20:26:18 | DATE_ORDER, ROW_BAL | second reader |
| 119 | 5 | date | 13 Mar 2024 | 13-03-2024 16:22:34 | DATE_ORDER, ROW_BAL | second reader |
| 120 | 5 | date | 14 Mar 2024 | 14-03-2024 12:52:18 | DATE_ORDER, ROW_BAL | second reader |
| 121 | 5 | credit | Rs. 1,604,477.73 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 121 | 5 | date | 15 Mar 2024 | 15-03-2024 14:00:00 | DATE_ORDER, ROW_BAL | second reader |
| 121 | 5 | debit | (blank) | Rs. 1,604,477.73 | DATE_ORDER, ROW_BAL | second reader |
| 123 | 5 | date | 16 Mar 2024 | 16-03-2024 10:29:28 | DATE_ORDER, ROW_BAL | second reader |
| 124 | 5 | date | 16 Mar 2024 | 16-03-2024 11:49:58 | DATE_ORDER, ROW_BAL | second reader |
| 125 | 5 | date | 16 Mar 2024 | 16-03-2024 13:40:55 | DATE_ORDER, ROW_BAL | second reader |
| 127 | 5 | date | 16 Mar 2024 | 16-03-2024 14:45:24 | DATE_ORDER, ROW_BAL | second reader |
| 128 | 5 | date | 16 Mar 2024 | 16-03-2024 15:42:59 | DATE_ORDER, ROW_BAL | second reader |
| 129 | 5 | date | 16 Mar 2024 | 16-03-2024 17:43:07 | DATE_ORDER, ROW_BAL | second reader |
| 130 | 5 | date | 16 Mar 2024 | 16-03-2024 19:43:48 | DATE_ORDER, ROW_BAL | second reader |
| 131 | 5 | date | 18 Mar 2024 | 18-03-2024 15:14:44 | DATE_ORDER, ROW_BAL | second reader |
| 132 | 5 | date | 18 Mar 2024 | 18-03-2024 19:29:29 | DATE_ORDER, ROW_BAL | second reader |
| 133 | 5 | date | 19 Mar 2024 | 19-03-2024 11:03:08 | DATE_ORDER, ROW_BAL | second reader |
| 134 | 5 | date | 19 Mar 2024 | 19-03-2024 15:06:09 | DATE_ORDER, ROW_BAL | second reader |
| 135 | 5 | date | 20 Mar 2024 | 20-03-2024 11:34:20 | DATE_ORDER, ROW_BAL | second reader |
| 136 | 5 | date | 20 Mar 2024 | 20-03-2024 13:38:32 | DATE_ORDER, ROW_BAL | second reader |
| 137 | 5 | date | 20 Mar 2024 | 20-03-2024 14:19:55 | DATE_ORDER, ROW_BAL | second reader |
| 138 | 5 | date | 21 Mar 2024 | 21-03-2024 10:56:19 | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | date | 26 Mar 2024 | 26-03-2024 07:49:22 | DATE_ORDER, ROW_BAL | second reader |
| 143 | 5 | date | 26 Mar 2024 | 26-03-2024 14:19:37 | DATE_ORDER, ROW_BAL | second reader |
| 144 | 5 | date | 26 Mar 2024 | 26-03-2024 19:37:50 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 112, page 5, DATE_ORDER: row 112 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 122, page 5, DATE_ORDER: row 122 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 126, page 5, DATE_ORDER: row 126 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 139, page 5, DATE_ORDER: row 139 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 140, page 5, DATE_ORDER: row 140 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 142, page 5, DATE_ORDER: row 142 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 157 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 151 | 6 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
