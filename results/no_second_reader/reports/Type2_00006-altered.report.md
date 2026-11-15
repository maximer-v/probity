# Verification report: agami-Digital_Type2_00006-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:24, row:150.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 158 |
| Rule checks passed | 316 of 319 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `dfca99b42a816941` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 24, page 2, ROW_BAL: row 24: 197566991 + -49882848 = 147684143, but the balance column reads 137684143 (off by -10000000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 150, page 5, ROW_BAL: row 150: 1006042232 + 267587057 = 1273629289, but the balance column reads 738455175 (off by -535174114)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 422963741 + movements 842391103 = 1265354844, closing balance reads 720180730

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 156 | 2 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 158 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
