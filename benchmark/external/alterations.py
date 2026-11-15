"""Alterations of known kind, planted in a statement that ties.

Each function takes a clean statement (a PDF built by ``agami_patch.repair`` and its
truth) and writes an altered copy with a truth that says exactly what was changed. The
truth always describes what is PRINTED: an altered amount appears in the truth as
altered, because reading it faithfully is one thing and concluding about it another.

    amount            one amount changed, balances untouched           -> chain breaks
    balance           one balance changed                              -> chain breaks twice
    direction         one amount moved to the other side               -> chain breaks
    row_removed       one row whited out, balances untouched           -> chain breaks
    amount_adjusted   one amount changed AND every later balance and
                      the closing balance recomputed                   -> still ties
    row_adjusted      one row whited out AND later balances recomputed -> still ties
    text              one description replaced, no figure touched      -> still ties

The last three leave the arithmetic intact on purpose. A benchmark that only planted
alterations its own rule can see would be measuring a tautology.

``expected_rows`` in each truth lists the rows on which the running balance fails in a
perfect transcription of the altered document, which is what "located" is scored
against. For ``balance`` that is two rows: the altered one and the one after it.
"""

from __future__ import annotations

import copy
import random
from typing import Any

from . import agami_patch as ap

KINDS = ("amount", "balance", "direction", "row_removed", "amount_adjusted",
         "row_adjusted", "text")
#: Kinds whose altered document no longer satisfies the running balance.
DETECTABLE = {"amount", "balance", "direction", "row_removed"}


class CannotBuild(Exception):
    """This alteration cannot be planted in this document with certainty."""


def _load(pdf_path: str, truth: dict[str, Any]):
    pdf, streams, pages = ap._load_pages(pdf_path)
    led = truth["ledger"]
    column = ap.locate_column(pages, ap.balance_sequence(truth))
    cells = ap._amount_cells_by_row(led, pages)
    if column is None or not cells:
        raise CannotBuild("could not map cells to the ledger")
    grouping = ap.detect_grouping(c for page in pages for c in page)
    return pdf, streams, pages, led, column, cells, grouping


def _header_cell(pages, column, value: int):
    """The header cell (not in the balance column) printing ``value``, on page 1."""
    in_column = {id(c) for c in column}
    found = [c for c in pages[0] if id(c) not in in_column and ap._to_minor(c.num) == value]
    if len(found) != 1:
        raise CannotBuild(f"{len(found)} header cells print {value}; need exactly one")
    return found[0]


def _finish(pdf, streams, out_path: str, base: dict[str, Any], new_truth: dict[str, Any],
            kind: str, detail: dict[str, Any], expected_rows: list[int]) -> dict[str, Any]:
    new_truth["inconsistency"] = {"kind": kind, "detail": detail}
    new_truth["alteration"] = {"kind": kind, "detail": detail,
                               "detectable_by_arithmetic": kind in DETECTABLE,
                               "expected_rows": expected_rows}
    new_truth["provenance"] = {
        "source": "AgamiAI/Indian-Bank-Statements",
        "modified_by_us": ("transaction amounts corrected to the publisher's own balance "
                           f"column, then one alteration of kind '{kind}'"),
    }
    ap._save(pdf, streams, out_path)
    return new_truth


def _pick_row(led, cells, rng, *, lo: int = 3, margin: int = 3) -> tuple[int, str]:
    rows = [(i, side) for (i, side) in cells
            if lo <= i < len(led["rows"]) - margin and (led["rows"][i].get(side) or 0) >= 1000]
    if not rows:
        raise CannotBuild("no suitable row")
    return rng.choice(sorted(rows))


# ------------------------------------------------------------------------- amount

def amount(pdf_path, truth, out_path, rng: random.Random) -> dict[str, Any]:
    pdf, streams, pages, led, column, cells, grouping = _load(pdf_path, truth)
    i, side = _pick_row(led, cells, rng)
    old = led["rows"][i][side]
    new = ap._plausible_alteration(old, rng)
    if new == old:
        raise CannotBuild("alteration left the amount unchanged")
    cell = cells[(i, side)]
    streams[cell.page - 1] = ap.rewrite(streams[cell.page - 1], [(cell, new)], grouping)
    t = copy.deepcopy(truth)
    t["ledger"]["rows"][i][side] = new
    return _finish(pdf, streams, out_path, truth, t, "amount",
                   {"row": i, "side": side, "from": old, "to": new}, [i])


# ------------------------------------------------------------------------ balance

def balance(pdf_path, truth, out_path, rng: random.Random) -> dict[str, Any]:
    pdf, streams, pages, led, column, cells, grouping = _load(pdf_path, truth)
    i, _side = _pick_row(led, cells, rng)
    old = led["rows"][i]["balance"]
    new = ap._plausible_alteration(old, rng)
    if new == old or new <= 0:
        raise CannotBuild("alteration left the balance unchanged")
    cell = column[i]
    streams[cell.page - 1] = ap.rewrite(streams[cell.page - 1], [(cell, new)], grouping)
    t = copy.deepcopy(truth)
    t["ledger"]["rows"][i]["balance"] = new
    return _finish(pdf, streams, out_path, truth, t, "balance",
                   {"row": i, "from": old, "to": new}, [i, i + 1])


# ---------------------------------------------------------------------- direction

def direction(pdf_path, truth, out_path, rng: random.Random) -> dict[str, Any]:
    pdf, streams, pages, led, column, cells, grouping = _load(pdf_path, truth)
    geom = ap._column_geometry(cells, pages)
    order = sorted(cells)
    rng.shuffle(order)
    for i, side in order:
        if not (3 <= i < len(led["rows"]) - 3):
            continue
        magnitude = led["rows"][i].get(side) or 0
        if magnitude < 1000:
            continue
        other = "credit" if side == "debit" else "debit"
        try:
            page, pieces = ap._retarget_amount(
                streams, cells, geom, column[i], i, have_side=side, want_side=other,
                magnitude=magnitude, grouping=grouping)
        except ap._CannotRetarget:
            continue
        streams[page - 1] = ap._apply(streams[page - 1], pieces)
        t = copy.deepcopy(truth)
        t["ledger"]["rows"][i][side] = 0
        t["ledger"]["rows"][i][other] = magnitude
        return _finish(pdf, streams, out_path, truth, t, "direction",
                       {"row": i, "from_side": side, "to_side": other,
                        "amount": magnitude}, [i])
    raise CannotBuild("no row whose amount could be moved to the other side")


# ----------------------------------------------------------- amount, balances adjusted

def amount_adjusted(pdf_path, truth, out_path, rng: random.Random) -> dict[str, Any]:
    """Change one amount and carry the difference through every later balance."""
    pdf, streams, pages, led, column, cells, grouping = _load(pdf_path, truth)
    i, side = _pick_row(led, cells, rng)
    old = led["rows"][i][side]
    new = ap._plausible_alteration(old, rng)
    if new == old:
        raise CannotBuild("alteration left the amount unchanged")
    shift = (new - old) * (1 if side == "credit" else -1)
    if min(r["balance"] + shift for r in led["rows"][i:]) <= 0:
        # Try the same size of change in the other direction before giving up.
        mirrored = old - (new - old)
        if mirrored <= 0:
            raise CannotBuild("adjusted balances would go negative")
        new, shift = mirrored, -shift
        if min(r["balance"] + shift for r in led["rows"][i:]) <= 0:
            raise CannotBuild("adjusted balances would go negative")
    closing_cell = _header_cell(pages, column, led["closing_balance"])

    by_page: dict[int, list[tuple[ap.Cell, int]]] = {}
    by_page.setdefault(cells[(i, side)].page, []).append((cells[(i, side)], new))
    for j in range(i, len(led["rows"])):
        by_page.setdefault(column[j].page, []).append(
            (column[j], led["rows"][j]["balance"] + shift))
    by_page.setdefault(closing_cell.page, []).append(
        (closing_cell, led["closing_balance"] + shift))
    for page, edits in by_page.items():
        streams[page - 1] = ap.rewrite(streams[page - 1], edits, grouping)

    t = copy.deepcopy(truth)
    t["ledger"]["rows"][i][side] = new
    for j in range(i, len(led["rows"])):
        t["ledger"]["rows"][j]["balance"] += shift
    t["ledger"]["closing_balance"] += shift
    return _finish(pdf, streams, out_path, truth, t, "amount_adjusted",
                   {"row": i, "side": side, "from": old, "to": new,
                    "balances_shifted_by": shift}, [])


