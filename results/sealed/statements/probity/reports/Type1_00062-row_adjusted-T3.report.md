# Verification report: Type1_00062-row_adjusted-T3

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:63, row:64.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 164 |
| Rule checks passed | 327 of 331 |
| Rows corrected | 31 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0463 |
| Document SHA-256 | `e45ef5a21200b3fb` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 45 | 3 | date | 25 Jan 2024 | 25-01-2024 23:07:00 | DATE_ORDER, ROW_BAL | second reader |
| 46 | 3 | date | 27 Jan 2024 | 27-01-2024 14:17:21 | DATE_ORDER, ROW_BAL | second reader |
| 47 | 3 | date | 27 Jan 2024 | 27-01-2024 18:58:03 | DATE_ORDER, ROW_BAL | second reader |
| 48 | 3 | date | 27 Jan 2024 | 27-01-2024 20:07:19 | DATE_ORDER, ROW_BAL | second reader |
| 49 | 3 | date | 29 Jan 2024 | 29-01-2024 10:06:52 | DATE_ORDER, ROW_BAL | second reader |
| 50 | 3 | date | 29 Jan 2024 | 29-01-2024 10:42:31 | DATE_ORDER, ROW_BAL | second reader |
| 51 | 3 | date | 29 Jan 2024 | 29-01-2024 19:59:08 | DATE_ORDER, ROW_BAL | second reader |
| 52 | 3 | date | 31 Jan 2024 | 31-01-2024 17:53:59 | DATE_ORDER, ROW_BAL | second reader |
| 53 | 3 | date | 31 Jan 2024 | 31-01-2024 19:26:03 | DATE_ORDER, ROW_BAL | second reader |
| 54 | 3 | date | 01 Feb 2024 | 01-02-2024 07:55:57 | DATE_ORDER, ROW_BAL | second reader |
| 55 | 3 | date | 02 Feb 2024 | 02-02-2024 09:26:00 | DATE_ORDER, ROW_BAL | second reader |
| 56 | 3 | date | 02 Feb 2024 | 02-02-2024 14:17:54 | DATE_ORDER, ROW_BAL | second reader |
| 57 | 3 | date | 02 Feb 2024 | 02-02-2024 16:48:02 | DATE_ORDER, ROW_BAL | second reader |
| 58 | 3 | date | 03 Feb 2024 | 03-02-2024 12:22:25 | DATE_ORDER, ROW_BAL | second reader |
| 59 | 3 | date | 03 Feb 2024 | 03-02-2024 16:44:19 | DATE_ORDER, ROW_BAL | second reader |
| 60 | 3 | date | 03 Feb 2024 | 03-02-2024 20:43:50 | DATE_ORDER, ROW_BAL | second reader |
| 61 | 3 | date | 03 Feb 2024 | 03-02-2024 21:41:31 | DATE_ORDER, ROW_BAL | second reader |
| 62 | 3 | date | 05 Feb 2024 | 05-02-2024 06:27:26 | DATE_ORDER, ROW_BAL | second reader |
| 65 | 3 | date | 05 Feb 2024 | 05-02-2024 14:16:07 | DATE_ORDER, ROW_BAL | second reader |
| 66 | 3 | date | 05 Feb 2024 | 05-02-2024 15:29:19 | DATE_ORDER, ROW_BAL | second reader |
| 67 | 3 | date | 05 Feb 2024 | 05-02-2024 15:37:08 | DATE_ORDER, ROW_BAL | second reader |
| 68 | 3 | date | 06 Feb 2024 | 06-02-2024 08:29:29 | DATE_ORDER, ROW_BAL | second reader |
| 69 | 3 | date | 06 Feb 2024 | 06-02-2024 13:25:52 | DATE_ORDER, ROW_BAL | second reader |
| 70 | 3 | date | 07 Feb 2024 | 07-02-2024 07:15:42 | DATE_ORDER, ROW_BAL | second reader |
| 71 | 3 | date | 07 Feb 2024 | 07-02-2024 12:35:35 | DATE_ORDER, ROW_BAL | second reader |
| 72 | 3 | date | 07 Feb 2024 | 07-02-2024 15:50:20 | DATE_ORDER, ROW_BAL | second reader |
| 73 | 3 | date | 07 Feb 2024 | 07-02-2024 23:30:00 | DATE_ORDER, ROW_BAL | second reader |
| 74 | 3 | date | 09 Feb 2024 | 09-02-2024 06:48:03 | DATE_ORDER, ROW_BAL | second reader |
| 75 | 3 | date | 09 Feb 2024 | 09-02-2024 09:46:52 | DATE_ORDER, ROW_BAL | second reader |
| 76 | 3 | date | 12 Feb 2024 | 12-02-2024 06:57:37 | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | date | 12 Feb 2024 | 12-02-2024 11:18:44 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 63, page 3, ROW_BAL: row 63: 203034201 + -178691567 = 24342634, but the balance column reads 24342636 (off by 2)
- row 63, page 3, DATE_ORDER: row 63 has no readable date
  - second look (UNALIGNED): the second reading of page 3 has 33 rows against 33, and no row in it could be shown to be the row in question
- row 64, page 3, ROW_BAL: row 64: 24342636 + 199890257 = 224232893, but the balance column reads 224232891 (off by -2)
- row 64, page 3, DATE_ORDER: row 64 has no readable date
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 05 Feb 2024 / (blank) / Rs. 1,998,902.57 / Rs. 2,242,328.91; second reader 05-02-2024 10:48:07 / (blank) / Rs. 1,998,902.57 / Rs. 2,242,328.91 (date / debit / credit / balance)

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 162 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 162 | 2 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
