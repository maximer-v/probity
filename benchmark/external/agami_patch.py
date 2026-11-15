"""Build statements that tie, and statements with one known alteration, on a public layout.

Every one of the 400 documents in AgamiAI/Indian-Bank-Statements fails its own running
balance: 7,802 of 64,698 rows (12.06%), at least six breaks per document. As published,
the corpus therefore contains:

* **no document whose correct conclusion is CONFIRMED**, so a system that refuses
  everything would score perfectly;
* **no alteration of known provenance**, so there is nothing to measure detection
  against.

This module builds both on the publisher's own pages, and records which bytes are
theirs and which are ours.

**The correction.** The printed closing balance equals the printed last-row balance in
200 of 200 digital documents, while the chain recomputed from the published amounts
ends below it in 184, on it in 16 and above it in none. A one-sided error points at the
amounts, not at the balance column, so the amounts are corrected to agree with the
printed balances.
Dates, descriptions, reference codes and balances stay exactly as published.

**The alteration.** In the altered group, one printed amount is then changed by a known
quantity and the balance column is left alone, so the chain no longer follows and
nothing on the page says so. Which cell, from what and to what are recorded in the
truth file.

**How the edit is made.** Each amount in these PDFs is an isolated text block::

    BT
    1 0 0 1 500.131 716.5 Tm
    (Rs\\056\\04018\\054916\\05603) Tj
    T*
    ET

so a cell can be rewritten without touching its neighbours. Amounts are right-aligned, so
changing the digit count requires moving the origin. ``/F1`` is non-embedded Helvetica,
whose digits are all 556/1000 em and whose ``.`` and ``,`` are 278, so the shift is
``width(old) - width(new)`` exactly. Only the difference is used, never an absolute
position, so an error in the absolute text origin cannot move a cell.

Cells are located by **position**, never by string search: seven of the 143 balance
strings in the first document appear more than once, and a search-and-replace would hit
the wrong row. Blocks are read in page then y order, and the resulting sequence of values
is asserted equal to the published balance sequence before anything is written. If the
mapping is wrong the assertion fails and no file is produced.

Nothing here is trusted. ``verify()`` reads every written file back through the
framework's text-layer reader and compares each amount, direction and date with the
truth file; it also checks that the truth's chain is exact (for a corrected document) or
breaks at exactly the planted row (for an altered one), and that every amount still sits
on a column margin. A document that fails any of these is not emitted.

    python -m benchmark.external.agami_patch --dir <download dir> --out data/external/agami_built
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# Helvetica (Adobe standard 14) advance widths, 1/1000 em. Only the characters that can
# appear in an amount cell are needed; anything else raises rather than guessing, since a
# silently wrong width would move a cell and corrupt the layout we are claiming to
# preserve.
_HELV: dict[str, int] = {
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556,
    "5": 556, "6": 556, "7": 556, "8": 556, "9": 556,
    ".": 278, ",": 278, " ": 278, "-": 333, "(": 333, ")": 333,
    "R": 722, "s": 500, "r": 333, "C": 722, "D": 722, "c": 500, "d": 556,
    "/": 278, "+": 584, ":": 278,
}


def text_width(s: str, size: float) -> float:
    """Advance width of ``s`` at ``size`` points, in points."""
    total = 0
    for ch in s:
        try:
            total += _HELV[ch]
        except KeyError as exc:  # pragma: no cover - guards against silent mislayout
            raise ValueError(f"no Helvetica width for {ch!r} in {s!r}") from exc
    return total * size / 1000.0


# ---------------------------------------------------------------------------
# content-stream surgery


_ESCAPE = {"\\": r"\134", "(": r"\050", ")": r"\051"}


def pdf_escape(s: str) -> str:
    """Encode a string the way these documents encode theirs.

    The generator escapes punctuation as three-digit octal and leaves digits literal.
    Matching that exactly keeps a patched cell byte-indistinguishable in form from an
    untouched one, so a reader cannot tell which cells we wrote.
    """
    out = []
    for ch in s:
        if ch in _ESCAPE:
            out.append(_ESCAPE[ch])
        elif ch in ".,-/ ":
            out.append("\\%03o" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def pdf_unescape(s: str) -> str:
    """Decode octal and backslash escapes in a PDF literal string."""
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt.isdigit():
                j = i + 1
                while j < len(s) and j < i + 4 and s[j].isdigit():
                    j += 1
                out.append(chr(int(s[i + 1:j], 8)))
                i = j
                continue
            out.append(nxt)
            i += 2
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


# One text object. Splitting on these first matters: an amount cell is often preceded by
# an *empty* cell block (the unused side of the row), and a regex permitted to skip
# forward from a Tm to the next Tj will pair the empty block's origin with the following
# cell's text. That misattribution moves the wrong cell, so blocks are isolated before
# anything inside them is read.
_TEXT_OBJECT = re.compile(r"BT\s*\n(?P<body>.*?)\nET", re.DOTALL)
_TM = re.compile(r"^1 0 0 1 (?P<x>-?[\d.]+) (?P<y>-?[\d.]+) Tm$", re.MULTILINE)
_TF = re.compile(r"^/(?P<font>\S+)\s+(?P<size>[\d.]+)\s+Tf$", re.MULTILINE)
_TJ = re.compile(r"^\((?P<payload>(?:[^()\\]|\\.)*)\) Tj$", re.MULTILINE)

_AMOUNT = re.compile(r"^(?P<prefix>Rs\.\s*|)(?P<num>-?[\d,]+\.\d{2})(?P<suffix>\s*(?:Cr|Dr)?)$")


@dataclass
class Cell:
    """One amount cell in one page's content stream."""

    page: int
    x: float
    y: float
    size: float
    text: str                 # decoded, e.g. "Rs. 18,916.03"
    span: tuple[int, int]     # payload offsets in the stream
    x_span: tuple[int, int]   # offsets of the Tm x literal
    prefix: str
    num: str
    suffix: str

    @property
    def right_edge(self) -> float:
        return self.x + text_width(self.text, self.size)


