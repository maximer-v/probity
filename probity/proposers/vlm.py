"""A vision model as a proposer: it transcribes, the framework does the arithmetic.

The division of labour is the point, and it is enforced by what the model is asked for:

* the model returns **the characters it sees**, exactly as printed — ``"1.234,56"``,
  ``"(250,00)"``, ``"1,234.56 CR"``;
* the model also returns what it *believes* the value is in minor units;
* and the framework parses the printed characters itself, with its own locale-exact
  parser, and **ignores the model's integer except to check it**.

That check is worth more than it looks. A model that reads the digits correctly but
mis-converts the locale — reading ``1.234,56`` as 1.23 because it assumed a decimal
point — disagrees with its own transcription, and the disagreement is caught before the
value is ever used. The model is never asked to add anything up.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

from ..dates import parse_date_result
from ..grounding import BBox, DocumentIndex, PageIndex, Token
from ..invariants import Location
from ..money import parse_amount_result
from ..openrouter import OUTPUT_CEILING, ModelSpec, OpenRouterClient, image_message
from ..records import Field, Provenance, Row, Statement
from ..trace import ModelCall, sha256_text
from .base import Document, Proposal, Proposer

#: What the model must return. Deliberately *not* a finished statement: there is no
#: "reconciled" field and no totals, because this tier is a reader, not a judge.
TRANSCRIPTION_SCHEMA: dict[str, Any] = {
    "name": "statement_transcription",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["account_id", "period_start", "period_end", "opening_balance",
                     "closing_balance", "tx_count", "rows", "page_carry_forward"],
        "properties": {
            "account_id": {"type": "string", "description": "exactly as printed"},
            "period_start": {"type": "string", "description": "exactly as printed"},
            "period_end": {"type": "string", "description": "exactly as printed"},
            "opening_balance": {"type": "string", "description": "exactly as printed"},
            "closing_balance": {"type": "string", "description": "exactly as printed"},
            "tx_count": {"type": "string",
                         "description": "the declared transaction count as printed, or empty"},
            "page_carry_forward": {
                "type": "array",
                "description": "subtotal lines such as 'Saldo que pasa' or 'Carried "
                               "forward' printed at the foot of a page. Empty if the "
                               "statement has none.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["page", "balance"],
                    "properties": {
                        "page": {"type": "integer"},
                        "balance": {"type": "string",
                                    "description": "exactly as printed"},
                    },
                },
            },
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["page", "date", "description", "debit", "credit",
                                 "balance", "balance_minor_units", "amount_column"],
                    "properties": {
                        "page": {"type": "integer"},
                        "date": {"type": "string", "description": "exactly as printed"},
                        "description": {"type": "string"},
                        "debit": {"type": "string",
                                  "description": "money out, exactly as printed, or empty"},
                        "credit": {"type": "string",
                                   "description": "money in, exactly as printed, or empty"},
                        # Asked for separately because getting the digits right and
                        # putting them on the correct side are different skills, and the
                        # model is reliable at one and not the other: on this corpus it
                        # transcribes amounts essentially perfectly and assigns one or
                        # two rows in 160 to the wrong column. A flipped direction moves
                        # the balance by twice the amount, so it is the costliest error
                        # the reader makes. This asks what the column is *called* on the
                        # page, which is a different question from which field to use.
                        "amount_column": {
                            "type": "string",
                            "description": "the exact column heading printed above this "
                                           "row's amount, copied from the table header "
                                           "(for example 'Debit', 'Credit', 'Withdrawal', "
                                           "'Deposit', 'Amount'), plus any Cr/Dr marker "
                                           "printed on the row itself. Empty if the row "
                                           "has no amount."},
                        "balance": {"type": "string",
                                    "description": "running balance, exactly as printed"},
                        "balance_minor_units": {
                            "type": "integer",
                            "description": "what you believe the balance is in minor units "
                                           "(cents). This is checked against the printed "
                                           "characters, not trusted."},
                    },
                },
            },
        },
    },
}

INSTRUCTION = """Transcribe this bank statement.

Report every value **exactly as it is printed**, character for character. Do not convert,
normalise, reformat or correct anything:

- an amount printed `1.234,56` is reported as `1.234,56`, not `1234.56`
- an amount printed `(250,00)` keeps its brackets
- an amount printed `1,234.56 CR` keeps the `CR`
- a date printed `18/03/2026` keeps that form
- an empty cell is reported as an empty string

Transcribe every transaction row that appears, in the order printed, and record which
page each one is on.

If a page ends with a carry-forward or subtotal line (`Saldo que pasa`, `Carried
forward`, `Suma y sigue` and similar), report it under `page_carry_forward`. It is not a
transaction and must not appear among the rows.

Do not compute totals. Do not check whether the statement balances. Do not fix anything
that looks wrong — if a figure looks inconsistent, transcribe it as printed anyway.
"""


#: One page render at a time, process-wide.
_RENDER_LOCK = threading.Lock()


@dataclass
class VLMProposer(Proposer):
    """Reads page images with a vision model; the framework parses what it returns."""

    client: OpenRouterClient = None            # type: ignore[assignment]
    model: ModelSpec = None                    # type: ignore[assignment]
    tier: str = "llm_small"
    cost_class: int = 3
    bills_usd: bool = True
    supports_regions: bool = True
    dpi: int = 170
    #: Room for a full page of rows in one reply. See ``OUTPUT_CEILING``.
    max_tokens: int = OUTPUT_CEILING
    #: Pages per request. 0 sends the whole document in one call.
    pages_per_call: int = 0
    #: Resolution for a re-read, when a check has failed and the machine is sending the
    #: model back to a page.
    #:
    #: A re-read at the reading resolution is the same question asked twice: identical
    #: image, identical prompt, temperature zero, and so identically the same misreading.
    #: Six of eleven clean documents were refused that way -- the failing row correctly
    #: named, the re-read confirming the error rather than correcting it.
    #:
    #: 400 is not a tuned number; it is simply well above the reading resolution.
    repair_dpi: int = 400
    #: Extra text appended to the instruction for this model only. Some providers refuse
    #: a structured-output request unless the prompt contains the word "json"; this is
    #: where that goes, so the instruction every other model sees stays byte-identical.
    prompt_suffix: str = ""
    model_calls: list[ModelCall] = dc_field(default_factory=list)

    def available(self) -> tuple[bool, str]:
        if self.client is None or self.model is None:
            return False, "no OpenRouter client or model configured"
        return True, f"{self.model.model}"

    def _page_images(self, doc: Document, dpi: float | None = None) -> list[str]:
        # The PDF renderer is not safe to call from several threads at once.
        with _RENDER_LOCK:
            return self._render_pages(doc, dpi)

    def _render_pages(self, doc: Document, dpi: float | None = None) -> list[str]:
        """Page images at ``dpi``, rendered fresh when a resolution is asked for.

        Pre-rendered images supplied with the document are used for the first read, but a
        re-read that asks for a specific resolution must not be handed them: the whole
        point of a re-read is that the input is different.
        """
        if dpi is None and doc.page_images:
            return [doc.page_images[k] for k in sorted(doc.page_images)]
        import pypdfium2 as pdfium

        want = dpi or self.dpi
        # Resolution is expressed per inch of paper, but a PDF's "points" cannot be
        # trusted to be 1/72 inch. A scanned statement is one big image whose page box
        # is stated in pixels (2481 x 3508 for A4 at 300 dpi), so scaling by dpi/72
        # would render it at 5855 px wide and cost a fortune for no extra detail.
        # Normalise against the long edge of A4 instead: identical to dpi/72 for an
        # ordinary page, correct for a page whose units are really pixels.
        target_long_edge = want / 72.0 * 841.89
        out, pdf = [], pdfium.PdfDocument(doc.pdf_path)
        # Rendered pages are working files. They go to the system temp directory, keyed
        # by the document's path, size and modification time, and never next to the
        # document: a tool pointed at a folder of statements must not fill it.
        import hashlib
        import tempfile
        src = Path(doc.pdf_path).resolve()
        st = src.stat()
        key = hashlib.sha256(f"{src}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:16]
        work_dir = Path(tempfile.gettempdir()) / "probity-pages" / key
        work_dir.mkdir(parents=True, exist_ok=True)
        work = work_dir / src.stem
        for i in range(len(pdf)):
            page = pdf[i]
            long_edge = max(page.get_width(), page.get_height())
            scale = target_long_edge / long_edge if long_edge else want / 72.0
            p = Path(f"{work}.vlm.{int(want)}.p{i + 1}.png")
            if not p.exists():
                page.render(scale=scale).to_pil().save(p)
            out.append(str(p))
        return out

    def propose(self, doc: Document, spec, *, region: Location | None = None,
                previous: Statement | None = None) -> Proposal:
        is_reread = region is not None and region.page is not None
        images = self._page_images(doc, dpi=self.repair_dpi if is_reread else None)
        prompt = INSTRUCTION + f"\n{_locale_note(spec)}" + self.prompt_suffix

        # A region re-read: the machine has found a row that does not tie out and is
        # sending the model back to look at it again. Only that row's page is shown, and
        # the previous reading handed over has already had every amount stripped from it
        # by `redact_for_repair`, so there is no target to reproduce. The model is asked
        # to read the page, not to make anything agree.
        reindex: dict[int, int] | None = None
        if region is not None and region.page is not None:
            page_no = int(region.page)
            if 1 <= page_no <= len(images):
                images = [images[page_no - 1]]
                prompt += (
                    f"\n\nThis is page {page_no} of the statement. Transcribe every "
                    f"transaction row printed on it, in order, and set `page` to "
                    f"{page_no} on each. Read what is printed; do not adjust anything "
                    f"to make a total agree."
                )
                reindex = {page_no: _first_index_on_page(previous, page_no)}

        # How many pages go in one request. Reading a six-page, 162-row statement in a
        # single call asks for about 9,500 tokens of JSON in one unbroken stretch, and
        # accuracy decays along it even though the row *count* comes back right. Splitting
        # the document is the framework's decision about how to use the model, which is
        # part of what the framework is for.
        chunks = ([images] if self.pages_per_call <= 0 else
                  [images[i:i + self.pages_per_call]
                   for i in range(0, len(images), self.pages_per_call)])

        calls: list[ModelCall] = []
        merged: dict[str, Any] | None = None
        truncated = False
        unparsed: list[int] = []
        for n, chunk in enumerate(chunks, start=1):
            first_page = (n - 1) * max(self.pages_per_call, 1) + 1
            note = ("" if len(chunks) == 1 else
                    f"\nThese are pages {first_page} to {first_page + len(chunk) - 1} of "
                    f"{len(images)}. Number the `page` field accordingly, and transcribe "
                    f"only the rows printed on these pages.")
            resp = self.client.chat(self.model, image_message(prompt + note, chunk),
                                    json_schema=TRANSCRIPTION_SCHEMA,
                                    max_tokens=self.max_tokens,
                                    purpose=f"transcribe:{first_page}")
            calls.append(ModelCall(
                tier=self.tier, model=f"llm:{self.model.model}", provider=resp.provider,
                params={"temperature": 0.0, "schema": "statement_transcription",
                        "pages": f"{first_page}-{first_page + len(chunk) - 1}"},
                prompt_sha256=sha256_text(prompt + note),
                output_sha256=sha256_text(resp.text or ""),
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                cost_usd=resp.cost_usd, latency_ms=resp.latency_ms, cached=resp.cached,
                purpose="transcribe"))
            if (resp.finish_reason or "").lower() in {"length", "max_tokens"}:
                truncated = True
                break
            part = _parse(resp.text)
            if part is None:
                # Skipping a page whose reply did not parse would hand back a document
                # that is silently missing that page. Its rows may net to zero, so the
                # arithmetic cannot be relied on to notice. Record it and refuse below.
                unparsed.append(first_page)
                continue
            if merged is None:
                merged = part
            else:
                merged.setdefault("rows", []).extend(part.get("rows") or [])
                merged.setdefault("page_carry_forward", []).extend(
                    part.get("page_carry_forward") or [])
                # Header fields are printed on the first page; later chunks cannot see
                # them and must not be allowed to blank what the first chunk read.
                for key in ("account_id", "period_start", "period_end",
                            "opening_balance", "closing_balance", "tx_count"):
                    if not merged.get(key) and part.get(key):
                        merged[key] = part[key]

        resp_text_present = merged is not None
        self.model_calls = calls

        # A reply cut off at the token ceiling is the one failure that does not look like
        # a failure. The JSON is repaired by `_parse` picking the outermost braces, the
        # rows that did arrive are all individually correct, and the result is a document
        # that is simply missing its tail. Nothing downstream can tell that apart from a
        # statement that really ended there, so it has to be refused here, by name.
        if truncated:
            empty = Statement(doc_id=doc.doc_id, currency=spec.currency_default)
            return Proposal(
                statement=empty, index=DocumentIndex(sources=("llm",)),
                tier=self.tier, model_calls=calls,
                parse_errors={"response:TRUNCATED": 1},
                notes=[f"the model stopped at the {self.max_tokens}-token ceiling, so the "
                       f"transcription is incomplete and cannot be trusted as a whole "
                       f"document"])

        if unparsed and len(chunks) > 1:
            empty = Statement(doc_id=doc.doc_id, currency=spec.currency_default)
            return Proposal(
                statement=empty, index=DocumentIndex(sources=("llm",)),
                tier=self.tier, model_calls=calls,
                parse_errors={"response:PAGE_NOT_JSON": len(unparsed)},
                notes=[f"the reply for page(s) starting at {unparsed} was not valid JSON, "
                       f"so the transcription is missing those pages and cannot be "
                       f"presented as the whole document"])

        data = merged
        if data is None:
            empty = Statement(doc_id=doc.doc_id, currency=spec.currency_default)
            return Proposal(statement=empty, index=DocumentIndex(sources=("llm",)),
                            tier=self.tier, model_calls=calls,
                            parse_errors={"response:NOT_JSON": 1},
                            notes=["the model's reply was not valid JSON"])

        proposal = _build(data, spec, doc, images, self.tier,
                          source=f"llm:{self.model.model}", reindex=reindex)
        proposal.model_calls = calls
        return proposal


#: Column headings and row markers that name a side, in the languages these specs cover.
#: Only unambiguous words appear: "amount" and "importe" name a column that carries both
#: directions, so they say nothing about the side and are deliberately absent.
#: Plurals are listed explicitly: matching is on whole tokens, so "withdrawals" does
#: not match "withdrawal", and a missing plural silently turns a heading that names both
#: directions ("Deposits / Withdrawals") into one that appears to name only one.
_DEBIT_WORDS = ("debit", "debits", "débito", "débitos", "debito", "debitos",
                "withdrawal", "withdrawals", "withdrawn", "paid out", "money out",
                "cargo", "cargos", "saída", "saídas", "saida", "saidas",
                "retiro", "retiros", "dr")
_CREDIT_WORDS = ("credit", "credits", "crédito", "créditos", "credito", "creditos",
                 "deposit", "deposits", "depósito", "depósitos", "paid in", "money in",
                 "abono", "abonos", "entrada", "entradas",
                 "ingreso", "ingresos", "cr")


def _side_from_column(label: str) -> str | None:
    """Which side a printed column heading or Cr/Dr marker names, if it names one."""
    # Every character that is not a letter or a digit becomes a space before tokenising.
    # Splitting on whitespace alone left punctuation glued to the word, so "Debit /
    # Credit:" tokenised as {"debit", "credit:"} and read as debit, and "Debit/ Credit"
    # as {"debit/", "credit"} and read as credit. Both headings name both directions and
    # must be silence.
    text = " ".join("".join(c if c.isalnum() else " " for c in label.lower()).split())
    if not text:
        return None
    tokens = set(text.split())
    debit = any(w in tokens for w in _DEBIT_WORDS) or any(
        w in text for w in _DEBIT_WORDS if " " in w)
    credit = any(w in tokens for w in _CREDIT_WORDS) or any(
        w in text for w in _CREDIT_WORDS if " " in w)
    if debit == credit:
        # Either neither, or a heading that names both ("Debit / Credit"). Both are
        # silence rather than evidence, and silence must not move a value.
        return None
    return "debit" if debit else "credit"


def _locale_note(spec) -> str:
    loc = spec.locale
    return (f"This statement is in locale {spec.locale_name}: the decimal separator is "
            f"'{loc.decimal_sep}' and the thousands separator is '{loc.thousands_sep}'. "
            f"Report the characters as printed; the conversion is not your job.")


def _parse(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        text = text.split("\n", 1)[1] if "\n" in text else text
    for candidate in (text, text[text.find("{"): text.rfind("}") + 1] if "{" in text else ""):
        if not candidate:
            continue
        try:
            out = json.loads(candidate)
            if isinstance(out, dict):
                return out
        except json.JSONDecodeError:
            continue
    return None


def _first_index_on_page(previous: Statement | None, page: int) -> int:
    """The document row index the given page starts at, read off the previous reading.

    A region re-read sees one page, so the model numbers its rows from zero. Patching
    them back requires the document's own numbering, and the only record of which
    indices live on which page is the reading being repaired. ``redact_for_repair`` has
    removed that reading's amounts but kept its structure, which is exactly what is
    needed here and nothing more.
    """
    if previous is None:
        return 0
    on_page = [r.index for r in previous.rows if r.page == page]
    return min(on_page) if on_page else 0


def _build(data: dict[str, Any], spec, doc: Document, images: list[str], tier: str,
           *, source: str, reindex: dict[int, int] | None = None) -> Proposal:
    """Parse the model's *printed characters* with our own parser, and check its arithmetic.

    Two independent things come back from the model for each balance: the characters and
    the model's own integer. We parse the characters; the integer is only ever used to
    detect that the model contradicted itself.
    """
    st = Statement(doc_id=doc.doc_id, currency=spec.currency_default,
                   page_count=max(1, len(images)))
    errors: dict[str, int] = {}
    notes: list[str] = []

    def bump(code: str) -> None:
        errors[code] = errors.get(code, 0) + 1

    # The index is the model's own transcription. Grounding against it is a consistency
    # check, not a presence check on the pixels, and the certificate's provenance says
    # so by recording the value as coming from a model rather than a text layer.
    index = DocumentIndex(sources=("llm",))
    page_tokens: dict[int, list[Token]] = {}

    def remember(page: int, text: str) -> BBox:
        box = BBox(page, 0.0, 0.0, 595.0, 842.0)
        for word in str(text).split():
            page_tokens.setdefault(page, []).append(Token(word, box, "llm"))
        return box

    def money_field(name: str, raw: Any, page: int, claimed: Any = None) -> Field:
        raw = "" if raw is None else str(raw).strip()
        box = remember(page, raw)
        if not raw:
            return Field(name)
        value, err = parse_amount_result(raw, spec.locale, spec.currency_default,
                                         allow_blank=False)
        if err:
            bump(f"{name}:{err}")
        f = Field(name=name, raw=raw, value=value, provenance=Provenance.LLM,
                  bbox=box, source_model=source, error_code=err)
        if name == "debit" and value is not None and value.minor < 0:
            f.value = -value
        if (claimed is not None and value is not None
                and isinstance(claimed, int) and claimed != value.minor):
            # The model read the characters one way and converted them another. We keep
            # our own reading of the characters and record the contradiction.
            f.error_code = "MODEL_SELF_CONTRADICTION"
            f.grounding_detail = {"model_claimed_minor": claimed,
                                  "parsed_from_printed": value.minor}
            bump(f"{name}:MODEL_SELF_CONTRADICTION")
        return f

    for name, key in (("opening_balance", "opening_balance"),
                      ("closing_balance", "closing_balance")):
        setattr(st.header, name, money_field(name, data.get(key), 1))

    for name, key in (("period_start", "period_start"), ("period_end", "period_end")):
        raw = str(data.get(key) or "").strip()
        box = remember(1, raw)
        value, err = parse_date_result(raw, spec.header_date_fmt) if raw else (None, "EMPTY")
        if value is None and raw and spec.header_date_fmt != spec.date_fmt:
            value, err = parse_date_result(raw, spec.date_fmt)
        if err:
            bump(f"{name}:{err}")
        setattr(st.header, name, Field(name=name, raw=raw, value=value,
                                       provenance=Provenance.LLM, bbox=box,
                                       source_model=source, error_code=err))

    account = str(data.get("account_id") or "").strip()
    st.header.account_id = Field("account_id", account, account or None,
                                 Provenance.LLM, remember(1, account), source)
    count_raw = str(data.get("tx_count") or "").strip()
    digits = "".join(c for c in count_raw if c.isdigit())
    st.header.tx_count = Field("tx_count", count_raw, int(digits) if digits else None,
                               Provenance.LLM, remember(1, count_raw), source)
    st.header.currency = Field("currency", spec.currency_default,
                               spec.currency_default, Provenance.LLM)

    n_pages = max(1, len(images))
    # On a region re-read only one page was shown, so the model's `page` field is taken
    # as that page and its row numbering is shifted onto the document's.
    only_page = next(iter(reindex)) if reindex else None
    seen_on_page = 0
    for i, r in enumerate(data.get("rows") or []):
        page = only_page if only_page is not None else int(r.get("page") or 1)
        if only_page is not None:
            i = reindex[only_page] + seen_on_page
            seen_on_page += 1
        elif not 1 <= page <= n_pages:
            # A row placed on a page the document does not have cannot be grounded
            # against anything, and silently clamping it would invent a location.
            bump("row:PAGE_OUT_OF_RANGE")
            notes.append(f"row {i} claims page {page}; the document has {n_pages}")
            continue
        row = Row(index=i, page=page)

        raw_date = str(r.get("date") or "").strip()
        box = remember(page, raw_date)
        value, err = parse_date_result(raw_date, spec.date_fmt) if raw_date else (None, "EMPTY")
        if err:
            bump(f"date:{err}")
        row.date = Field("date", raw_date, value, Provenance.LLM, box, source,
                         error_code=err)

        desc = str(r.get("description") or "").strip()
        row.description = Field("description", desc, desc or None, Provenance.LLM,
                                remember(page, desc), source)

        debit_raw, credit_raw = r.get("debit"), r.get("credit")

        # The model reports the printed column heading as well as choosing a JSON key.
        # When the two disagree we do NOT pick a winner. Both come from the same model
        # in the same response, so neither is evidence about the other, and swapping
        # the value on the heading's word can rescue a genuinely inconsistent document
        # into a balanced one: a direction flip moves the chain by twice the amount, so
        # a wrong swap is the most dangerous edit available. The contradiction is an
        # unresolved read, which is a typed failure (P6). It stamps both amount cells so
        # the row cannot be accepted as read, and the repair loop re-reads the region.
        # Resolving it properly needs the amount's x-position against the heading's,
        # which is a second source of evidence a transcription does not carry.
        side = _side_from_column(str(r.get("amount_column") or ""))
        contradiction: str | None = None
        if side is not None:
            placed = ("debit" if str(debit_raw or "").strip()
                      else "credit" if str(credit_raw or "").strip() else None)
            if placed is not None and placed != side:
                contradiction = "COLUMN_CONTRADICTS_FIELD"
                bump("row:COLUMN_CONTRADICTS_FIELD")
                notes.append(
                    f"row {i}: value placed in {placed} but the column is reported as "
                    f"{str(r.get('amount_column')).strip()!r}; direction unresolved")

        row.debit = money_field("debit", debit_raw, page)
        row.credit = money_field("credit", credit_raw, page)
        row.balance = money_field("balance", r.get("balance"), page,
                                  claimed=r.get("balance_minor_units"))
        if contradiction is not None:
            # Stamp the side that carries the value; an unresolved direction makes the
            # amount unusable, not merely suspicious.
            for cell in (row.debit, row.credit):
                if (cell.raw or "").strip():
                    cell.error_code = contradiction
        st.rows.append(row)

    for cf in data.get("page_carry_forward") or []:
        page = int(cf.get("page") or 1)
        st.carried_forward[page] = money_field("carried_forward", cf.get("balance"), page)

    for page, tokens in page_tokens.items():
        idx = PageIndex(page=page, width=595.0, height=842.0)
        idx.tokens = tokens
        index.pages[page] = idx

    if not st.rows:
        notes.append("the model returned no transaction rows")
    return Proposal(statement=st, index=index, tier=tier,
                    parse_errors=errors, notes=notes)
