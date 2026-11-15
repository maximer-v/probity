# Verification report: Type1_00016-amount_adjusted-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:115.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 158 |
| Rule checks passed | 318 of 319 |
| Rows corrected | 32 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0418 |
| Document SHA-256 | `a2a7c3d08df9388e` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 112 | 5 | date | 05 Mar 2024 | 05-03-2024 13:50:04 | DATE_ORDER, ROW_BAL | second reader |
| 113 | 5 | date | 06 Mar 2024 | 06-03-2024 06:42:52 | DATE_ORDER, ROW_BAL | second reader |
| 114 | 5 | date | 06 Mar 2024 | 06-03-2024 10:27:16 | DATE_ORDER, ROW_BAL | second reader |
| 116 | 5 | date | 07 Mar 2024 | 07-03-2024 12:15:34 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 5 | date | 07 Mar 2024 | 07-03-2024 23:30:00 | DATE_ORDER, ROW_BAL | second reader |
| 118 | 5 | date | 09 Mar 2024 | 09-03-2024 11:06:17 | DATE_ORDER, ROW_BAL | second reader |
| 119 | 5 | date | 09 Mar 2024 | 09-03-2024 15:19:15 | DATE_ORDER, ROW_BAL | second reader |
| 120 | 5 | date | 09 Mar 2024 | 09-03-2024 21:16:48 | DATE_ORDER, ROW_BAL | second reader |
| 121 | 5 | date | 11 Mar 2024 | 11-03-2024 14:38:39 | DATE_ORDER, ROW_BAL | second reader |
| 122 | 5 | date | 12 Mar 2024 | 12-03-2024 19:45:15 | DATE_ORDER, ROW_BAL | second reader |
| 123 | 5 | date | 14 Mar 2024 | 14-03-2024 10:32:31 | DATE_ORDER, ROW_BAL | second reader |
| 124 | 5 | date | 15 Mar 2024 | 15-03-2024 13:08:53 | DATE_ORDER, ROW_BAL | second reader |
| 125 | 5 | date | 15 Mar 2024 | 15-03-2024 14:00:00 | DATE_ORDER, ROW_BAL | second reader |
| 126 | 5 | date | 16 Mar 2024 | 16-03-2024 12:16:15 | DATE_ORDER, ROW_BAL | second reader |
| 127 | 5 | date | 16 Mar 2024 | 16-03-2024 21:20:35 | DATE_ORDER, ROW_BAL | second reader |
| 128 | 5 | date | 18 Mar 2024 | 18-03-2024 11:32:31 | DATE_ORDER, ROW_BAL | second reader |
| 129 | 5 | date | 18 Mar 2024 | 18-03-2024 14:14:54 | DATE_ORDER, ROW_BAL | second reader |
| 130 | 5 | date | 19 Mar 2024 | 19-03-2024 11:02:57 | DATE_ORDER, ROW_BAL | second reader |
| 131 | 5 | date | 20 Mar 2024 | 20-03-2024 07:42:48 | DATE_ORDER, ROW_BAL | second reader |
| 132 | 5 | date | 20 Mar 2024 | 20-03-2024 11:45:00 | DATE_ORDER, ROW_BAL | second reader |
| 133 | 5 | date | 20 Mar 2024 | 20-03-2024 12:01:06 | DATE_ORDER, ROW_BAL | second reader |
| 134 | 5 | date | 20 Mar 2024 | 20-03-2024 12:59:12 | DATE_ORDER, ROW_BAL | second reader |
| 135 | 5 | date | 20 Mar 2024 | 20-03-2024 19:26:14 | DATE_ORDER, ROW_BAL | second reader |
| 136 | 5 | date | 20 Mar 2024 | 20-03-2024 20:52:58 | DATE_ORDER, ROW_BAL | second reader |
| 137 | 5 | date | 21 Mar 2024 | 21-03-2024 07:28:07 | DATE_ORDER, ROW_BAL | second reader |
| 138 | 5 | date | 22 Mar 2024 | 22-03-2024 14:35:37 | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | date | 23 Mar 2024 | 23-03-2024 10:10:00 | DATE_ORDER, ROW_BAL | second reader |
| 140 | 5 | date | 23 Mar 2024 | 23-03-2024 10:12:18 | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | date | 23 Mar 2024 | 23-03-2024 11:51:17 | DATE_ORDER, ROW_BAL | second reader |
| 142 | 5 | date | 23 Mar 2024 | 23-03-2024 14:33:36 | DATE_ORDER, ROW_BAL | second reader |
| 143 | 5 | date | 26 Mar 2024 | 26-03-2024 13:01:48 | DATE_ORDER, ROW_BAL | second reader |
| 144 | 5 | date | 26 Mar 2024 | 26-03-2024 13:38:25 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 115, page 5, DATE_ORDER: row 115 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 158 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 157 | 1 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
