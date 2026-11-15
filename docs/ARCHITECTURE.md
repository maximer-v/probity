# Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  1. Document spec  (declarative, YAML)                               │
│     schema · invariants · locale · currency · budgets · policy       │
│     probity/spec.py · examples/specs/*.yaml                           │
├──────────────────────────────────────────────────────────────────────┤
│  2. State machine  (deterministic)                                   │
│     states as an enum · transitions as a table · named guards        │
│     probity/machine.py · probity/pipeline.py                           │
├──────────────────────────────────────────────────────────────────────┤
│  3. Proposers  (non-deterministic, swappable, no authority)          │
│     text layer │ vision model (reader) │ second vision model (checker)│
│     probity/proposers/*                                               │
├──────────────────────────────────────────────────────────────────────┤
│  4. Verifiers  (deterministic, the only things that decide)          │
│     invariant engine │ grounding engine │ locale-exact parsers       │
│     probity/invariants.py · probity/grounding.py · money.py · dates.py │
├──────────────────────────────────────────────────────────────────────┤
│  5. Output                                                           │
│     typed records · certificate · replayable trace                   │
│     probity/records.py · certificate.py · trace.py                    │
└──────────────────────────────────────────────────────────────────────┘
```

The arrow of authority runs one way. Layer 3 may propose any value it likes; only layer 4
can confirm one; only layer 2 can accept a document. No proposer has access to the
invariant engine, and the `Proposer` interface has no way to express a verdict — there is
no `accept` flag and no confidence the machine will read.

## What a model is, and is not, allowed to do

This is the design in one table. Everything else follows from it.

| step | who does it | why |
|---|---|---|
| read the characters printed on the page | **a model** | this is what vision models are good at, and nothing else here can do it |
| turn `1.234,56` into 123456 minor units | **code** | a locale rule, not a judgement. A model that assumes a decimal point on a decimal-comma statement is wrong by a factor of a thousand and the output still looks reasonable |
| check `balance[i] = balance[i-1] + credit - debit` on every row | **code** | exact integer arithmetic, no tolerance |
| read a page again when a rule fails | **a different model** | the same model on the same image repeats its mistake |
| choose between two readings | **code** | the rule that failed is re-run on the second reading, and that result is the answer |
| conclude on the document | **code** | a model asked to assess a reading asserts instead of checking |

The `Proposer` interface gives a model no way to express a verdict: there is no `accept`
flag and no confidence field the machine reads.

## Design rules, and where each is enforced

Code comments refer to these by number.

| | rule | enforced by |
|---|---|---|
| **P1** | printed string to integer minor units, never a float | `money.py`: `Money` holds an `int`; `parse_amount` never constructs a float |
| **P2** | exact equality, no tolerance | `invariants.py`: every comparison goes through `balances_equal`, which is `int == int` |
| **P3** | a value is never confirmed by the rule that produced it | `records.py`: a derived field reports `INFERRED` whatever is stamped on it |
| **P4** | route on rule results, never on model confidence | `machine.py`: every guard is a named, deterministic function of the run state; a test asserts none is named for confidence |
| **P5** | a re-read is bounded, is never told the answer, and is kept only if the failed rule then passes | `repair.py`, `second_opinion.py`; budgets in the spec |
| **P6** | never invent a value | no defaults anywhere; an unreadable cell is a typed state with a reason code |
| **P7** | cheapest reader first | `spec.tier_order` with per-reader budgets; the second reader is called only where a rule failed |
| **P8** | full audit trail | `trace.py`: every guard, transition, check and model call |
| **P9** | reproducible where possible | `temperature=0`, pinned providers, content-keyed cache, replay hash |

## Why the running balance is the primary rule

The familiar check is `opening + credits - debits == closing`. It is one bit of
information about a whole document. The running balance gives one bit *per row*:

```
balance[i] == balance[i-1] + credit[i] - debit[i]        exact, integer minor units
```

That turns verification into localisation, which is what makes everything downstream
possible: the second reader can be sent to one page, a correction can be tested on one
row, and a person reviewing the result gets a line instead of a re-keying job. The error
signature also points at the cell: a wrong *amount* breaks one row, a wrong *balance*
breaks two consecutive rows.

`spec.validate()` refuses `ROW_BAL` for a layout without a running balance column
instead of silently degrading.

## The readers

| name in the spec | what it is | when it runs |
|---|---|---|
| `text_layer` | the PDF's own characters, when the file has them | first, and free; an image has none, so the machine moves on |
| `llm_small` | the first reader: a low-cost vision model transcribing each page | every scanned or photographed document |
| `checker` | the second reader: a different vision model | only for a page on which a rule failed, once per page |
| `llm_large` | an optional stronger reader | only if configured, and only when the first reader returned nothing; it never replaces an existing reading |

Images (PNG, JPEG, TIFF, WebP, BMP, GIF) are wrapped into an image-only PDF at ingest
(`images.py`), so everything after that step is identical for a PDF and a photo.

## The second reader

One model reading a page is one opinion. When a rule fails on a row there are two
explanations, and they call for opposite responses: the reader misread the row and the
document is fine, or the reader read it correctly and the document does not tie. Asking
the same model again does not separate them.

A different model can (`probity/second_opinion.py`). It is configured as `checker`,
which is not a rung of the reader ladder: it never reads a whole document. It is asked
for a page on which a rule failed (and for the page before it when the balance carried
into the failing row sits there), at most once per page, and it is given the image and
the transcription instruction only. It does not see the first reading, the rule, or the
row in question.

| the two readings of the failing row | finding | effect |
|---|---|---|
| differ, and the second satisfies the guards | `CORRECTED` | the row takes the second reading; both values, both model names and the passing rules are recorded |
| agree, and so do the figures carried into the row | `DOCUMENT_INCONSISTENT` | nothing changes; the row is reported |
| differ, and the second does not satisfy the guards | `DISPUTED` | nothing changes; both readings are reported |
| agree, but the figure carried into the row is not agreed | `DISPUTED` | nothing changes |
| cannot be paired | `UNALIGNED` | nothing changes |

The second reader supplies a candidate and never a verdict. The procedure, the six
guards that bound it, and what its conclusions do and do not establish are specified in
[METHOD.md](METHOD.md). The short version of the last point: a rule passing shows that
a reading is consistent, not that it is what is printed.

**On scans, "grounded" carries no weight.** The grounding engine compares a value with
text found on the page. For an image the only text is the first model's transcription,
so that comparison establishes nothing, and the certificate's grounding section should
be ignored for image input. The evidence on a scan is the second reader and the
arithmetic.

## The certificate

What a lender or auditor consumes. Not a score:

- document hash, spec fingerprint, framework version;
- `verification_level` — what the layout made possible at all;
- per field: value, provenance, bounding box, `verified_by`, status;
- per invariant: pass or fail, with the operands;
- flags, and the rows a human should look at;
- `conclusion`, the list of `corrections`, and every `second_opinions` entry with both
  readings side by side;
- the full transition path, the model-call log, the cost and the replay hash;
- **`not_claimed`** — the error classes this method structurally cannot catch.

A certificate that implied completeness would be worse than no certificate, which is why
that last field is not optional.
