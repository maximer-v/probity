# Scanned examples

Two image-only statements and everything the command below wrote for each, unedited.

| file | what it is |
|---|---|
| `clean_statement.pdf` | six pages, 163 rows, ties |
| `altered_statement.pdf` | six pages, 167 rows. One debit on page 5 was changed from `93,823.71` to `23,823.71` before the pages were flattened |

```bash
cd examples/scanned
export OPENROUTER_API_KEY=...
for d in clean_statement altered_statement; do
  probity verify $d.pdf --spec ../specs/agami_type2.yaml \
      --model google/gemini-3.1-flash-lite \
      --second-model qwen/qwen3.5-flash-02-23 \
      --explain --report outputs/$d.report.md \
      --certificate outputs/$d.certificate.json \
      --trace outputs/$d.trace.jsonl --csv outputs/$d.rows.csv \
      > outputs/$d.explain.txt
done
```

| output | read it for |
|---|---|
| `outputs/*.report.md` | the conclusion, the corrections and the reported rows, in one page |
| `outputs/*.explain.txt` | every step the machine took and why |
| `outputs/*.certificate.json` | the same as data |
| `outputs/*.trace.jsonl` | one event per line |
| `outputs/*.rows.csv` | the final transactions |

The files in `outputs/` come from one such run, rendered from its cached model replies,
which is why the logs show `cached` in place of a price. The requests cost $0.050 for
the altered statement and $0.039 for the clean one.

## What the recorded run shows

**`clean_statement`: `CONFIRMED`.** The first reader put two amounts in the wrong column
(rows 151 and 155). The second reader transcribed them the other way round, the row
balance then passed, and the rows were corrected.

**`altered_statement`: `DOCUMENT_INCONSISTENT` at row 127,** which is the alteration.
Six misread rows were corrected on the way:

- rows 69, 73, 77, 78 and 135 from the second reader, whose transcription differed and
  made the row tie;
- row 148 from the third reading. The page prints a credit there, and both models
  transcribed it as a debit. They agreed with each other, so the second reader could not
  settle it. The first reader's higher-resolution transcription had it as a credit, and
  with that the row tied.

On row 127 all three readings have the same figures, and they are 70,000.00 apart from
the balance.

## Expect different details on a fresh run

The models do not return the same transcription every time. A fresh run may misread
different rows and need a different number of corrections, and could report a row that
is fine if all three readings shared a misreading. In the runs made for this repository an altered statement
was never confirmed, but that is an observation on a small sample and not a guarantee.

The statements are synthetic, derived from
[AgamiAI/Indian-Bank-Statements](https://huggingface.co/datasets/AgamiAI/Indian-Bank-Statements)
(Apache 2.0): amounts corrected so the statement ties, one amount altered in the altered
one, then every page flattened to a degraded greyscale image by
`benchmark/external/rasterise.py`.