def find_amount_cells(stream: str, page: int, default_size: float = 6.5) -> list[Cell]:
    """Every cell on a page whose payload reads as an amount, in stream order.

    Font size carries across text objects, since these streams set ``Tf`` once and rely
    on the text state persisting. A block with exactly one ``Tm`` and one ``Tj`` is a
    single cell and is the only shape accepted; a multi-line block is a wrapped
    description, never an amount, and is skipped rather than guessed at.
    """
    cells: list[Cell] = []
    size = default_size
    for obj in _TEXT_OBJECT.finditer(stream):
        body, base = obj.group("body"), obj.start("body")
        fonts = _TF.findall(body)
        if fonts:
            size = float(fonts[-1][1])
        tms, tjs = list(_TM.finditer(body)), list(_TJ.finditer(body))
        if len(tms) != 1 or len(tjs) != 1:
            continue
        tm, tj = tms[0], tjs[0]
        text = pdf_unescape(tj.group("payload"))
        am = _AMOUNT.match(text.strip())
        if not am:
            continue
        cells.append(Cell(
            page=page, x=float(tm.group("x")), y=float(tm.group("y")), size=size,
            text=text,
            span=(base + tj.start("payload"), base + tj.end("payload")),
            x_span=(base + tm.start("x"), base + tm.end("x")),
            prefix=am.group("prefix"), num=am.group("num"), suffix=am.group("suffix"),
        ))
    return cells


def format_amount(minor: int, grouping: str = "western") -> str:
    """Format the way this publisher formats, not the way the locale suggests.

    These are Indian bank statements, so lakh grouping (2,2,...,3) is the expected
    convention and the framework's parser accepts it. The publisher does not use it: a
    sweep of 1,144 six-or-more-digit amounts across the corpus prints ``2,482,196``, never
    ``24,82,196``. Writing a replacement in lakh grouping would change the comma count,
    which changes the cell's width and so its alignment, and would make the cells we
    wrote visibly different in format from the cells we did not. The convention is
    therefore taken from the document, not from the locale.
    """
    neg = minor < 0
    whole, frac = divmod(abs(minor), 100)
    if grouping == "indian":
        s = str(whole)
        if len(s) > 3:
            head, tail = s[:-3], s[-3:]
            parts = []
            while len(head) > 2:
                parts.insert(0, head[-2:])
                head = head[:-2]
            if head:
                parts.insert(0, head)
            s = ",".join(parts + [tail])
    else:
        s = f"{whole:,}"
    return ("-" if neg else "") + f"{s}.{frac:02d}"


def detect_grouping(cells: Iterable[Cell]) -> str:
    """Read the grouping convention off the document's own long amounts."""
    for cell in cells:
        whole = cell.num.lstrip("-").split(".")[0]
        digits = whole.replace(",", "")
        if len(digits) >= 6 and "," in whole:
            # lakh grouping puts the first comma three digits from the point and then
            # every two; western puts one every three.
            return "indian" if len(whole.split(",")[-2]) == 2 else "western"
    return "western"


def rewrite(stream: str, edits: list[tuple[Cell, int]],
            grouping: str = "western") -> str:
    """Apply ``(cell, new_minor_units)`` edits to one page, preserving right alignment.

    Edits are applied from the end of the stream backwards so that earlier offsets stay
    valid. The new origin is ``x + width(old) - width(new)``: a difference of widths, so
    the result does not depend on knowing the absolute text origin. That matters here,
    because the page's base transform puts the rendered origin some 25 points from the
    value in the ``Tm``, and a scheme that needed the absolute position would be wrong by
    that much on every cell.
    """
    pieces: list[tuple[int, int, str]] = []
    for cell, minor in edits:
        new_text = f"{cell.prefix}{format_amount(minor, grouping)}{cell.suffix}"
        dx = text_width(cell.text, cell.size) - text_width(new_text, cell.size)
        new_x = cell.x + dx
        pieces.append((cell.span[0], cell.span[1], pdf_escape(new_text)))
        pieces.append((cell.x_span[0], cell.x_span[1], f"{new_x:.3f}"))
    for start, end, text in sorted(pieces, reverse=True):
        stream = stream[:start] + text + stream[end:]
    return stream


# ---------------------------------------------------------------------------
# mapping cells to the published ledger


