# Verification report: agami-Digital_Type1_00004-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:124, row:130.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 155 |
| Rule checks passed | 310 of 313 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Model cost | $0.0000 |
| Document SHA-256 | `580b1334f2deeb7b` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 124, page 5, ROW_BAL: row 124: 117951509 + -12402217 = 105549292, but the balance column reads 101549292 (off by -4000000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 130, page 5, ROW_BAL: row 130: 37644784 + 90091672 = 127736456, but the balance column reads -52446888 (off by -180183344)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 64903611 + movements 128380466 = 193284077, closing balance reads 9100733

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 153 | 2 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 155 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger
