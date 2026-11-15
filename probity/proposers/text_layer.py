"""Tier 0: the PDF's own text layer. Deterministic, free, exact when it exists.

Most statements a customer downloads from online banking are digital PDFs that already
carry every character and its coordinates. Reading those with a model is paying for a
guess at information the file states outright, which is why this tier runs first and,
on digital documents, usually last.

The implementation that this framework was written in reaction to searched the raw PDF
bytes with a regular expression. Almost every real bank PDF compresses its text streams,
so that approach finds nothing on real files and then invents rows to fill the gap. Here
the file is parsed properly, and finding nothing is a reported state, not a placeholder.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from ..dates import parse_date_result
from ..grounding import BBox, DocumentIndex, PageIndex, Token
from ..invariants import Location, Scope
from ..money import normalise_numeric_text, parse_amount_result
from ..records import Field, Header, Provenance, Row, Statement
from .base import Document, Proposal, Proposer

# Column header lexicon. Adding a language means adding words here, not code.
LEXICON: dict[str, tuple[str, ...]] = {
    "date": ("fecha", "data", "date", "fec.", "f. valor", "f.valor", "datum", "dt"),
    "description": ("descripcion", "descripción", "concepto", "detalle", "descrição",
                    "historico", "histórico", "description", "details", "narrative",
                    "referencia", "operacion", "operación", "lancamento", "lançamento"),
    "debit": ("debito", "débito", "debit", "cargo", "cargos", "debe", "saida", "saída",
              "retiro", "retiros", "withdrawal", "withdrawals", "pagos",
              "paid out", "money out", "egreso", "egresos"),
    "credit": ("credito", "crédito", "credit", "abono", "abonos", "haber", "entrada",
               "entradas", "deposito", "depósito", "deposit", "deposits", "depositos",
               "paid in", "money in", "ingreso", "ingresos"),
    "balance": ("saldo", "balance", "saldos", "saldo actual", "running balance"),
    "amount": ("importe", "monto", "valor", "amount", "montante"),
    # A separate indicator column that says which way a single amount column goes.
    "direction": ("cr/dr", "dr/cr", "crdr", "drcr", "tipo", "type", "d/c", "c/d",
                  "debcred", "naturaleza"),
}

#: Markers that appear in a ``direction`` cell. Right-hand side means money out.
DIRECTION_DEBIT = ("DR", "D", "DB", "DEB", "DEBIT", "CARGO", "W")
DIRECTION_CREDIT = ("CR", "C", "CRED", "CREDIT", "ABONO", "DEP")

HEADER_LABELS: dict[str, tuple[str, ...]] = {
    "opening_balance": ("saldo anterior", "saldo inicial", "saldo anterior:", "opening balance",
                        "balance anterior", "saldo precedente", "saldo inicial:",
                        "saldo anterior ", "previous balance", "saldo antecedente",
                        # Printed at the head of the transaction table in much of Asia,
                        # the UK and the Commonwealth rather than in a summary block.
                        "balance brought forward", "brought forward", "balance b/f",
                        "saldo que viene", "saldo inicial del periodo"),
    "closing_balance": ("saldo final", "saldo actual", "closing balance", "saldo final:",
                        "nuevo saldo", "saldo disponible", "ending balance", "saldo atual"),
    "period_start": ("periodo desde", "desde", "período desde", "searched by from",
                     "from", "period", "periodo:",
                     "fecha inicial", "data inicial"),
    "period_end": ("periodo hasta", "hasta", "período hasta", "to", "fecha final",
                   "data final", "até"),
    "account_id": ("cuenta", "cuenta no", "numero de cuenta", "número de cuenta", "account",
                   "account number", "conta", "n° cuenta", "no. cuenta", "iban"),
    "tx_count": ("movimientos", "total movimientos", "numero de movimientos",
                 "transactions", "total transactions", "cantidad de movimientos",
                 "nro movimientos", "transacciones"),
    "currency": ("moneda", "divisa", "currency", "moeda"),
}

_AMOUNT_RE = re.compile(r"^[\s(]*[-+]?[\d.,   ]*\d[\d.,   ]*[-)]?\s*(CR|DR|DB)?\.?$", re.I)


def _norm_label(s: str) -> str:
    out = s.lower().strip().rstrip(":").strip()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ã", "a"),
                 ("õ", "o"), ("ç", "c"), ("ê", "e"), ("ô", "o")):
        out = out.replace(a, b)
    return out


def read_index(pdf_path: str) -> DocumentIndex:
    """Every word of the text layer with its box, page by page."""
    import pdfplumber

    pages: dict[int, PageIndex] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, start=1):
            idx = PageIndex(page=n, width=float(page.width), height=float(page.height))
            for w in page.extract_words(use_text_flow=False, keep_blank_chars=False,
                                        extra_attrs=["size"]):
                idx.tokens.append(Token(
                    text=w["text"],
                    bbox=BBox(n, float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"])),
                    source="text_layer"))
            pages[n] = idx
    return DocumentIndex(pages=pages, sources=("text_layer",))


def has_text_layer(index: DocumentIndex, min_tokens: int = 25) -> tuple[bool, dict[str, Any]]:
    """Guard ``has_text_layer``: enough extractable words to be worth parsing.

    Reported with its evidence, because "this scan has 3 stray words from a stamp" and
    "this digital PDF has 1,200 words" must not be the same answer.
    """
    counts = {n: len(p.tokens) for n, p in index.pages.items()}
    total = sum(counts.values())
    return total >= min_tokens, {"tokens_per_page": counts, "total_tokens": total,
                                 "threshold": min_tokens}


@dataclass
class _Columns:
    """x-ranges for each logical column, derived from the header row."""

    ranges: dict[str, tuple[float, float]]
    header_y: float
    page: int

    def assign(self, box: BBox) -> str | None:
        centre = (box.x0 + box.x1) / 2
        best, best_d = None, 1e9
        for name, (x0, x1) in self.ranges.items():
            if x0 <= centre <= x1:
                return name
            d = min(abs(centre - x0), abs(centre - x1))
            if d < best_d:
                best, best_d = name, d
        return best if best_d < 12 else None


def _lines(tokens: list[Token], tol: float = 2.6) -> list[list[Token]]:
    """Group words into visual lines by their vertical centre."""
    rows: list[list[Token]] = []
    for t in sorted(tokens, key=lambda t: ((t.bbox.y0 + t.bbox.y1) / 2, t.bbox.x0)):
        centre = (t.bbox.y0 + t.bbox.y1) / 2
        if rows and abs(((rows[-1][0].bbox.y0 + rows[-1][0].bbox.y1) / 2) - centre) <= tol:
            rows[-1].append(t)
        else:
            rows.append([t])
    for r in rows:
        r.sort(key=lambda t: t.bbox.x0)
    return rows


def _detect_columns(page: PageIndex, hints: dict[str, Any]) -> _Columns | None:
    """Find the table header and turn it into column x-ranges.

    A declared layout wins: ``layout_hints.columns`` in the spec gives exact ranges for
    a known bank. Otherwise the header words are matched against the lexicon, which is
    what makes a never-seen bank parseable at all.

    Matching works over *runs* of adjacent tokens rather than single words, because
    extraction routinely splits a header: a two-word label ("F. Valor") arrives as two
    tokens, and small-caps styling makes pdfplumber emit "DATE" as "D" + "ATE". Both are
    real artifacts of real statements, so the matcher joins up to four neighbours and
    compares with the spaces removed.
    """
    declared = hints.get("columns")
    if declared:
        return _Columns({k: (float(v[0]), float(v[1])) for k, v in declared.items()},
                        header_y=float(hints.get("header_y", 0.0)), page=page.page)

    targets = {col: {_norm_label(w).replace(" ", "").replace(".", "") for w in words}
               for col, words in LEXICON.items()}

    best: tuple[int, dict[str, tuple[float, float]], float] | None = None
    for line in _lines(page.tokens):
        found: dict[str, tuple[float, float]] = {}
        taken: set[int] = set()

        def consider(width: int, exact: bool) -> None:
            for i in range(len(line) - width + 1):
                span = set(range(i, i + width))
                if taken & span:
                    continue
                run = line[i:i + width]
                joined = _norm_label("".join(t.text for t in run)).replace(" ", "").replace(".", "")
                if not joined:
                    continue
                for col, words in targets.items():
                    if col in found:
                        continue
                    hit = (joined in words) if exact else any(
                        joined.startswith(w) and len(w) >= 4 for w in words)
                    if hit:
                        found[col] = (run[0].bbox.x0, run[-1].bbox.x1)
                        taken.update(span)
                        break

        # Exact matches first and widest-first, so "F. Valor" claims the date column
        # before the bare "Valor" can be mistaken for an amount column, and "D"+"ATE"
        # (small-caps) is recognised as "Date". Prefix matching is a single-token
        # fallback only: applied to runs it swallows the whole header row.
        for width in (4, 3, 2, 1):
            consider(width, exact=True)
        consider(1, exact=False)
        if "date" in found and len(found) >= 3:
            score = len(found)
            if best is None or score > best[0]:
                best = (score, found, max(t.bbox.y1 for t in line))
    if best is None:
        return None

    _, found, header_y = best
    # Widen each header word's x-range to the midpoints between neighbours, so a number
    # right-aligned under a short header still lands in the right column.
    ordered = sorted(found.items(), key=lambda kv: kv[1][0])
    ranges: dict[str, tuple[float, float]] = {}
    for i, (name, (x0, x1)) in enumerate(ordered):
        left = 0.0 if i == 0 else (ordered[i - 1][1][1] + x0) / 2
        right = page.width if i == len(ordered) - 1 else (x1 + ordered[i + 1][1][0]) / 2
        ranges[name] = (left, right)
    return _Columns(ranges, header_y=header_y, page=page.page)


@dataclass
class _CharStream:
    """A page's tokens as one character stream, with each character mapped to its token.

    Header labels and their values are frequently glued into one token
    ("Saldo | anterior3.049,73") or split across a column break ("Saldo" at the end of
    one line, "actual6.637,14" at the start of the next). Searching token by token gets
    both wrong, and the failure is quiet: the value of the *next* label is returned
    instead, so an opening balance silently becomes a closing balance. Searching a
    character stream and then mapping the match back to tokens handles both.
    """

    raw: str
    folded: str          # same length as raw: lowercased, accents folded, spaces dropped
    token_of: list[int]
    tokens: list[Token]

    def bbox_for(self, start: int, end: int) -> BBox | None:
        ids = sorted({self.token_of[i] for i in range(start, min(end, len(self.raw)))})
        if not ids:
            return None
        boxes = [self.tokens[i].bbox for i in ids]
        return BBox(boxes[0].page, min(b.x0 for b in boxes), min(b.y0 for b in boxes),
                    max(b.x1 for b in boxes), max(b.y1 for b in boxes))


def _fold_char(ch: str) -> str:
    table = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ã": "a", "õ": "o",
             "ç": "c", "ê": "e", "ô": "o", "ü": "u", "ñ": "n", "à": "a", "â": "a"}
    low = ch.lower()
    return table.get(low, low)


def build_stream(page: PageIndex) -> _CharStream:
    raw_parts: list[str] = []
    token_of: list[int] = []
    tokens: list[Token] = []
    for line in _lines(page.tokens):
        for t in line:
            idx = len(tokens)
            tokens.append(t)
            raw_parts.append(t.text)
            token_of.extend([idx] * len(t.text))
    raw = "".join(raw_parts)
    folded = "".join(_fold_char(c) for c in raw)
    return _CharStream(raw=raw, folded=folded, token_of=token_of, tokens=tokens)


_DATE_AFTER = re.compile(r"\d{1,2}\s*[/.\-]\s*\d{1,2}\s*[/.\-]\s*\d{2,4}"
                         r"|\d{1,2}\s*[A-Za-z]{3,9}\.?\s*\d{4}")
_AMOUNT_AFTER = re.compile(r"[(\-]?\d[\d.,  ]*\d[\-)]?|\d")
_INT_AFTER = re.compile(r"\d{1,6}")
_TEXT_AFTER = re.compile(r"[A-Za-z0-9][A-Za-z0-9/\-.*]{2,33}")

_VALUE_RE = {"money": _AMOUNT_AFTER, "date": _DATE_AFTER, "int": _INT_AFTER, "text": _TEXT_AFTER}


def find_period_range(index: DocumentIndex, fmt: str,
                      *, window: int = 64) -> tuple[tuple[str, BBox], tuple[str, BBox]] | None:
    """Read a period printed as one range: "From 01 Jan 2024 To 31 Mar 2024".

    Searching for the end date by its own label is unsafe, because that label is a
    short common word. "To" occurs inside "UPI-TRANSFER TO 9097052564", so the first
    match can be a transaction description hundreds of rows down, and the period then
    silently ends in the middle of the statement. Every date in the document lies inside
    such a period, so DATE_ORDER keeps passing and nothing reveals the error.

    Taking both dates from a single range, after one unambiguous opening label, removes
    the guess entirely.
    """
    start_labels = ("searched by from", "periodo desde", "período desde", "period",
                    "periodo", "statement period", "from")
    for _, page in sorted(index.pages.items()):
        stream = build_stream(page)
        for label in start_labels:
            key = _norm_label(label).replace(" ", "")
            if len(key) < 4:
                continue
            pos = stream.folded.find(key)
            if pos < 0:
                continue
            start = pos + len(key)
            tail = stream.raw[start:start + window]
            matches = list(_DATE_AFTER.finditer(tail))
            if len(matches) < 2:
                continue
            out = []
            for m in matches[:2]:
                a, b = start + m.start(), start + m.end()
                box = stream.bbox_for(a, b)
                if box is None:
                    break
                out.append((m.group(0).strip(" :"), box))
            if len(out) == 2:
                return out[0], out[1]
    return None


def find_header_field(index: DocumentIndex, keys: Iterable[str], kind: str,
                      *, window: int = 46) -> tuple[str, BBox] | None:
    """Locate ``label value`` anywhere in the document and return the value's text and box.

    Only the ``window`` characters after the label are considered, so a label whose
    value is missing cannot reach across the page and adopt an unrelated number.
    """
    wanted = [_norm_label(k).replace(" ", "") for k in keys]
    pattern = _VALUE_RE[kind]
    for _, page in sorted(index.pages.items()):
        stream = build_stream(page)
        for key in wanted:
            if not key:
                continue
            pos = stream.folded.find(key)
            if pos < 0:
                continue
            start = pos + len(key)
            tail = stream.raw[start:start + window]
            m = pattern.search(tail)
            if not m:
                continue
            a, b = start + m.start(), start + m.end()
            box = stream.bbox_for(a, b)
            if box is None:
                continue
            return m.group(0).strip(" :"), box
    return None



def parse_statement_from_index(index: DocumentIndex, spec, *, doc_id: str,
                               provenance_source: str = "text_layer",
                               ) -> tuple[Statement, dict[str, int], list[str]]:
    """Turn located tokens into a candidate statement.

    One parser serves both sources. A digital PDF supplies tokens from its text layer
    and a scan supplies them from OCR, but column detection, cell assembly, locale-aware
    number parsing and strict dates are identical for both. A fix for one is a fix for
    the other, and the grounding engine can compare two readings of the same page
    because they are expressed in the same coordinates.
    """
    provenance_enum = (Provenance.TEXT_LAYER if provenance_source == "text_layer"
                       else Provenance.OCR)
    st = Statement(doc_id=doc_id, currency=spec.currency_default,
                   page_count=len(index.pages))
    errors: dict[str, int] = {}
    notes: list[str] = []

    def bump(code: str) -> None:
        errors[code] = errors.get(code, 0) + 1

    # ---- header
    hdr_specs = [
        ("opening_balance", "money"), ("closing_balance", "money"),
        ("period_start", "date"), ("period_end", "date"),
        ("account_id", "text"), ("tx_count", "int"),
    ]
    for name, kind in hdr_specs:
        got = find_header_field(index, HEADER_LABELS[name], kind)
        f: Field = getattr(st.header, name)
        f.name = name
        if got is None:
            f.error_code = "LABEL_NOT_FOUND"
            bump(f"{name}:LABEL_NOT_FOUND")
            continue
        raw, box = got
        f.raw, f.bbox, f.provenance = raw, box, provenance_enum
        if kind == "money":
            val, err = parse_amount_result(raw, spec.locale, spec.currency_default,
                                           allow_blank=False)
            f.value, f.error_code = val, err
            if err:
                bump(f"{name}:{err}")
        elif kind == "date":
            # Header dates may be printed in a different format from the rows.
            val, err = parse_date_result(raw, spec.header_date_fmt)
            if val is None and spec.header_date_fmt != spec.date_fmt:
                val, err = parse_date_result(raw, spec.date_fmt)
            f.value, f.error_code = val, err
            if err:
                bump(f"{name}:{err}")
        elif kind == "int":
            digits = re.sub(r"[^\d]", "", raw)
            if digits:
                f.value = int(digits)
            else:
                f.error_code = "NOT_AN_INTEGER"
                bump(f"{name}:NOT_AN_INTEGER")
        else:
            f.value = raw
    # A period printed as a single range is read as a range. This runs whenever a
    # range is present, not only as a repair, because the failure it prevents is
    # silent: the end-date label is a short common word ("to", "hasta") that also
    # occurs inside transaction narratives, so a per-label search can return a
    # perfectly well-formed date from the middle of the statement. Every row then
    # still falls inside the period and DATE_ORDER keeps passing.
    _range_first = find_period_range(index, spec.header_date_fmt)
    if _range_first is not None:
        rng = _range_first
        if rng is not None:
            (raw_a, box_a), (raw_b, box_b) = rng
            va, ea = parse_date_result(raw_a, spec.header_date_fmt)
            vb, eb = parse_date_result(raw_b, spec.header_date_fmt)
            if va is not None and vb is not None and vb >= va:
                st.header.period_start = Field("period_start", raw_a, va,
                                               provenance_enum, box_a)
                st.header.period_end = Field("period_end", raw_b, vb,
                                             provenance_enum, box_b)
                errors.pop("period_start:FORMAT_MISMATCH", None)
                errors.pop("period_end:FORMAT_MISMATCH", None)
                errors.pop("period_start:LABEL_NOT_FOUND", None)
                errors.pop("period_end:LABEL_NOT_FOUND", None)

    st.header.currency.value = spec.currency_default
    st.header.currency.provenance = provenance_enum

    # ---- rows, page by page
    row_index = 0
    for page_no, page in sorted(index.pages.items()):
        cols = _detect_columns(page, spec.layout_hints)
        if cols is None:
            notes.append(f"page {page_no}: no table header recognised")
            bump("page:NO_TABLE_HEADER")
            continue
        # Pass 1: split every line below the header into cells, and keep the ones
        # that start with a parseable date.
        candidates: list[tuple[dict[str, list[Token]], Any, Any]] = []
        for line in _lines(page.tokens):
            if max(t.bbox.y1 for t in line) <= cols.header_y + 1:
                continue
            cells: dict[str, list[Token]] = {}
            for tok in line:
                col = cols.assign(tok.bbox)
                if col:
                    cells.setdefault(col, []).append(tok)

            # A carry-forward line is checked first: its label spills into the date
            # column, so testing "does this line have a date" first would classify
            # it as an unparseable transaction and discard the subtotal silently.
            cf = _carry_forward_from(line, cols, spec)
            if cf is not None:
                st.carried_forward[page_no] = cf
                continue
            if "date" not in cells:
                continue
            found_date = _first_date_in(cells["date"], spec.date_fmt)
            if found_date is None:
                continue    # header repeat, legend or footer: not a row
            dval, date_text, date_toks = found_date
            cells["date"] = date_toks
            candidates.append((cells, dval, date_text))

        # Right-align anchors, measured from the data rather than from the header.
        # A numeric column's figures all end at the same x, so a token that stops
        # well short of that anchor is overflow from the description, not a value.
        # Without this an empty debit cell on a credit row quietly adopts the
        # reference number printed at the end of the narrative.
        anchors = _column_anchors(candidates, cols)

        # Then use those anchors to correct the column each figure was put in.
        #
        # Assignment above goes by a token's centre, which is right for a left-aligned
        # column and wrong for a right-aligned one: the shorter the figure, the further
        # right its centre sits, so a small amount drifts into the next column while
        # large ones in the same column do not. On one external document "6.12" landed
        # in the balance column, which left the row with no amount at all and refused
        # an otherwise perfect document. The margin, not the centre, is what identifies
        # a money column, and it is measured here rather than taken from the header.
        _reassign_by_anchor(candidates, anchors)

        # Pass 2: build the rows.
        for cells, dval, date_text in candidates:
            row = Row(index=row_index, page=page_no)
            row_index += 1
            row.date = _field("date", date_text, dval, None, cells["date"])

            desc_toks = cells.get("description", [])
            row.description = _field("description", " ".join(t.text for t in desc_toks) or None,
                                     " ".join(t.text for t in desc_toks) or None, None, desc_toks)

            for col in ("debit", "credit", "balance"):
                toks = _cell_value_tokens(cells.get(col, []), anchors.get(col))
                raw = " ".join(t.text for t in toks).strip()
                if not toks or not raw:
                    setattr(row, col, Field(col))
                    continue
                val, err = parse_amount_result(raw, spec.locale, spec.currency_default)
                if err:
                    bump(f"{col}:{err}")
                note = None
                if col == "debit" and val is not None and val.minor < 0:
                    # "221.36 DR" in a column already headed "Withdrawals": the
                    # marker restates the column rather than negating it. The
                    # magnitude is what the ledger owes, and the column header is
                    # first-hand evidence for the side, not a derivation from the
                    # balance, so P3 is untouched.
                    val, note = -val, "SIGN_FROM_COLUMN"
                f = _field(col, raw, val, err, toks)
                if note:
                    f.grounding_detail = {"note": note}
                setattr(row, col, f)

            if spec.columns.mode == "signed_amount" and "amount" in cells:
                toks = _cell_value_tokens(cells["amount"], anchors.get("amount"))
                raw = " ".join(t.text for t in toks).strip()
                val, err = parse_amount_result(raw, spec.locale, spec.currency_default)
                if err:
                    bump(f"amount:{err}")
                elif val is not None:
                    # A single signed column: the sign on the page decides the side.
                    # Nothing here is derived from a balance difference, so both
                    # sides stay first-hand evidence (P3).
                    target = "credit" if val.minor >= 0 else "debit"
                    setattr(row, target, _field(target, raw,
                                                val if val.minor >= 0 else -val, None, toks))

            elif spec.columns.mode == "amount_direction" and "amount" in cells:
                # One amount column plus a Cr/Dr indicator column. The indicator is
                # printed evidence about the direction, read from the page like any
                # other cell, so the row stays first-hand evidence. What must never
                # happen is inferring the direction from the balance difference:
                # that would make ROW_BAL verify a value it had itself produced (P3).
                toks = _cell_value_tokens(cells["amount"], anchors.get("amount"))
                raw = " ".join(t.text for t in toks).strip()
                val, err = parse_amount_result(raw, spec.locale, spec.currency_default)
                dir_toks = cells.get("direction", [])
                marker = _norm_label("".join(t.text for t in dir_toks)).upper()
                side = _read_direction(marker)
                if err:
                    bump(f"amount:{err}")
                if val is None:
                    pass
                elif side is not None:
                    setattr(row, side, _field(side, raw, abs_money(val), None, toks))
                else:
                    bump("direction:UNREADABLE_MARKER")
                    notes.append(f"row {row.index}: direction marker {marker!r} "
                                 "is not a recognised Cr/Dr indicator")
            st.rows.append(row)

    if not st.rows:
        notes.append("no transaction rows found in the text layer")
    return st, errors, notes


class TextLayerProposer(Proposer):
    """Tier 0. Free, exact, and the only tier that needs no model at all."""

    tier = "text_layer"
    cost_class = 0
    bills_usd = False

    def propose(self, doc: Document, spec, *, region: Location | None = None,
                previous: Statement | None = None) -> Proposal:
        index = read_index(doc.pdf_path)
        st, errors, notes = parse_statement_from_index(
            index, spec, doc_id=doc.doc_id, provenance_source="text_layer")
        return Proposal(statement=st, index=index, tier=self.tier,
                        parse_errors=errors, notes=notes)



NUMERIC_COLUMNS = ("debit", "credit", "balance", "amount")


def abs_money(value):
    """Magnitude of an amount whose direction is carried by a separate column."""
    return value if value.minor >= 0 else -value


def _read_direction(marker: str) -> str | None:
    """Read a Cr/Dr indicator cell, tolerating decoration glued to it.

    A watermark glyph lands against the marker and turns "CR" into "ECR" or "DR" into
    "DRI". An exact match would reject those and escalate a row that is perfectly
    legible. A substring search accepts them, but only when the cell points one way:
    a cell containing both CR and DR is genuinely ambiguous and is refused, because
    guessing the direction of a payment is not a small error.
    """
    if not marker:
        return None
    has_debit = any(m in marker for m in ("DR", "DB", "DEBIT", "CARGO"))
    has_credit = any(m in marker for m in ("CR", "CREDIT", "ABONO"))
    if has_debit and not has_credit:
        return "debit"
    if has_credit and not has_debit:
        return "credit"
    if marker in ("D",):
        return "debit"
    if marker in ("C",):
        return "credit"
    return None


def _column_anchors(candidates: list, cols: "_Columns") -> dict[str, float]:
    """The right-hand x at which each numeric column's figures line up.

    Measured from tokens that contain a digit only. A watermark letter printed to the
    right of the figures would otherwise set the anchor beyond every real amount, and
    then every amount in the column would be judged to fall short of its own alignment
    line and the whole column would read as empty.
    """
    anchors: dict[str, float] = {}
    for col in NUMERIC_COLUMNS:
        xs = []
        for cells, _, _ in candidates:
            digits = [t for t in cells.get(col, []) if any(c.isdigit() for c in t.text)]
            if digits:
                xs.append(max(t.bbox.x1 for t in digits))
        if xs:
            anchors[col] = max(xs)
    return anchors


def _reassign_by_anchor(candidates: list, anchors: dict[str, float],
                        tol: float = 1.5) -> None:
    """Move each figure into the numeric column whose right margin it shares.

    Only figures move, and only between numeric columns: a token is a candidate if it
    carries a digit and already sits in one of them. Everything else -- descriptions,
    dates, reference codes, the direction marker -- is left exactly where the header put
    it, so widening this cannot pull narrative text into a money column.

    A figure moves only when its right edge matches exactly one column's measured margin
    within ``tol``. Two columns whose margins fall within a point and a half of each other
    cannot be told apart this way, and in that case nothing moves: an ambiguous figure
    stays where it was rather than being guessed into a column, and the row check then
    reports the disagreement instead of a confident wrong answer.
    """
    if len(anchors) < 2:
        return
    for cells, _dval, _text in candidates:
        for col in list(cells):
            if col not in NUMERIC_COLUMNS:
                continue
            for tok in list(cells[col]):
                if not any(c.isdigit() for c in tok.text):
                    continue
                matches = [name for name, x in anchors.items()
                           if abs(tok.bbox.x1 - x) <= tol]
                if len(matches) != 1 or matches[0] == col:
                    continue
                target = matches[0]
                cells[col].remove(tok)
                cells.setdefault(target, []).append(tok)
                cells[target].sort(key=lambda t: t.bbox.x0)
            if not cells[col]:
                del cells[col]


def _first_date_in(toks: list[Token], fmt: str) -> tuple[Any, str, list[Token]] | None:
    """The leftmost run of tokens in a cell that parses as a date under ``fmt``.

    A date column is often wider than its own content: a layout with "Txn Date" and
    "Value Date" side by side, or a row number and a transaction id printed before the
    date, all land in the same cell once the column boundaries come from the header
    words. Joining the whole cell and parsing it fails, and the row is then discarded
    as a footer. Scanning left to right for the first thing that *is* a date keeps the
    row and takes the earliest of the two dates, which is the transaction date.
    """
    ordered = sorted(toks, key=lambda t: t.bbox.x0)
    for width in (1, 2, 3):
        for i in range(len(ordered) - width + 1):
            run = ordered[i:i + width]
            text = " ".join(t.text for t in run)
            value, err = parse_date_result(text, fmt)
            if value is not None:
                return value, text, run
    return None


#: Tokens that carry sign information and must be kept with the number, but only when
#: they are printed hard against it (see _cell_value_tokens).
_SIGN_TOKENS = {"CR", "DR", "DB", "DEB", "-", "(", ")", "+"}
#: Tokens that are only a currency label and must be discarded before parsing.
_CURRENCY_ONLY = {"RS", "R$", "US$", "$", "€", "£", "¥", "₹", "BS", "BS.S",
                  "EUR", "USD", "INR", "GBP", "BRL", "VES", "MXN", "COP"}


def _numeric_tokens(toks: list[Token]) -> list[Token]:
    """Drop tokens from a numeric cell that cannot be part of a number.

    Documents carry decoration that lands inside data cells. A rotated "MACHINE
    GENERATED" watermark contributes a single stray letter to a row, and a currency
    label is printed as its own token. Keeping either turns a perfectly readable amount
    into a parse error, which escalates a document that was never damaged: "Rs." adds a
    second full stop and the cell is rejected for having two decimal separators.

    Sign markers are kept, because they change the value. Currency labels are dropped,
    because they do not.
    """
    keep = []
    for t in toks:
        text = t.text.strip()
        if any(ch.isdigit() for ch in text):
            keep.append(t)
            continue
        upper = normalise_numeric_text(text).upper().strip(".,")
        if upper in _CURRENCY_ONLY:
            continue
        if upper in _SIGN_TOKENS:
            keep.append(t)
    return keep


def _cell_value_tokens(toks: list[Token], anchor: float | None,
                       tol: float = 2.5, sign_gap: float = 2.0) -> list[Token]:
    """The tokens that really form this right-aligned cell's value, or none at all.

    The figure is built from the digit tokens first, and a sign token joins it only if
    it is printed hard against the digits. This ordering matters: a stray "-" from a
    hyphenated narrative ("By Clg:DEL - ACCTS-CITI BANK") lands in the amount column
    with a visible gap, and treating it as a sign turns 24,304.46 into -24,304.46. That
    is a wrong value that parses cleanly, balances nothing, and would be invisible
    without the row check.
    """
    toks = _numeric_tokens(toks)
    if not toks:
        return []
    digits = [t for t in toks if any(c.isdigit() for c in t.text)]
    if not digits:
        return []
    group = _rightmost_group(digits)
    if anchor is not None and max(t.bbox.x1 for t in group) < anchor - tol:
        return []       # the cell is empty; what is here belongs to the narrative

    left, right = min(t.bbox.x0 for t in group), max(t.bbox.x1 for t in group)
    for t in toks:
        if t in group:
            continue
        if (left - t.bbox.x1) >= 0 and (left - t.bbox.x1) <= sign_gap:
            group.append(t)
        elif (t.bbox.x0 - right) >= 0 and (t.bbox.x0 - right) <= sign_gap:
            group.append(t)
    return sorted(group, key=lambda t: t.bbox.x0)


def _rightmost_group(toks: list[Token], gap: float = 5.0) -> list[Token]:
    """Keep only the last visually contiguous run of tokens in a right-aligned cell.

    A long or wrapped description overflows past the column boundary, so an amount
    column can collect the tail of the text as well as the figure: "/ REF 007919" next
    to "134.33" reads as 7,919,134.33, which is a wrong value that still parses. Because
    numeric columns are right-aligned, the figure is always the rightmost run, and the
    intruding text is separated from it by a visible gap.
    """
    if len(toks) <= 1:
        return toks
    ordered = sorted(toks, key=lambda t: t.bbox.x0)
    group = [ordered[0]]
    for prev, cur in zip(ordered, ordered[1:]):
        if cur.bbox.x0 - prev.bbox.x1 > gap:
            group = [cur]
        else:
            group.append(cur)
    return group


def _field(name: str, raw, value, err, toks: list[Token]) -> Field:
    box = None
    if toks:
        box = BBox(toks[0].bbox.page, min(t.bbox.x0 for t in toks), min(t.bbox.y0 for t in toks),
                   max(t.bbox.x1 for t in toks), max(t.bbox.y1 for t in toks))
    return Field(name=name, raw=raw, value=value, provenance=Provenance.TEXT_LAYER,
                 bbox=box, error_code=err)


def _first_amount_like(text: str) -> str | None:
    for part in text.replace(" ", " ").split():
        if _AMOUNT_RE.match(part) and any(ch.isdigit() for ch in part):
            return part
    # Fall back to the longest run of digits and separators.
    m = re.search(r"[-+(]?[\d][\d.,   ]*\d[-)]?", text)
    return m.group(0) if m else None


def _carry_forward_from(line: list[Token], cols: _Columns, spec) -> Field | None:
    """Recognise "carried forward" / "saldo que pasa" lines and read their amount."""
    joined = _norm_label(" ".join(t.text for t in line))
    markers = ("saldo que pasa", "suma y sigue", "carried forward", "saldo transporte",
               "transporta", "saldo a transportar", "carry forward", "saldo parcial")
    if not any(m in joined for m in markers):
        return None
    bal_toks = [t for t in line if cols.assign(t.bbox) == "balance"]
    if not bal_toks:
        bal_toks = [t for t in line if _AMOUNT_RE.match(t.text) and any(c.isdigit() for c in t.text)]
    if not bal_toks:
        return None
    raw = " ".join(t.text for t in bal_toks)
    val, err = parse_amount_result(raw, spec.locale, spec.currency_default, allow_blank=False)
    f = _field("carried_forward", raw, val, err, bal_toks)
    return f