def balance_sequence(truth: dict[str, Any]) -> list[int]:
    return [r["balance"] for r in truth["ledger"]["rows"]]


def locate_column(
    pages: list[list[Cell]], want: list[int], tol: float = 1.5
) -> list[Cell] | None:
    """Find the cells that carry ``want``, by position, and prove the mapping.

    Rather than trust a column guess, every plausible right edge is tried: cells sharing
    a right edge are read in page then y order and the resulting values compared against
    the published sequence. A column is accepted only on an exact, complete match, so a
    mapping that is off by one row -- the failure that would quietly tamper with the wrong
    cell -- cannot be accepted.
    """
    edges: dict[float, list[Cell]] = {}
    for cells in pages:
        for c in cells:
            key = round(c.right_edge / tol) * tol
            edges.setdefault(key, []).append(c)

    for _edge, group in sorted(edges.items(), key=lambda kv: -len(kv[1])):
        if len(group) != len(want):
            continue
        ordered = sorted(group, key=lambda c: (c.page, -c.y))
        got = [_to_minor(c.num) for c in ordered]
        if got == want:
            return ordered
    return None


def _amount_cells_by_row(
    led: dict[str, Any], pages: list[list[Cell]]
) -> dict[tuple[int, str], Cell]:
    """Map ``(row, side)`` to the cell that prints that amount, for either column mode.

    The two layouts in this corpus disagree about how direction is expressed, and the
    difference is not cosmetic. Type 1 prints separate ``Debit`` and ``Credit`` columns,
    so a column holds only one side's non-zero amounts. Type 2 prints a single ``Amount``
    column whose direction comes from a neighbouring ``Cr/Dr`` column, so the same column
    interleaves both sides and a one-sided sequence never matches it.

    Both are attempted and whichever proves out by position is used. A layout that
    matches neither yields no mapping, and the caller skips the document rather than
    writing into a cell it has not identified.
    """
    rows = led["rows"]
    out: dict[tuple[int, str], Cell] = {}

    # Separate debit and credit columns.
    for side in ("debit", "credit"):
        seq = [(i, r.get(side) or 0) for i, r in enumerate(rows)]
        nonzero = [(i, v) for i, v in seq if v]
        if not nonzero:
            continue
        column = locate_column(pages, [v for _i, v in nonzero])
        if column is None:
            continue
        for (row_i, _v), cell in zip(nonzero, column):
            out[(row_i, side)] = cell
    if out:
        return out

    # One signed-by-indicator amount column.
    combined = [
        (i, (r.get("debit") or 0) or (r.get("credit") or 0),
         "debit" if (r.get("debit") or 0) else "credit")
        for i, r in enumerate(rows)
    ]
    nonzero = [(i, v, side) for i, v, side in combined if v]
    if nonzero:
        column = locate_column(pages, [v for _i, v, _s in nonzero])
        if column is not None:
            for (row_i, _v, side), cell in zip(nonzero, column):
                out[(row_i, side)] = cell
    return out


def _to_minor(num: str) -> int:
    neg = num.startswith("-")
    digits = num.lstrip("-").replace(",", "")
    whole, frac = digits.split(".")
    v = int(whole) * 100 + int(frac)
    return -v if neg else v


# ---------------------------------------------------------------------------
# the two builds


@dataclass
class BuildResult:
    doc_id: str
    kind: str                      # "repaired" | "tampered"
    out_pdf: str
    truth: dict[str, Any]
    n_edits: int
    pages: int = 0
    notes: list[str] = field(default_factory=list)
    # (page, right edge) of every cell we rewrote, so verification can confirm the
    # rendered text still ends where the publisher's did.
    edited: list[tuple[int, float]] = field(default_factory=list)


class _CannotRetarget(Exception):
    """Raised when a cell cannot be moved with certainty, so the document is skipped."""


# An amount cell the generator left blank: the unused side of a Type 1 row. Its ``Tm``
# carries the column's right margin, because the generator positions a right-aligned cell
# by subtracting the text width and the width of "" is zero.
_EMPTY = re.compile(
    r"BT\s*\n(?:/\S+\s+[\d.]+\s+Tf\s*\n)?"
    r"1 0 0 1 (?P<x>-?[\d.]+) (?P<y>-?[\d.]+) Tm\s*\n"
    r"(?P<tail>T\*\s*\nET)",
    re.MULTILINE,
)
_INDICATOR = re.compile(r"^(?P<word>CR|DR|Cr|Dr)$")


@dataclass
class ColumnGeometry:
    """Where each amount column sits, and how its cells are dressed."""

    right_edge: dict[str, float] = field(default_factory=dict)
    prefix: dict[str, str] = field(default_factory=dict)
    suffix: dict[str, str] = field(default_factory=dict)
    size: dict[str, float] = field(default_factory=dict)
    single_column: bool = False