# --------------------------------------------------------------------- row removal

def _row_band(column, i: int) -> tuple[float, float]:
    """The vertical band of row ``i`` on its page: halfway to the rows above and below.

    A wrapped description starts above its row's baseline and a two-line date ends
    below it, so cells are found by band and not by one y value. Rows at the top or
    bottom of a page, and rows on page 1 (whose header uses its own coordinates), are
    not used.
    """
    cell = column[i]
    if cell.page == 1:
        raise CannotBuild("row is on the first page, next to the header")
    above = column[i - 1] if i > 0 and column[i - 1].page == cell.page else None
    below = column[i + 1] if i + 1 < len(column) and column[i + 1].page == cell.page else None
    if above is None or below is None:
        raise CannotBuild("row is first or last on its page")
    return (cell.y + below.y) / 2.0, (cell.y + above.y) / 2.0


_WRAPPED = None


def _band_objects(stream: str, lo: float, hi: float) -> list[list[tuple[int, int, str]]]:
    """Text objects printed in the band: for each, its (start, end, text) lines.

    These pages position a cell in one of two ways. Amounts, cheque numbers and blank
    cells are bare text objects whose ``Tm`` is in page coordinates. Dates and
    descriptions sit inside ``q 1 0 0 1 X Y cm q ... Q Q``, with a ``Tm`` relative to
    that origin, so their height on the page is ``Y`` plus the ``Tm`` offset.
    """
    import re

    global _WRAPPED
    if _WRAPPED is None:
        _WRAPPED = re.compile(
            r"q\s*\n1 0 0 1 (?P<cx>-?[\d.]+) (?P<cy>-?[\d.]+) cm\s*\nq\s*\n"
            r"(?P<inner>(?:(?!\nQ\s*\nQ).)*?BT\s*\n.*?\nET)\s*\nQ\s*\nQ", re.DOTALL)

    out, covered = [], []
    for w in _WRAPPED.finditer(stream):
        covered.append((w.start(), w.end()))
        inner, base = w.group("inner"), w.start("inner")
        tms, tjs = list(ap._TM.finditer(inner)), list(ap._TJ.finditer(inner))
        if len(tms) != 1 or not tjs:
            continue
        if not (lo < float(w.group("cy")) + float(tms[0].group("y")) <= hi):
            continue
        out.append([(base + tj.start("payload"), base + tj.end("payload"),
                     ap.pdf_unescape(tj.group("payload"))) for tj in tjs])
    for obj in ap._TEXT_OBJECT.finditer(stream):
        if any(a <= obj.start() < b for a, b in covered):
            continue
        body, base = obj.group("body"), obj.start("body")
        tms, tjs = list(ap._TM.finditer(body)), list(ap._TJ.finditer(body))
        if len(tms) != 1 or not tjs:
            continue
        if not (lo < float(tms[0].group("y")) <= hi):
            continue
        out.append([(base + tj.start("payload"), base + tj.end("payload"),
                     ap.pdf_unescape(tj.group("payload"))) for tj in tjs])
    return out


def _white_out(streams, column, i: int) -> None:
    cell = column[i]
    lo, hi = _row_band(column, i)
    objects = _band_objects(streams[cell.page - 1], lo, hi)
    if len(objects) < 4:
        raise CannotBuild("could not find the row's cells to white out")
    streams[cell.page - 1] = ap._apply(
        streams[cell.page - 1], [(a, b, "") for lines in objects for a, b, _t in lines])


