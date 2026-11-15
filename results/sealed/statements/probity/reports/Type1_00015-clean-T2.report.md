# Verification report: Type1_00015-clean-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:13, row:20, row:29, row:35, row:36, row:38.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 165 |
| Rule checks passed | 326 of 333 |
| Rows corrected | 26 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0430 |
| Document SHA-256 | `856373eb75bc1fa1` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 14 | 2 | date | 09 Jan 2024 | 09-01-2024 13:36:58 | DATE_ORDER, ROW_BAL | second reader |
| 15 | 2 | date | 10 Jan 2024 | 10-01-2024 11:12:24 | DATE_ORDER, ROW_BAL | second reader |
| 16 | 2 | date | 10 Jan 2024 | 10-01-2024 18:21:10 | DATE_ORDER, ROW_BAL | second reader |
| 17 | 2 | date | 10 Jan 2024 | 10-01-2024 21:25:16 | DATE_ORDER, ROW_BAL | second reader |
| 18 | 2 | date | 11 Jan 2024 | 11-01-2024 11:23:05 | DATE_ORDER, ROW_BAL | second reader |
| 19 | 2 | date | 11 Jan 2024 | 11-01-2024 12:16:42 | DATE_ORDER, ROW_BAL | second reader |
| 21 | 2 | date | 11 Jan 2024 | 11-01-2024 17:23:01 | DATE_ORDER, ROW_BAL | second reader |
| 22 | 2 | date | 12 Jan 2024 | 12-01-2024 12:47:30 | DATE_ORDER, ROW_BAL | second reader |
| 23 | 2 | date | 13 Jan 2024 | 13-01-2024 10:23:58 | DATE_ORDER, ROW_BAL | second reader |
| 24 | 2 | date | 13 Jan 2024 | 13-01-2024 11:23:05 | DATE_ORDER, ROW_BAL | second reader |
| 25 | 2 | date | 13 Jan 2024 | 13-01-2024 14:50:48 | DATE_ORDER, ROW_BAL | second reader |
| 26 | 2 | date | 13 Jan 2024 | 13-01-2024 21:42:13 | DATE_ORDER, ROW_BAL | second reader |
| 27 | 2 | date | 15 Jan 2024 | 15-01-2024 10:23:58 | DATE_ORDER, ROW_BAL | second reader |
| 28 | 2 | date | 15 Jan 2024 | 15-01-2024 16:13:52 | DATE_ORDER, ROW_BAL | second reader |
| 30 | 2 | date | 16 Jan 2024 | 16-01-2024 12:14:53 | DATE_ORDER, ROW_BAL | second reader |
| 31 | 2 | date | 16 Jan 2024 | 16-01-2024 13:29:38 | DATE_ORDER, ROW_BAL | second reader |
| 32 | 2 | date | 16 Jan 2024 | 16-01-2024 17:24:09 | DATE_ORDER, ROW_BAL | second reader |
| 33 | 2 | date | 17 Jan 2024 | 17-01-2024 12:52:35 | DATE_ORDER, ROW_BAL | second reader |
| 34 | 2 | date | 17 Jan 2024 | 17-01-2024 13:31:36 | DATE_ORDER, ROW_BAL | second reader |
| 37 | 2 | date | 19 Jan 2024 | 19-01-2024 12:08:59 | DATE_ORDER, ROW_BAL | second reader |
| 39 | 2 | date | 20 Jan 2024 | 20-01-2024 10:51:50 | DATE_ORDER, ROW_BAL | second reader |
| 40 | 2 | date | 20 Jan 2024 | 20-01-2024 15:30:00 | DATE_ORDER, ROW_BAL | second reader |
| 41 | 2 | date | 22 Jan 2024 | 22-01-2024 10:03:31 | DATE_ORDER, ROW_BAL | second reader |
| 42 | 2 | date | 24 Jan 2024 | 24-01-2024 07:19:45 | DATE_ORDER, ROW_BAL | second reader |
| 43 | 2 | date | 24 Jan 2024 | 24-01-2024 08:50:45 | DATE_ORDER, ROW_BAL | second reader |
| 45 | 2 | date | 24 Jan 2024 | 24-01-2024 19:56:13 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 13, page 2, DATE_ORDER: row 13 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 20, page 2, DATE_ORDER: row 20 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 29, page 2, DATE_ORDER: row 29 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 35, page 2, DATE_ORDER: row 35 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 36, page 2, DATE_ORDER: row 36 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 38, page 2, DATE_ORDER: row 38 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 44, page 2, DATE_ORDER: row 44 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 165 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 158 | 7 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