def _column_geometry(cells: dict[tuple[int, str], Cell],
                     pages: list[list[Cell]]) -> ColumnGeometry:
    """Read each column's right margin off the cells that are already in it.

    Taken from the document rather than assumed, so a layout that right-aligns at a
    different margin needs no new constant. ``single_column`` records the Type 2 case,
    where debits and credits share one margin and the direction lives elsewhere.
    """
    geom = ColumnGeometry()
    edges: dict[str, list[float]] = {}
    for (_row, side), cell in cells.items():
        edges.setdefault(side, []).append(cell.right_edge)
        geom.prefix.setdefault(side, cell.prefix)
        geom.suffix.setdefault(side, cell.suffix)
        geom.size.setdefault(side, cell.size)
    for side, values in edges.items():
        geom.right_edge[side] = round(sum(values) / len(values), 3)
    if len(geom.right_edge) == 2:
        a, b = geom.right_edge.values()
        geom.single_column = abs(a - b) < 1.5
    return geom


def _find_empty_cell(stream: str, y: float, right_edge: float,
                     tol: float = 1.5) -> re.Match[str] | None:
    """The blank cell on row ``y`` in the column whose margin is ``right_edge``."""
    best = None
    for m in _EMPTY.finditer(stream):
        if abs(float(m.group("y")) - y) > 1.0:
            continue
        if abs(float(m.group("x")) - right_edge) > tol:
            continue
        best = m
        break
    return best


def _find_indicator(stream: str, y: float) -> tuple[int, int, str] | None:
    """The ``CR``/``DR`` cell on row ``y``, as ``(start, end, word)`` of its payload."""
    for obj in _TEXT_OBJECT.finditer(stream):
        body, base = obj.group("body"), obj.start("body")
        tms, tjs = list(_TM.finditer(body)), list(_TJ.finditer(body))
        if len(tms) != 1 or len(tjs) != 1:
            continue
        if abs(float(tms[0].group("y")) - y) > 1.0:
            continue
        word = pdf_unescape(tjs[0].group("payload")).strip()
        if _INDICATOR.match(word):
            return base + tjs[0].start("payload"), base + tjs[0].end("payload"), word
    return None


def _retarget_amount(
    streams: list[str],
    cells: dict[tuple[int, str], Cell],
    geom: ColumnGeometry,
    balance_cell: Cell,
    row_i: int,
    *,
    have_side: str | None,
    want_side: str,
    magnitude: int,
    grouping: str,
) -> tuple[int, list[tuple[int, int, str]]]:
    """Put ``magnitude`` in row ``row_i``'s ``want_side`` column, clearing the other.

    Returns the page and the byte edits to apply to it. Every edit is expressed as a
    span replacement so that a page's edits can be applied together, back to front.
    """
    page = balance_cell.page
    stream = streams[page - 1]
    pieces: list[tuple[int, int, str]] = []

    src = cells.get((row_i, have_side)) if have_side else None

    # Type 2: one amount column, direction carried by a neighbouring CR/DR cell.
    if geom.single_column:
        if src is None:
            raise _CannotRetarget("no amount cell to edit in the single-column layout")
        pieces.extend(_set_amount_pieces(src, magnitude, grouping))
        if have_side != want_side:
            found = _find_indicator(stream, src.y)
            if found is None:
                raise _CannotRetarget("no CR/DR indicator beside the amount")
            start, end, word = found
            flipped = "CR" if want_side == "credit" else "DR"
            if word.islower() or word[1:].islower():
                flipped = flipped.capitalize()
            pieces.append((start, end, pdf_escape(flipped)))
        return page, pieces

    # Type 1: separate columns. Same side is an in-place rewrite.
    if have_side == want_side and src is not None:
        pieces.extend(_set_amount_pieces(src, magnitude, grouping))
        return page, pieces

    # Different side: clear the old cell and write into the blank one the generator left.
    if src is not None:
        pieces.append((src.span[0], src.span[1], ""))

    right_edge = geom.right_edge.get(want_side)
    if right_edge is None:
        raise _CannotRetarget(f"no geometry for the {want_side} column")
    blank = _find_empty_cell(stream, balance_cell.y, right_edge)
    if blank is None:
        raise _CannotRetarget(f"no blank {want_side} cell on this row")

    prefix = geom.prefix.get(want_side, "")
    suffix = geom.suffix.get(want_side, "")
    size = geom.size.get(want_side, balance_cell.size)
    text = f"{prefix}{format_amount(magnitude, grouping)}{suffix}"
    new_x = right_edge - text_width(text, size)
    pieces.append((blank.start("x"), blank.end("x"), f"{new_x:.3f}"))
    pieces.append((blank.start("tail"), blank.start("tail"),
                   f"({pdf_escape(text)}) Tj\n"))
    return page, pieces


def _set_amount_pieces(cell: Cell, magnitude: int,
                       grouping: str) -> list[tuple[int, int, str]]:
    """In-place rewrite of one cell, keeping its right margin."""
    text = f"{cell.prefix}{format_amount(magnitude, grouping)}{cell.suffix}"
    dx = text_width(cell.text, cell.size) - text_width(text, cell.size)
    return [(cell.span[0], cell.span[1], pdf_escape(text)),
            (cell.x_span[0], cell.x_span[1], f"{cell.x + dx:.3f}")]


def _apply(stream: str, pieces: list[tuple[int, int, str]]) -> str:
    """Apply span replacements back to front so earlier offsets stay valid."""
    for start, end, text in sorted(pieces, key=lambda p: (-p[0], -p[1])):
        stream = stream[:start] + text + stream[end:]
    return stream