def _drop_row(truth: dict[str, Any], i: int) -> dict[str, Any]:
    t = copy.deepcopy(truth)
    rows = t["ledger"]["rows"]
    del rows[i]
    for k, r in enumerate(rows):
        r["index"] = k
    if isinstance(t["ledger"].get("tx_count"), int):
        t["ledger"]["tx_count"] -= 1
    return t


def row_removed(pdf_path, truth, out_path, rng: random.Random) -> dict[str, Any]:
    pdf, streams, pages, led, column, cells, grouping = _load(pdf_path, truth)
    i, side = _pick_row(led, cells, rng)
    removed = dict(led["rows"][i])
    _white_out(streams, column, i)
    t = _drop_row(truth, i)
    # The row that followed now sits at index i, and its balance no longer follows.
    return _finish(pdf, streams, out_path, truth, t, "row_removed",
                   {"row": i, "removed": {k: removed.get(k) for k in
                                          ("date", "debit", "credit", "balance")}}, [i])


def row_adjusted(pdf_path, truth, out_path, rng: random.Random) -> dict[str, Any]:
    """White out one row and recompute every later balance so the statement still ties."""
    pdf, streams, pages, led, column, cells, grouping = _load(pdf_path, truth)
    i, side = _pick_row(led, cells, rng)
    removed = dict(led["rows"][i])
    shift = (removed.get("debit") or 0) - (removed.get("credit") or 0)
    if min(r["balance"] + shift for r in led["rows"][i + 1:]) <= 0:
        raise CannotBuild("adjusted balances would go negative")
    closing_cell = _header_cell(pages, column, led["closing_balance"])
    by_page: dict[int, list[tuple[ap.Cell, int]]] = {}
    for j in range(i + 1, len(led["rows"])):
        by_page.setdefault(column[j].page, []).append(
            (column[j], led["rows"][j]["balance"] + shift))
    by_page.setdefault(closing_cell.page, []).append(
        (closing_cell, led["closing_balance"] + shift))
    # Balance cells first: whiting out changes offsets on the removed row's page.
    for page, edits in by_page.items():
        streams[page - 1] = ap.rewrite(streams[page - 1], edits, grouping)
    _pdf2, _s2, pages2 = None, None, [ap.find_amount_cells(s, n + 1)
                                       for n, s in enumerate(streams)]
    column2 = ap.locate_column(
        pages2, [r["balance"] if k <= i else r["balance"] + shift
                 for k, r in enumerate(led["rows"])])
    if column2 is None:
        raise CannotBuild("could not re-locate the balance column after adjusting it")
    _white_out(streams, column2, i)

    t = _drop_row(truth, i)
    for r in t["ledger"]["rows"][i:]:
        r["balance"] += shift
    t["ledger"]["closing_balance"] += shift
    return _finish(pdf, streams, out_path, truth, t, "row_adjusted",
                   {"row": i, "removed": {k: removed.get(k) for k in
                                          ("date", "debit", "credit", "balance")},
                    "balances_shifted_by": shift}, [])


# --------------------------------------------------------------------------- text

def _squash(text: str) -> str:
    return "".join(str(text).split()).lower()


