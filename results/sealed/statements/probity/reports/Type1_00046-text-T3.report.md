# Verification report: Type1_00046-text-T3

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:126, row:136, row:137.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 165 |
| Rule checks passed | 328 of 333 |
| Rows corrected | 30 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0423 |
| Document SHA-256 | `c3288a67c8ea8b46` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 112 | 5 | date | 28 Feb 2024 | 28-02-2024 11:19:20 | DATE_ORDER, ROW_BAL | second reader |
| 113 | 5 | date | 28 Feb 2024 | 28-02-2024 16:26:01 | DATE_ORDER, ROW_BAL | second reader |
| 114 | 5 | date | 28 Feb 2024 | 28-02-2024 23:59:00 | DATE_ORDER, ROW_BAL | second reader |
| 115 | 5 | date | 29 Feb 2024 | 29-02-2024 19:36:04 | DATE_ORDER, ROW_BAL | second reader |
| 116 | 5 | date | 01 Mar 2024 | 01-03-2024 08:39:58 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 5 | date | 02 Mar 2024 | 02-03-2024 13:11:56 | DATE_ORDER, ROW_BAL | second reader |
| 118 | 5 | date | 02 Mar 2024 | 02-03-2024 19:43:28 | DATE_ORDER, ROW_BAL | second reader |
| 119 | 5 | date | 02 Mar 2024 | 02-03-2024 20:53:24 | DATE_ORDER, ROW_BAL | second reader |
| 120 | 5 | date | 04 Mar 2024 | 04-03-2024 14:44:19 | DATE_ORDER, ROW_BAL | second reader |
| 121 | 5 | date | 05 Mar 2024 | 05-03-2024 10:00:00 | DATE_ORDER, ROW_BAL | second reader |
| 122 | 5 | date | 05 Mar 2024 | 05-03-2024 12:07:51 | DATE_ORDER, ROW_BAL | second reader |
| 123 | 5 | date | 05 Mar 2024 | 05-03-2024 15:11:40 | DATE_ORDER, ROW_BAL | second reader |
| 124 | 5 | date | 05 Mar 2024 | 05-03-2024 21:07:23 | DATE_ORDER, ROW_BAL | second reader |
| 125 | 5 | date | 05 Mar 2024 | 05-03-2024 21:16:15 | DATE_ORDER, ROW_BAL | second reader |
| 127 | 5 | date | 06 Mar 2024 | 06-03-2024 10:27:37 | DATE_ORDER, ROW_BAL | second reader |
| 128 | 5 | date | 06 Mar 2024 | 06-03-2024 15:10:00 | DATE_ORDER, ROW_BAL | second reader |
| 129 | 5 | date | 06 Mar 2024 | 06-03-2024 16:40:28 | DATE_ORDER, ROW_BAL | second reader |
| 130 | 5 | date | 07 Mar 2024 | 07-03-2024 11:38:51 | DATE_ORDER, ROW_BAL | second reader |
| 131 | 5 | date | 09 Mar 2024 | 09-03-2024 15:46:18 | DATE_ORDER, ROW_BAL | second reader |
| 132 | 5 | date | 09 Mar 2024 | 09-03-2024 15:50:42 | DATE_ORDER, ROW_BAL | second reader |
| 133 | 5 | date | 12 Mar 2024 | 12-03-2024 07:33:41 | DATE_ORDER, ROW_BAL | second reader |
| 134 | 5 | date | 12 Mar 2024 | 12-03-2024 09:28:07 | DATE_ORDER, ROW_BAL | second reader |
| 135 | 5 | date | 13 Mar 2024 | 13-03-2024 15:55:49 | DATE_ORDER, ROW_BAL | second reader |
| 138 | 5 | date | 14 Mar 2024 | 14-03-2024 07:25:18 | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | date | 15 Mar 2024 | 15-03-2024 10:13:07 | DATE_ORDER, ROW_BAL | second reader |
| 140 | 5 | date | 15 Mar 2024 | 15-03-2024 19:19:09 | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | date | 16 Mar 2024 | 16-03-2024 08:14:05 | DATE_ORDER, ROW_BAL | second reader |
| 142 | 5 | date | 18 Mar 2024 | 18-03-2024 16:13:18 | DATE_ORDER, ROW_BAL | second reader |
| 143 | 5 | date | 19 Mar 2024 | 19-03-2024 13:18:28 | DATE_ORDER, ROW_BAL | second reader |
| 144 | 5 | date | 19 Mar 2024 | 19-03-2024 15:31:44 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 126, page 5, DATE_ORDER: row 126 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 136, page 5, ROW_BAL: row 136: 37904127 + 69970836 = 107874963, but the balance column reads 107874933 (off by -30)
- row 136, page 5, DATE_ORDER: row 136 has no readable date
  - second look (UNALIGNED): the second reading of page 5 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 137, page 5, ROW_BAL: row 137: 107874933 + 169814270 = 277689203, but the balance column reads 277689233 (off by 30)
- row 137, page 5, DATE_ORDER: row 137 has no readable date
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 14 Mar 2024 / (blank) / Rs. 1,698,142.70 / Rs. 2,776,892.33; second reader 14-03-2024 06:44:42 / (blank) / Rs. 1,698,142.70 / Rs. 2,776,892.33 (date / debit / credit / balance)

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 163 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 162 | 3 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