def _sha256_file(path: str) -> str:
    """Identify the artefact, so a result can be tied to the exact bytes scored."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_pages(pdf_path: str) -> tuple[Any, list[str], list[list[Cell]]]:
    import pikepdf

    pdf = pikepdf.open(pdf_path)
    streams = [p.Contents.read_bytes().decode("latin-1") for p in pdf.pages]
    pages = [find_amount_cells(s, i + 1) for i, s in enumerate(streams)]
    return pdf, streams, pages


def _save(pdf: Any, streams: list[str], out_path: str) -> None:
    import pikepdf

    for page, stream in zip(pdf.pages, streams):
        page.Contents = pdf.make_stream(stream.encode("latin-1"))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pdf.save(out_path)


def repair_balances(pdf_path: str, truth: dict[str, Any],
                    out_path: str) -> BuildResult | None:
    """Recompute the balance column from the amounts. **Kept for the record, not used.**

    This was the first repair, on the reasoning that a balance column is derived and so a
    disagreement must be the derived column's fault. Measuring the corpus says otherwise,
    and the measurement is one-sided enough to be worth keeping the rejected branch for:

    * the printed closing balance equals the printed last-row balance in **200 of 200**
      digital documents, so the balance column and the header agree with each other
      everywhere;
    * recomputing the chain from the publisher's amounts lands *below* the printed
      closing balance in every single document -- the deviation's maximum across the
      corpus is exactly 0.00 and its median is -626,346.67 -- which is a systematic bias
      in the amounts, not scattered noise in the balances;
    * and it would push 76 of 200 accounts into overdraft, the largest by 31.7 million.

    So this direction repairs the trustworthy column using the untrustworthy data, and
    produces documents no bank would recognise. ``repair`` corrects the amounts instead.
    """
    import copy

    pdf, streams, pages = _load_pages(pdf_path)
    column = locate_column(pages, balance_sequence(truth))
    if column is None:
        return None

    led = truth["ledger"]
    bal = led["opening_balance"]
    wanted: list[int] = []
    for row in led["rows"]:
        bal = bal + (row["credit"] or 0) - (row["debit"] or 0)
        wanted.append(bal)

    grouping = detect_grouping(c for page in pages for c in page)
    by_page: dict[int, list[tuple[Cell, int]]] = {}
    n = 0
    for cell, new in zip(column, wanted):
        if _to_minor(cell.num) == new:
            continue
        by_page.setdefault(cell.page, []).append((cell, new))
        n += 1
    for page, edits in by_page.items():
        streams[page - 1] = rewrite(streams[page - 1], edits, grouping)

    new_truth = copy.deepcopy(truth)
    for row, new in zip(new_truth["ledger"]["rows"], wanted):
        row["balance"] = new
    new_truth["ledger"]["closing_balance"] = wanted[-1] if wanted else led["opening_balance"]
    new_truth["inconsistency"] = None
    new_truth["provenance"] = {
        "source": "AgamiAI/Indian-Bank-Statements",
        "modified_by_us": "balance column recomputed from the publisher's own amounts",
        "cells_rewritten": n,
        "grouping": grouping,
    }
    _save(pdf, streams, out_path)
    return BuildResult(truth["doc_id"], "repaired", out_path, new_truth, n,
                       pages=len(streams))


def repair(pdf_path: str, truth: dict[str, Any], out_path: str) -> BuildResult | None:
    """Correct the amounts that contradict the publisher's own balance column.

    The balance column and the header are left exactly as published -- they are the part
    of this corpus that is internally coherent -- and the transaction amounts are moved
    to whatever the balance column says they must have been. That is about 20 cells a
    document rather than 143, it needs no change to the opening or closing balance, and
    every balance on the page stays the publisher's own figure.

    Roughly 46% of the broken rows need their value in the *other* column, because the
    publisher printed a debit where the balance implies a credit or the reverse. Both
    layouts are handled: Type 1 clears one column's cell and writes into the empty block
    the generator already left in the other, and Type 2 keeps the single amount column
    and flips the ``CR``/``DR`` indicator beside it.
    """
    import copy

    pdf, streams, pages = _load_pages(pdf_path)
    column = locate_column(pages, balance_sequence(truth))
    if column is None:
        return None
    cells = _amount_cells_by_row(led := truth["ledger"], pages)
    if not cells:
        return None

    geom = _column_geometry(cells, pages)
    grouping = detect_grouping(c for page in pages for c in page)
    rows = led["rows"]

    plan: list[tuple[int, int, str]] = []        # (page, side-effect edits) per page
    edits_by_page: dict[int, list[tuple[int, int, str]]] = {}
    changes: list[dict[str, Any]] = []

    prev = led["opening_balance"]
    for i, row in enumerate(rows):
        bal = row["balance"]
        want = bal - prev
        prev = bal
        have = (row["credit"] or 0) - (row["debit"] or 0)
        if want == have:
            continue

        want_side = "credit" if want > 0 else "debit"
        have_side = ("credit" if (row["credit"] or 0) else
                     "debit" if (row["debit"] or 0) else None)
        magnitude = abs(want)

        try:
            page, page_edits = _retarget_amount(
                streams, cells, geom, column[i], i,
                have_side=have_side, want_side=want_side,
                magnitude=magnitude, grouping=grouping)
        except _CannotRetarget:
            return None
        edits_by_page.setdefault(page, []).extend(page_edits)
        changes.append({"row": i, "from_side": have_side, "to_side": want_side,
                        "from": abs(have), "to": magnitude})

    for page, pieces in edits_by_page.items():
        streams[page - 1] = _apply(streams[page - 1], pieces)

    new_truth = copy.deepcopy(truth)
    for change in changes:
        r = new_truth["ledger"]["rows"][change["row"]]
        r["debit"] = change["to"] if change["to_side"] == "debit" else 0
        r["credit"] = change["to"] if change["to_side"] == "credit" else 0
    new_truth["inconsistency"] = None
    new_truth["provenance"] = {
        "source": "AgamiAI/Indian-Bank-Statements",
        "modified_by_us": (
            "transaction amounts corrected to the publisher's own balance column; "
            "the balance column, opening and closing balances are untouched"
        ),
        "cells_rewritten": len(changes),
        "direction_changes": sum(1 for c in changes
                                 if c["from_side"] != c["to_side"]),
        "grouping": grouping,
        "unmodified": ("dates, descriptions, reference codes, running balances, "
                       "opening and closing balances"),
    }
    _save(pdf, streams, out_path)
    return BuildResult(truth["doc_id"], "repaired", out_path, new_truth,
                       len(changes), pages=len(streams))


def tamper(
    pdf_path: str,
    truth: dict[str, Any],
    out_path: str,
    rng: random.Random,
    repaired_first: bool = True,
    delta: int | None = None,
) -> BuildResult | None:
    """Alter one printed amount and leave the balance column, recording what we changed.

    The document is repaired first, so that the only break in the result is the one we
    planted and detection is measured against a single known target rather than against
    a document that was already inconsistent in six other places.
    """
    import copy
    import tempfile

    base_truth = truth
    if repaired_first:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        rep = repair(pdf_path, truth, tmp_path)
        if rep is None:
            Path(tmp_path).unlink(missing_ok=True)
            return None
        pdf_path, base_truth = tmp_path, rep.truth

    pdf, streams, pages = _load_pages(pdf_path)
    led = base_truth["ledger"]
    grouping = detect_grouping(c for page in pages for c in page)

    cell_for_row = _amount_cells_by_row(led, pages)
    if not cell_for_row:
        return None

    candidates = [
        (i, side) for (i, side) in cell_for_row
        if (led["rows"][i].get(side) or 0) >= 1000
    ]
    if not candidates:
        return None
    rng.shuffle(candidates)

    for row_i, side in candidates:
        cell = cell_for_row[(row_i, side)]
        old = led["rows"][row_i].get(side) or 0
        if _to_minor(cell.num) != old:
            continue
        if delta is None:
            new = _plausible_alteration(old, rng)
        else:
            # A tamper of an exact size, for the question "how small a change does this
            # still catch". The chain then breaks by precisely ``delta``, which is what
            # makes a detection floor measurable rather than argued about.
            new = old + delta
            if new <= 0:
                continue
        if new == old:
            continue
        streams[cell.page - 1] = rewrite(streams[cell.page - 1], [(cell, new)], grouping)

        new_truth = copy.deepcopy(base_truth)
        new_truth["ledger"]["rows"][row_i][side] = new
        # The balance column is deliberately left as printed, so the chain breaks here.
        for row, src in zip(new_truth["ledger"]["rows"], base_truth["ledger"]["rows"]):
            row["balance"] = src["balance"]
        new_truth["inconsistency"] = {
            "kind": "tampered_amount",
            "detail": {"row": row_i, "side": side, "from": old, "to": new},
        }
        # Must describe what `repair` actually does. This said "balance column
        # recomputed from the publisher's amounts" for a while after the repair had been
        # changed to the opposite direction, so every tampered document carried a
        # provenance block that was false about which of its figures were ours.
        new_truth["provenance"] = {
            "source": "AgamiAI/Indian-Bank-Statements",
            "modified_by_us": (
                "transaction amounts corrected to the publisher's own balance column, "
                "then one printed amount altered by a known quantity"
            ),
            "tampered_row": row_i,
            "tampered_side": side,
            "unmodified": ("dates, descriptions, reference codes, running balances, "
                           "opening and closing balances, all other amounts"),
        }
        _save(pdf, streams, out_path)
        if repaired_first:
            Path(pdf_path).unlink(missing_ok=True)
        return BuildResult(truth["doc_id"], "tampered", out_path, new_truth, 1,
                           pages=len(streams))
    return None


def _plausible_alteration(minor: int, rng: random.Random) -> int:
    """A change a person might make to a statement, not a random number.

    Each option keeps the digit count where it can, because a tamper that changes the
    width of the field is one a reader could spot from the column alignment alone, and
    the point is to plant something only the arithmetic reveals.
    """
    digits = [c for c in str(minor) if c.isdigit()]
    options = []
    # bump a single leading digit
    s = str(minor)
    for i in range(min(2, len(s))):
        for d in "123456789":
            if d != s[i]:
                options.append(int(s[:i] + d + s[i + 1:]))
    # transpose two adjacent digits
    for i in range(len(s) - 1):
        if s[i] != s[i + 1]:
            options.append(int(s[:i] + s[i + 1] + s[i] + s[i + 2:]))
    options = [o for o in options if o > 0 and o != minor and len(str(o)) == len(s)]
    return rng.choice(options) if options else minor + 10_000


# ---------------------------------------------------------------------------
# verification


def rendered_right_edges(pdf_path: str) -> dict[int, list[float]]:
    """Where each amount actually ends on the rendered page, read back from the file.

    This is deliberately independent of the width model used to write the patch. If the
    model were wrong -- it was, at first, because the replacement was formatted in lakh
    grouping while the publisher groups in threes, so every long replacement carried an
    extra comma and sat 1.8 points to the left -- then comparing the model against itself
    would agree and the corpus would ship visibly misaligned columns. Measuring the
    result through a renderer is the only check that could catch that.

    The box has to be the *advance* box, not the inked one. A glyph's ink stops where its
    strokes stop, so ``...03`` and ``...09`` end a fraction of a point apart even when
    both are set on the same right margin, and comparing ink extents reports a column as
    having moved whenever a digit changed. Advance boxes come from the font metrics and
    are identical across a right-aligned column: on one page of the first document they
    take exactly three values, one per amount column.
    """
    import pypdfium2 as pdfium

    out: dict[int, list[float]] = {}
    doc = pdfium.PdfDocument(pdf_path)
    for i in range(len(doc)):
        tp = doc[i].get_textpage()
        runs: list[list[int]] = []
        current: list[int] = []
        for j in range(tp.count_chars()):
            if tp.get_text_range(j, 1).strip():
                current.append(j)
            elif current:
                runs.append(current)
                current = []
        if current:
            runs.append(current)

        edges: list[float] = []
        for run in runs:
            text = "".join(tp.get_text_range(j, 1) for j in run)
            if _AMOUNT.match(text.strip()):
                edges.append(round(tp.get_charbox(run[-1], loose=True)[2], 2))
        out[i + 1] = sorted(edges)
    return out


def read_back(pdf_path: str, truth: dict[str, Any]) -> str:
    """Read a built PDF's text layer and compare it with its truth. "" when they agree."""
    from benchmark.convert import statement_to_reading
    from benchmark.metrics import compare
    from probity import DocumentSpec
    from probity.proposers.base import Document
    from probity.proposers.text_layer import TextLayerProposer

    layout = str(truth.get("bank_id") or "").replace("agami_", "")
    spec_path = (Path(__file__).resolve().parents[2] / "examples" / "specs"
                 / f"agami_{layout}.yaml")
    if not spec_path.exists():
        return f"no spec for layout {layout!r}"
    spec = DocumentSpec.load(str(spec_path))
    proposal = TextLayerProposer().propose(
        Document(doc_id=str(truth.get("doc_id", "")), pdf_path=pdf_path), spec)
    cmp = compare(statement_to_reading(proposal.statement), truth)
    return "" if cmp.correct else cmp.explain(limit=3)


