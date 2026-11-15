# Verification report: Type1_00090-text-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:15, row:20, row:25, row:43, row:50, row:113.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 156 |
| Rule checks passed | 305 of 315 |
| Rows corrected | 91 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0464 |
| Document SHA-256 | `33f9cc81356e8af8` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 13 | 2 | date | 09 Jan 2024 | 09-01-2024 14:12:16 | DATE_ORDER, ROW_BAL | second reader |
| 14 | 2 | date | 09 Jan 2024 | 09-01-2024 16:18:35 | DATE_ORDER, ROW_BAL | second reader |
| 16 | 2 | date | 10 Jan 2024 | 10-01-2024 13:36:37 | DATE_ORDER, ROW_BAL | second reader |
| 17 | 2 | date | 11 Jan 2024 | 11-01-2024 10:03:24 | DATE_ORDER, ROW_BAL | second reader |
| 18 | 2 | date | 15 Jan 2024 | 15-01-2024 12:30:53 | DATE_ORDER, ROW_BAL | second reader |
| 19 | 2 | date | 15 Jan 2024 | 15-01-2024 14:29:07 | DATE_ORDER, ROW_BAL | second reader |
| 21 | 2 | date | 15 Jan 2024 | 15-01-2024 15:41:14 | DATE_ORDER, ROW_BAL | second reader |
| 22 | 2 | date | 16 Jan 2024 | 16-01-2024 08:45:54 | DATE_ORDER, ROW_BAL | second reader |
| 23 | 2 | date | 16 Jan 2024 | 16-01-2024 21:56:26 | DATE_ORDER, ROW_BAL | second reader |
| 24 | 2 | date | 17 Jan 2024 | 17-01-2024 10:46:17 | DATE_ORDER, ROW_BAL | second reader |
| 26 | 2 | date | 17 Jan 2024 | 17-01-2024 11:43:18 | DATE_ORDER, ROW_BAL | second reader |
| 27 | 2 | date | 17 Jan 2024 | 17-01-2024 13:23:00 | DATE_ORDER, ROW_BAL | second reader |
| 28 | 2 | date | 18 Jan 2024 | 18-01-2024 11:44:03 | DATE_ORDER, ROW_BAL | second reader |
| 29 | 2 | date | 19 Jan 2024 | 19-01-2024 20:06:34 | DATE_ORDER, ROW_BAL | second reader |
| 30 | 2 | date | 20 Jan 2024 | 20-01-2024 19:48:56 | DATE_ORDER, ROW_BAL | second reader |
| 31 | 2 | date | 22 Jan 2024 | 22-01-2024 07:26:45 | DATE_ORDER, ROW_BAL | second reader |
| 32 | 2 | date | 22 Jan 2024 | 22-01-2024 13:57:07 | DATE_ORDER, ROW_BAL | second reader |
| 33 | 2 | date | 22 Jan 2024 | 22-01-2024 15:45:00 | DATE_ORDER, ROW_BAL | second reader |
| 34 | 2 | date | 22 Jan 2024 | 22-01-2024 16:46:41 | DATE_ORDER, ROW_BAL | second reader |
| 35 | 2 | date | 23 Jan 2024 | 23-01-2024 07:33:01 | DATE_ORDER, ROW_BAL | second reader |
| 36 | 2 | date | 23 Jan 2024 | 23-01-2024 12:22:44 | DATE_ORDER, ROW_BAL | second reader |
| 37 | 2 | date | 23 Jan 2024 | 23-01-2024 14:25:19 | DATE_ORDER, ROW_BAL | second reader |
| 38 | 2 | date | 24 Jan 2024 | 24-01-2024 10:40:51 | DATE_ORDER, ROW_BAL | second reader |
| 39 | 2 | date | 24 Jan 2024 | 24-01-2024 14:55:35 | DATE_ORDER, ROW_BAL | second reader |
| 40 | 2 | date | 25 Jan 2024 | 25-01-2024 21:09:24 | DATE_ORDER, ROW_BAL | second reader |
| 41 | 2 | date | 29 Jan 2024 | 29-01-2024 08:06:29 | DATE_ORDER, ROW_BAL | second reader |
| 42 | 2 | date | 29 Jan 2024 | 29-01-2024 10:12:13 | DATE_ORDER, ROW_BAL | second reader |
| 44 | 2 | date | 30 Jan 2024 | 30-01-2024 12:48:05 | DATE_ORDER, ROW_BAL | second reader |
| 45 | 2 | date | 30 Jan 2024 | 30-01-2024 13:25:12 | DATE_ORDER, ROW_BAL | second reader |
| 46 | 3 | date | 30 Jan 2024 | 30-01-2024 21:23:55 | DATE_ORDER, ROW_BAL | second reader |
| 47 | 3 | date | 31 Jan 2024 | 31-01-2024 12:55:16 | DATE_ORDER, ROW_BAL | second reader |
| 48 | 3 | date | 31 Jan 2024 | 31-01-2024 21:23:55 | DATE_ORDER, ROW_BAL | second reader |
| 49 | 3 | date | 01 Feb 2024 | 01-02-2024 13:15:46 | DATE_ORDER, ROW_BAL | second reader |
| 51 | 3 | date | 02 Feb 2024 | 02-02-2024 12:50:17 | DATE_ORDER, ROW_BAL | second reader |
| 52 | 3 | date | 02 Feb 2024 | 02-02-2024 21:07:39 | DATE_ORDER, ROW_BAL | second reader |
| 53 | 3 | date | 03 Feb 2024 | 03-02-2024 11:09:19 | DATE_ORDER, ROW_BAL | second reader |
| 54 | 3 | date | 03 Feb 2024 | 03-02-2024 14:29:53 | DATE_ORDER, ROW_BAL | second reader |
| 55 | 3 | date | 06 Feb 2024 | 06-02-2024 10:46:25 | DATE_ORDER, ROW_BAL | second reader |
| 56 | 3 | date | 06 Feb 2024 | 06-02-2024 17:31:51 | DATE_ORDER, ROW_BAL | second reader |
| 57 | 3 | date | 06 Feb 2024 | 06-02-2024 20:14:55 | DATE_ORDER, ROW_BAL | second reader |
| 58 | 3 | date | 07 Feb 2024 | 07-02-2024 06:57:38 | DATE_ORDER, ROW_BAL | second reader |
| 59 | 3 | date | 07 Feb 2024 | 07-02-2024 14:52:47 | DATE_ORDER, ROW_BAL | second reader |
| 60 | 3 | date | 07 Feb 2024 | 07-02-2024 15:48:44 | DATE_ORDER, ROW_BAL | second reader |
| 61 | 3 | date | 08 Feb 2024 | 08-02-2024 10:20:58 | DATE_ORDER, ROW_BAL | second reader |
| 62 | 3 | date | 08 Feb 2024 | 08-02-2024 15:43:29 | DATE_ORDER, ROW_BAL | second reader |
| 63 | 3 | date | 08 Feb 2024 | 08-02-2024 19:08:44 | DATE_ORDER, ROW_BAL | second reader |
| 64 | 3 | date | 09 Feb 2024 | 09-02-2024 10:56:00 | DATE_ORDER, ROW_BAL | second reader |
| 65 | 3 | date | 10 Feb 2024 | 10-02-2024 14:49:50 | DATE_ORDER, ROW_BAL | second reader |
| 66 | 3 | date | 12 Feb 2024 | 12-02-2024 12:23:15 | DATE_ORDER, ROW_BAL | second reader |
| 67 | 3 | date | 12 Feb 2024 | 12-02-2024 12:57:09 | DATE_ORDER, ROW_BAL | second reader |
| 68 | 3 | date | 12 Feb 2024 | 12-02-2024 14:31:28 | DATE_ORDER, ROW_BAL | second reader |
| 69 | 3 | date | 13 Feb 2024 | 13-02-2024 11:41:17 | DATE_ORDER, ROW_BAL | second reader |
| 70 | 3 | date | 13 Feb 2024 | 13-02-2024 15:26:13 | DATE_ORDER, ROW_BAL | second reader |
| 71 | 3 | date | 13 Feb 2024 | 13-02-2024 15:27:22 | DATE_ORDER, ROW_BAL | second reader |
| 72 | 3 | date | 13 Feb 2024 | 13-02-2024 16:03:50 | DATE_ORDER, ROW_BAL | second reader |
| 73 | 3 | date | 14 Feb 2024 | 14-02-2024 11:03:34 | DATE_ORDER, ROW_BAL | second reader |
| 74 | 3 | date | 14 Feb 2024 | 14-02-2024 12:48:53 | DATE_ORDER, ROW_BAL | second reader |
| 75 | 3 | date | 14 Feb 2024 | 14-02-2024 13:21:20 | DATE_ORDER, ROW_BAL | second reader |
| 76 | 3 | date | 14 Feb 2024 | 14-02-2024 14:22:10 | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | date | 15 Feb 2024 | 15-02-2024 12:15:36 | DATE_ORDER, ROW_BAL | second reader |
| 78 | 3 | date | 15 Feb 2024 | 15-02-2024 18:42:30 | DATE_ORDER, ROW_BAL | second reader |
| 112 | 5 | date | 01 Mar 2024 | 01-03-2024 10:40:23 | DATE_ORDER, ROW_BAL | second reader |
| 114 | 5 | date | 02 Mar 2024 | 02-03-2024 13:45:52 | DATE_ORDER, ROW_BAL | second reader |
| 115 | 5 | date | 04 Mar 2024 | 04-03-2024 15:44:03 | DATE_ORDER, ROW_BAL | second reader |
| 116 | 5 | date | 06 Mar 2024 | 06-03-2024 10:16:01 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 5 | date | 07 Mar 2024 | 07-03-2024 13:14:45 | DATE_ORDER, ROW_BAL | second reader |
| 118 | 5 | date | 09 Mar 2024 | 09-03-2024 11:30:37 | DATE_ORDER, ROW_BAL | second reader |
| 119 | 5 | date | 09 Mar 2024 | 09-03-2024 12:19:58 | DATE_ORDER, ROW_BAL | second reader |
| 120 | 5 | date | 09 Mar 2024 | 09-03-2024 14:53:02 | DATE_ORDER, ROW_BAL | second reader |
| 121 | 5 | date | 09 Mar 2024 | 09-03-2024 21:52:42 | DATE_ORDER, ROW_BAL | second reader |
| 122 | 5 | date | 09 Mar 2024 | 09-03-2024 21:56:22 | DATE_ORDER, ROW_BAL | second reader |
| 123 | 5 | date | 11 Mar 2024 | 11-03-2024 09:54:39 | DATE_ORDER, ROW_BAL | second reader |
| 124 | 5 | date | 11 Mar 2024 | 11-03-2024 16:33:02 | DATE_ORDER, ROW_BAL | second reader |
| 125 | 5 | date | 11 Mar 2024 | 11-03-2024 19:41:35 | DATE_ORDER, ROW_BAL | second reader |
| 126 | 5 | date | 12 Mar 2024 | 12-03-2024 14:36:44 | DATE_ORDER, ROW_BAL | second reader |
| 127 | 5 | date | 12 Mar 2024 | 12-03-2024 15:43:05 | DATE_ORDER, ROW_BAL | second reader |
| 128 | 5 | date | 12 Mar 2024 | 12-03-2024 20:11:51 | DATE_ORDER, ROW_BAL | second reader |
| 129 | 5 | date | 13 Mar 2024 | 13-03-2024 11:34:23 | DATE_ORDER, ROW_BAL | second reader |
| 130 | 5 | date | 13 Mar 2024 | 13-03-2024 19:35:48 | DATE_ORDER, ROW_BAL | second reader |
| 131 | 5 | date | 15 Mar 2024 | 15-03-2024 15:23:17 | DATE_ORDER, ROW_BAL | second reader |
| 132 | 5 | date | 16 Mar 2024 | 16-03-2024 10:42:10 | DATE_ORDER, ROW_BAL | second reader |
| 133 | 5 | date | 16 Mar 2024 | 16-03-2024 11:07:15 | DATE_ORDER, ROW_BAL | second reader |
| 134 | 5 | date | 16 Mar 2024 | 16-03-2024 13:06:09 | DATE_ORDER, ROW_BAL | second reader |
| 137 | 5 | date | 19 Mar 2024 | 19-03-2024 11:49:14 | DATE_ORDER, ROW_BAL | second reader |
| 138 | 5 | date | 19 Mar 2024 | 19-03-2024 13:07:16 | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | date | 19 Mar 2024 | 19-03-2024 16:14:03 | DATE_ORDER, ROW_BAL | second reader |
| 140 | 5 | date | 20 Mar 2024 | 20-03-2024 06:24:37 | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | date | 21 Mar 2024 | 21-03-2024 12:35:30 | DATE_ORDER, ROW_BAL | second reader |
| 142 | 5 | date | 22 Mar 2024 | 22-03-2024 12:54:37 | DATE_ORDER, ROW_BAL | second reader |
| 143 | 5 | date | 23 Mar 2024 | 23-03-2024 07:36:45 | DATE_ORDER, ROW_BAL | second reader |
| 144 | 5 | date | 23 Mar 2024 | 23-03-2024 14:10:58 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 15, page 2, DATE_ORDER: row 15 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 20, page 2, DATE_ORDER: row 20 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 25, page 2, DATE_ORDER: row 25 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 43, page 2, DATE_ORDER: row 43 has no readable date
  - second look (UNALIGNED): the second reading of page 2 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 50, page 3, DATE_ORDER: row 50 has no readable date
  - second look (UNALIGNED): the second reading of page 3 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 113, page 5, DATE_ORDER: row 113 has no readable date
- row 135, page 5, ROW_BAL: row 135: 631416 + 58660 = 690076, but the balance column reads 690067 (off by -9)
- row 135, page 5, DATE_ORDER: row 135 has no readable date
- row 136, page 5, ROW_BAL: row 136: 690067 + 320389 = 1010456, but the balance column reads 1010465 (off by 9)
- row 136, page 5, DATE_ORDER: row 136 has no readable date

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 154 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 148 | 8 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