def text(pdf_path, truth, out_path, rng: random.Random) -> dict[str, Any]:
    """Replace one row's description with another row's, touching no figure."""
    pdf, streams, pages, led, column, cells, grouping = _load(pdf_path, truth)
    rows = led["rows"]
    order = [i for i in range(3, len(rows) - 3)]
    rng.shuffle(order)
    for i in order:
        want = str(rows[i].get("description") or "")
        if not want.strip():
            continue
        cell = column[i]
        try:
            lo, hi = _row_band(column, i)
        except CannotBuild:
            continue
        stream = streams[cell.page - 1]
        hit = [lines for lines in _band_objects(stream, lo, hi)
               if _squash("".join(t for _a, _b, t in lines)) == _squash(want)]
        if len(hit) != 1:
            continue
        donors = sorted({r["description"] for r in rows
                         if r.get("description") and _squash(r["description"]) != _squash(want)
                         and len(r["description"]) <= len(hit[0][0][2])})
        if not donors:
            continue
        new = rng.choice(donors)
        # The replacement goes on the first printed line; any further lines are cleared.
        pieces = [(hit[0][0][0], hit[0][0][1], ap.pdf_escape(new))]
        pieces += [(a, b, "") for a, b, _t in hit[0][1:]]
        streams[cell.page - 1] = ap._apply(stream, pieces)
        t = copy.deepcopy(truth)
        t["ledger"]["rows"][i]["description"] = new
        return _finish(pdf, streams, out_path, truth, t, "text",
                       {"row": i, "from": want, "to": new}, [])
    raise CannotBuild("no description that could be located and replaced")


BUILDERS = {"amount": amount, "balance": balance, "direction": direction,
            "row_removed": row_removed, "amount_adjusted": amount_adjusted,
            "row_adjusted": row_adjusted, "text": text}


def _rendered_as_intended(clean_pdf: str, out_pdf: str, truth: dict[str, Any]) -> str:
    """Checks that the read-back of figures does not cover. "" when all hold.

    Every amount on the rendered page must still end on one of the column margins the
    clean document uses, so a rewritten figure cannot have drifted between columns.
    For a text alteration, the row must read back with the new description and the old
    one must be gone from that row: the figures alone would not notice if the
    replacement had silently failed.
    """
    before = ap.rendered_right_edges(clean_pdf)
    margins = sorted({round(x, 1) for edges in before.values() for x in edges})
    for page, edges in ap.rendered_right_edges(out_pdf).items():
        off = [x for x in edges if not any(abs(x - m) <= 0.1 for m in margins)]
        if off:
            return f"page {page}: {len(off)} amount(s) not on any column margin"
    alteration = truth["alteration"]
    if alteration["kind"] == "text":
        from probity import DocumentSpec
        from probity.proposers.base import Document
        from probity.proposers.text_layer import TextLayerProposer

        layout = str(truth.get("bank_id") or "").replace("agami_", "")
        spec = DocumentSpec.load(str(ap.Path(__file__).resolve().parents[2] / "examples"
                                     / "specs" / f"agami_{layout}.yaml"))
        rows = TextLayerProposer().propose(
            Document(doc_id="check", pdf_path=out_pdf), spec).statement.rows
        i = alteration["detail"]["row"]
        got = _squash(rows[i].description.raw) if i < len(rows) else ""
        if got != _squash(alteration["detail"]["to"]):
            return f"row {i} does not read back with the replacement description"
    return ""


def alter(kind: str, pdf_path: str, truth: dict[str, Any], out_path: str,
          rng: random.Random, tries: int = 12) -> dict[str, Any]:
    """Plant one alteration, retrying on a different row if a row cannot take it.

    The result is read back through the text layer and must match its own truth, and its
    running balance must fail on exactly the rows the truth expects.
    """
    from .agami import audit_ledger

    last = "no attempt made"
    for _ in range(tries):
        try:
            t = BUILDERS[kind](pdf_path, truth, out_path, rng)
        except CannotBuild as exc:
            last = str(exc)
            continue
        mismatch = ap.read_back(out_path, t)
        if mismatch:
            last = f"does not read back as its truth: {mismatch[:160]}"
            continue
        broken = audit_ledger(t)["broken_rows"]
        if sorted(broken) != sorted(t["alteration"]["expected_rows"]):
            last = f"chain breaks at {broken}, expected {t['alteration']['expected_rows']}"
            continue
        problem = _rendered_as_intended(pdf_path, out_path, t)
        if problem:
            last = problem
            continue
        return t
    raise CannotBuild(f"{kind}: {last}")