def verify(result: BuildResult, original_pdf: str) -> tuple[bool, list[str]]:
    """Re-read the file we wrote and refuse it unless it says what we intended.

    Three independent checks. The cells must still map to the ledger we claim is in the
    document; the arithmetic must be exactly as designed (no break at all for a repair,
    exactly the planted break for a tamper); and the rendered page must put the amount
    column back where the publisher had it. A patch that wrote the right value into the
    wrong cell, or the right cell at the wrong width, fails here rather than entering the
    benchmark.
    """
    from benchmark.external.agami import audit_ledger

    problems: list[str] = []
    _pdf, _streams, pages = _load_pages(result.out_pdf)
    led = result.truth["ledger"]

    column = locate_column(pages, balance_sequence(result.truth))
    if column is None:
        problems.append("balance column in the written file does not match the truth")

    # Not optional. This was written with a default of None and the build loop then called
    # verify() without it, so the one check that reads the rendered result was skipped on
    # every document while the build reported them all as verified.
    #
    # The check is "every amount sits on one of the column margins this document uses",
    # not "the amounts are where they were". A repair legitimately moves a value from the
    # debit column to the credit column, so comparing positions one by one would flag the
    # intended edits; what must never happen is a cell landing *between* columns, which is
    # what a wrong width produces.
    before = rendered_right_edges(original_pdf)
    margins = sorted({round(x, 1) for edges in before.values() for x in edges})
    after = rendered_right_edges(result.out_pdf)
    for page in sorted(after):
        off = [x for x in after[page]
               if not any(abs(x - m) <= 0.1 for m in margins)]
        if off:
            problems.append(
                f"page {page}: {len(off)} amount(s) not on any column margin, "
                f"e.g. {off[0]} (margins {margins})"
            )

    # The check that reads the figures back. Everything above establishes that the
    # truth file is internally as designed and that cells sit on the right margins; none
    # of it reads an amount or a direction out of the file that was written. This does:
    # the PDF is read through the framework's text-layer reader and compared, amount by
    # amount and date by date, with the truth it is supposed to carry.
    mismatch = read_back(result.out_pdf, result.truth)
    if mismatch:
        problems.append(f"the written file does not read back as its truth: {mismatch}")

    audit = audit_ledger(result.truth)
    if result.kind == "repaired":
        if not audit["chain_exact"]:
            problems.append(
                f"repaired document still breaks: {audit['n_problems']} rows, "
                f"closing_ok={audit['closing_ok']}"
            )
    else:
        detail = (result.truth.get("inconsistency") or {}).get("detail") or {}
        broken = audit["broken_rows"]
        if broken != [detail.get("row")]:
            problems.append(
                f"tampered document breaks at {broken}, planted at {detail.get('row')}"
            )
    return (not problems), problems


