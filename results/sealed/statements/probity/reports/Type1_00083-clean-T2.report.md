# Verification report: Type1_00083-clean-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:19, row:24.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 165 |
| Rule checks passed | 331 of 333 |
| Rows corrected | 31 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0452 |
| Document SHA-256 | `e99c66e6edba426c` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 13 | 2 | date | 06 Jan 2024 | 06-01-2024 14:09:21 | DATE_ORDER, ROW_BAL | second reader |
| 14 | 2 | date | 06 Jan 2024 | 06-01-2024 14:23:31 | DATE_ORDER, ROW_BAL | second reader |
| 15 | 2 | date | 08 Jan 2024 | 08-01-2024 14:31:06 | DATE_ORDER, ROW_BAL | second reader |
| 16 | 2 | date | 11 Jan 2024 | 11-01-2024 07:33:34 | DATE_ORDER, ROW_BAL | second reader |
| 17 | 2 | date | 11 Jan 2024 | 11-01-2024 09:30:00 | DATE_ORDER, ROW_BAL | second reader |
| 18 | 2 | date | 12 Jan 2024 | 12-01-2024 11:47:51 | DATE_ORDER, ROW_BAL | second reader |
| 20 | 2 | date | 13 Jan 2024 | 13-01-2024 10:25:05 | DATE_ORDER, ROW_BAL | second reader |
| 21 | 2 | date | 13 Jan 2024 | 13-01-2024 11:09:47 | DATE_ORDER, ROW_BAL | second reader |
| 22 | 2 | date | 13 Jan 2024 | 13-01-2024 12:29:43 | DATE_ORDER, ROW_BAL | second reader |
| 23 | 2 | date | 13 Jan 2024 | 13-01-2024 20:32:58 | DATE_ORDER, ROW_BAL | second reader |
| 25 | 2 | date | 15 Jan 2024 | 15-01-2024 13:52:23 | DATE_ORDER, ROW_BAL | second reader |
| 26 | 2 | date | 16 Jan 2024 | 16-01-2024 11:11:43 | DATE_ORDER, ROW_BAL | second reader |
| 27 | 2 | date | 16 Jan 2024 | 16-01-2024 13:52:06 | DATE_ORDER, ROW_BAL | second reader |
| 28 | 2 | date | 17 Jan 2024 | 17-01-2024 10:44:16 | DATE_ORDER, ROW_BAL | second reader |
| 29 | 2 | date | 17 Jan 2024 | 17-01-2024 14:14:55 | DATE_ORDER, ROW_BAL | second reader |
| 30 | 2 | date | 17 Jan 2024 | 17-01-2024 18:44:35 | DATE_ORDER, ROW_BAL | second reader |
| 31 | 2 | date | 18 Jan 2024 | 18-01-2024 09:00:00 | DATE_ORDER, ROW_BAL | second reader |
| 32 | 2 | date | 18 Jan 2024 | 18-01-2024 11:13:04 | DATE_ORDER, ROW_BAL | second reader |
| 33 | 2 | date | 18 Jan 2024 | 18-01-2024 13:21:50 | DATE_ORDER, ROW_BAL | second reader |
| 34 | 2 | date | 19 Jan 2024 | 19-01-2024 11:03:39 | DATE_ORDER, ROW_BAL | second reader |
| 35 | 2 | date | 19 Jan 2024 | 19-01-2024 14:43:39 | DATE_ORDER, ROW_BAL | second reader |
| 36 | 2 | date | 20 Jan 2024 | 20-01-2024 10:04:41 | DATE_ORDER, ROW_BAL | second reader |
| 37 | 2 | date | 20 Jan 2024 | 20-01-2024 10:50:00 | DATE_ORDER, ROW_BAL | second reader |
| 38 | 2 | date | 20 Jan 2024 | 20-01-2024 12:19:40 | DATE_ORDER, ROW_BAL | second reader |
| 39 | 2 | date | 20 Jan 2024 | 20-01-2024 12:30:31 | DATE_ORDER, ROW_BAL | second reader |
| 40 | 2 | date | 20 Jan 2024 | 20-01-2024 15:30:00 | DATE_ORDER, ROW_BAL | second reader |
| 41 | 2 | date | 22 Jan 2024 | 22-01-2024 11:05:56 | DATE_ORDER, ROW_BAL | second reader |
| 42 | 2 | date | 23 Jan 2024 | 23-01-2024 10:28:14 | DATE_ORDER, ROW_BAL | second reader |
| 43 | 2 | date | 23 Jan 2024 | 23-01-2024 10:59:40 | DATE_ORDER, ROW_BAL | second reader |
| 44 | 2 | date | 24 Jan 2024 | 24-01-2024 12:13:21 | DATE_ORDER, ROW_BAL | second reader |
| 45 | 2 | date | 24 Jan 2024 | 24-01-2024 18:38:24 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 19, page 2, DATE_ORDER: row 19 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 24, page 2, DATE_ORDER: row 24 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 165 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 163 | 2 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