# ---------------------------------------------------------------------------


def build(directory: str | Path, out_dir: str | Path, limit: int | None = None,
          seed: int = 20261113, tamper_share: float = 0.5) -> dict[str, Any]:
    from benchmark.external.agami import audit_ledger, load_dir

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    docs = [d for d in load_dir(directory) if d.render == "digital"]

    # Interleave the two layouts before truncating. Sorting by doc_id and taking a prefix
    # gave a 24-document corpus that was entirely Type 1, so the column mode that needs
    # the CR/DR indicator -- the harder of the two, and the one a reader is most likely to
    # get backwards -- was never in the benchmark at all.
    by_layout: dict[str, list[Any]] = {}
    for doc in sorted(docs, key=lambda d: d.doc_id):
        by_layout.setdefault(doc.layout, []).append(doc)
    docs = [d for pair in zip(*(by_layout[k] for k in sorted(by_layout))) for d in pair]
    if limit:
        docs = docs[:limit]

    records, rejected = [], []
    for i, doc in enumerate(docs):
        # Alternate within each layout so repaired and tampered are balanced across both.
        kind = "tampered" if (i // len(by_layout)) % 2 else "repaired"
        stem = f"{doc.doc_id}-{kind}"
        out_pdf = str(out / f"{stem}.pdf")
        try:
            res = (tamper(doc.pdf, doc.truth, out_pdf, rng) if kind == "tampered"
                   else repair(doc.pdf, doc.truth, out_pdf))
        except Exception as exc:  # noqa: BLE001 - recorded, not hidden
            rejected.append({"doc_id": doc.doc_id, "kind": kind, "why": f"{type(exc).__name__}: {exc}"})
            continue
        if res is None:
            rejected.append({"doc_id": doc.doc_id, "kind": kind, "why": "could not map cells to the ledger"})
            continue
        ok, problems = verify(res, original_pdf=doc.pdf)
        if not ok:
            rejected.append({"doc_id": doc.doc_id, "kind": kind, "why": "; ".join(problems)})
            Path(out_pdf).unlink(missing_ok=True)
            continue
        res.truth["doc_id"] = stem
        truth_path = out / f"{stem}.truth.json"
        truth_path.write_text(json.dumps(res.truth, indent=1, ensure_ascii=False), encoding="utf-8")
        audit = audit_ledger(res.truth)
        records.append({
            "doc_id": stem, "bank_id": f"agami_{doc.layout}", "group": kind,
            "kind": kind, "render": "digital", "is_digital": True,
            "document": out_pdf, "digital_pdf": out_pdf, "truth": str(truth_path),
            "spec": f"examples/specs/agami_{doc.layout}.yaml",
            "inconsistency": res.truth.get("inconsistency"),
            "severity": "material" if kind == "tampered" else "none",
            "page_count": res.pages, "n_rows_ledger": len(res.truth["ledger"]["rows"]),
            "chain_exact": audit["chain_exact"],
            "broken_rows_in_source": audit["broken_rows"],
            "n_edits": res.n_edits,
            "sha256": _sha256_file(out_pdf),
        })

    manifest = {
        "split": "external_agami_built",
        "source": "AgamiAI/Indian-Bank-Statements",
        "built_by": "benchmark/external/agami_patch.py",
        "seed": seed,
        "documents": records,
        "rejected": rejected,
        "counts": {
            "repaired": sum(1 for r in records if r["kind"] == "repaired"),
            "tampered": sum(1 for r in records if r["kind"] == "tampered"),
            "rejected": len(rejected),
        },
    }
    # Inside the output directory, not beside it. Writing the manifest to ``out.parent``
    # under a fixed name meant two builds in the same parent -- a 24-document subset and
    # the full 200, say -- silently overwrote each other's manifest while both sets of
    # PDFs sat there intact, so a later run could score one corpus against the other's
    # index. The manifest now travels with the documents it describes.
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False),
                             encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="data/external/agami_built")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=20261113)
    args = ap.parse_args()
    m = build(args.dir, args.out, limit=args.limit, seed=args.seed)
    print(json.dumps(m["counts"], indent=1))
    print("manifest:", m["manifest_path"])
    for r in m["rejected"][:10]:
        print("rejected:", r["doc_id"], r["kind"], "-", r["why"])


if __name__ == "__main__":
    main()
