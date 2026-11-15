"""The grounding engine: does this value actually appear on the page, there?

Grounding is the second, independent line of defence, and it catches the one error class
the invariants structurally cannot: a value *invented to make the totals balance*. Such a
value satisfies every accounting check by construction, because it was chosen to. The
only way to catch it is to go back to the pixels and the text layer and ask whether
anyone ever wrote it down.

The check is textual, not numeric: the normalised characters of the reported value must
appear inside (or very near) the reported box. Comparing numbers would let 1.234,56 match
a page that says 1234.56 when the locale says otherwise, which is a real OCR failure.
"""

from __future__ import annotations

import enum
import re
from datetime import date as date_cls
from dataclasses import dataclass, field as dc_field
from typing import Any, Iterable

from .money import Money, normalise_numeric_text
from .records import BBox, Field, Statement


class GroundingCode(enum.StrEnum):
    GROUNDED = "GROUNDED"                      # found inside the reported box
    GROUNDED_NEARBY = "GROUNDED_NEARBY"        # found within the tolerance band
    NO_BBOX = "NO_BBOX"                        # the proposer reported no location
    NOT_ON_PAGE = "NOT_ON_PAGE"                # the text appears nowhere on the page
    WRONG_PLACE = "WRONG_PLACE"                # the text is on the page, elsewhere
    BOX_EMPTY = "BOX_EMPTY"                    # nothing was written in that box
    BOX_SAYS_OTHERWISE = "BOX_SAYS_OTHERWISE"  # the box holds different characters
    NO_SOURCE = "NO_SOURCE"                    # no text layer or OCR tokens for the page
    SKIPPED = "SKIPPED"                        # the policy does not require grounding here


@dataclass(frozen=True)
class Token:
    """One word with its location, from the PDF text layer or from OCR."""

    text: str
    bbox: BBox
    source: str = "text_layer"

    @property
    def normalised(self) -> str:
        return normalise_numeric_text(self.text)


@dataclass
class PageIndex:
    """Searchable text for one page, from one or more sources."""

    page: int
    tokens: list[Token] = dc_field(default_factory=list)
    width: float = 0.0
    height: float = 0.0

    def text(self) -> str:
        return " ".join(t.normalised for t in self.tokens)

    def tokens_in(self, box: BBox, pad: float = 0.0) -> list[Token]:
        probe = BBox(box.page, box.x0 - pad, box.y0 - pad, box.x1 + pad, box.y1 + pad)
        return [t for t in self.tokens if probe.contains_centre_of(t.bbox)]

    def find(self, needle: str) -> list[Token]:
        """Tokens whose text contains the needle, plus runs of tokens that do together.

        Statements split "1.234,56" across tokens often enough (a space before the
        decimals, a currency symbol glued on) that a single-token search alone would
        report false ungrounded values.
        """
        needle = normalise_numeric_text(needle).replace(" ", "")
        if not needle:
            return []
        hits = [t for t in self.tokens if needle in t.normalised.replace(" ", "")]
        if hits:
            return hits
        # Two- and three-token runs, in reading order within a line.
        by_line: dict[int, list[Token]] = {}
        for t in self.tokens:
            by_line.setdefault(int(t.bbox.y0 // 3), []).append(t)
        for line in by_line.values():
            line.sort(key=lambda t: t.bbox.x0)
            for n in (2, 3):
                for i in range(len(line) - n + 1):
                    run = line[i:i + n]
                    joined = "".join(t.normalised for t in run).replace(" ", "")
                    if needle in joined:
                        return run
        return []


@dataclass
class DocumentIndex:
    """Every page's searchable text, keyed by page number."""

    pages: dict[int, PageIndex] = dc_field(default_factory=dict)
    sources: tuple[str, ...] = ()

    def page(self, n: int) -> PageIndex | None:
        return self.pages.get(n)

    def all_text(self) -> str:
        return "\n".join(p.text() for _, p in sorted(self.pages.items()))


@dataclass
class GroundingResult:
    field_name: str
    ok: bool
    code: GroundingCode
    probe: str = ""                     # the characters we looked for
    found_text: str | None = None       # what was actually in the box
    bbox: BBox | None = None
    matched_bbox: BBox | None = None
    iou: float = 0.0
    detail: dict[str, Any] = dc_field(default_factory=dict)

    @property
    def message(self) -> str:
        m = {
            GroundingCode.GROUNDED: "found where the proposer said it was",
            GroundingCode.GROUNDED_NEARBY: "found just outside the reported box",
            GroundingCode.NO_BBOX: "the proposer gave no location, so nothing can confirm it",
            GroundingCode.NOT_ON_PAGE: f"{self.probe!r} does not appear anywhere on the page",
            GroundingCode.WRONG_PLACE: f"{self.probe!r} is on the page but not at the reported place",
            GroundingCode.BOX_EMPTY: "nothing is written in the reported box",
            GroundingCode.BOX_SAYS_OTHERWISE: f"the box reads {self.found_text!r}, not {self.probe!r}",
            GroundingCode.NO_SOURCE: "no text layer or OCR tokens exist for this page",
            GroundingCode.SKIPPED: "grounding not required for this field class",
        }[self.code]
        return m

    def to_json(self) -> dict[str, Any]:
        return {"field": self.field_name, "ok": self.ok, "code": str(self.code),
                "probe": self.probe, "found_text": self.found_text,
                "bbox": self.bbox.to_json() if self.bbox else None,
                "matched_bbox": self.matched_bbox.to_json() if self.matched_bbox else None,
                "iou": round(self.iou, 3), "message": self.message, **self.detail}


def raw_represents_value(f: Field, locale, currency: str) -> bool:
    """Does the field's printed text actually parse back to the value it carries?

    Grounding searches for the *printed* spelling, which is right, but it means a
    proposer could report ``raw="90.00"`` beside ``value=8000`` and have the page
    confirm a number the field does not hold. Nothing else in the pipeline ties the two
    together, so the check belongs here: a field whose characters do not reproduce its
    own value is not grounded, whatever the page says.
    """
    from .money import Money, parse_amount_result

    if not f.raw:
        return True
    if isinstance(f.value, Money):
        parsed, err = parse_amount_result(str(f.raw), locale, currency)
        if err or parsed is None:
            return False
        return abs(parsed.minor) == abs(f.value.minor)
    if isinstance(f.value, date_cls):
        from .dates import parse_date_result
        for fmt in (locale.date_format, "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y"):
            parsed, _ = parse_date_result(str(f.raw), fmt)
            if parsed == f.value:
                return True
        return False
    return True


def probe_text(f: Field, locale) -> str:
    """The characters to look for on the page for this field.

    The *source* spelling wins when we have it. A value printed ``(250,00)`` or
    ``1.234,56 CR`` parses correctly but does not match the canonical rendering of the
    amount, so probing the canonical form makes a correctly-read value look ungrounded
    and sends a good document to a human. The canonical form is only a fallback for
    values that arrived without their original characters.
    """
    if f.raw:
        return str(f.raw)
    if isinstance(f.value, Money):
        return f.value.format(locale)
    return "" if f.value is None else str(f.value)


def ground_field(f: Field, index: DocumentIndex, locale, *,
                 pad: float = 2.0, nearby_pad: float = 14.0) -> GroundingResult:
    """Confirm one field against the page text. Never mutates the field's value."""
    probe = probe_text(f, locale)
    if not raw_represents_value(f, locale, _currency_of(f)):
        return GroundingResult(f.name, False, GroundingCode.BOX_SAYS_OTHERWISE, probe=probe,
                               found_text=str(f.raw), bbox=f.bbox,
                               detail={"why": "the printed text does not parse back to "
                                              "the value this field carries"})
    if f.bbox is None:
        return GroundingResult(f.name, False, GroundingCode.NO_BBOX, probe=probe)
    page = index.page(f.bbox.page)
    if page is None:
        return GroundingResult(f.name, False, GroundingCode.NO_SOURCE, probe=probe, bbox=f.bbox)
    if not probe:
        return GroundingResult(f.name, False, GroundingCode.BOX_EMPTY, probe=probe, bbox=f.bbox)

    needle = normalise_numeric_text(probe).replace(" ", "").lower()
    needle = _amount_needle(needle, f.name)
    in_box = page.tokens_in(f.bbox, pad=pad)
    box_text = _candidates(in_box)

    if needle and _numeric_match(needle, box_text, f.name):
        matched = _union([t.bbox for t in in_box]) if in_box else None
        return GroundingResult(f.name, True, GroundingCode.GROUNDED, probe=probe,
                               found_text=box_text or None, bbox=f.bbox, matched_bbox=matched,
                               iou=matched.iou(f.bbox) if matched else 0.0,
                               detail={"tokens_in_box": len(in_box)})

    near = page.tokens_in(f.bbox, pad=nearby_pad)
    near_text = _candidates(near)
    if needle and _numeric_match(needle, near_text, f.name):
        matched = _union([t.bbox for t in near])
        return GroundingResult(f.name, True, GroundingCode.GROUNDED_NEARBY, probe=probe,
                               found_text=near_text, bbox=f.bbox, matched_bbox=matched,
                               iou=matched.iou(f.bbox), detail={"pad": nearby_pad})

    elsewhere = page.find(probe)
    if elsewhere:
        matched = _union([t.bbox for t in elsewhere])
        return GroundingResult(f.name, False, GroundingCode.WRONG_PLACE, probe=probe,
                               found_text=box_text or None, bbox=f.bbox, matched_bbox=matched,
                               iou=matched.iou(f.bbox),
                               detail={"found_at": matched.to_json()})
    if not in_box:
        return GroundingResult(f.name, False, GroundingCode.BOX_EMPTY, probe=probe, bbox=f.bbox)
    return GroundingResult(f.name, False, GroundingCode.BOX_SAYS_OTHERWISE, probe=probe,
                           found_text=box_text[:160], bbox=f.bbox)


def _currency_of(f: Field) -> str:
    from .money import Money
    return f.value.currency if isinstance(f.value, Money) else "EUR"


_NUMBER_RUN = re.compile(r"[-+(]?[\d][\d.,]*[\d)]?|\d")

#: Separator used when joining the tokens found in a box. It must be a character that
#: cannot occur inside a number: joining tokens with nothing between them merges two
#: adjacent amounts into one run, so "3.454,93" and "8.011,48" become a single
#: "3.454,938.011,48" that matches neither. That turns correctly read values into
#: WRONG_PLACE failures and sends good documents to a human.
_JOIN = "\x1f"


def _amount_needle(needle: str, field_name: str) -> str:
    """The number out of an amount probe, without the currency printed beside it.

    A currency marker is not part of the number, and whether it travels with the value
    depends entirely on which reader produced it. The text-layer reader takes a cell's
    value tokens and returns ``6,086.63``; a model told to report the characters exactly
    as printed returns ``Rs. 6,086.63``. On the page those are two separate tokens, so
    the model's probe matched no complete token and could not be joined into one either,
    because ``rs.6,086.63`` is not a single number. Half the fields of a 98.8%-accurate
    model reading were reported as WRONG_PLACE for that reason alone -- values that were
    on the page, correct, and in the right cell.

    Stripping the marker does not weaken anything. What remains must still equal a
    complete numeric run with its own boundaries, so a claimed ``10.00`` still cannot
    ground itself against a printed ``110.00``; only the currency is discarded, and the
    currency is checked separately by the parser that produced the value.
    """
    if field_class(field_name) != "amount":
        return needle
    runs = _NUMBER_RUN.findall(needle)
    return max(runs, key=len) if runs else needle


def _candidates(tokens: list[Token]) -> str:
    """The text found in a box, with token boundaries preserved."""
    return _JOIN.join(t.normalised.replace(" ", "").lower() for t in tokens)


def _numeric_match(needle: str, haystack: str, field_name: str) -> bool:
    """Does the box really contain this value, as a whole number rather than a fragment?

    A plain substring test is not good enough and the failure is silent in the worst
    possible way: ``10.00`` is a substring of ``110.00``, and ``0.00`` is a substring of
    ``100.00``, so a value invented to make a statement balance can ground itself
    against a different number printed nearby. That defeats the one guarantee grounding
    exists to provide.

    For amount and date fields the match must therefore be against a complete numeric
    run in the box, with its own boundaries. Free text keeps the substring behaviour,
    because a description legitimately appears inside a longer narrative.
    """
    cls = field_class(field_name)
    pieces = [p for p in haystack.split(_JOIN) if p]
    if cls == "text":
        return needle in haystack.replace(_JOIN, "") or any(needle in p for p in pieces)
    if needle in pieces:
        return True
    # A value may be split across neighbouring tokens ("1.234" + ",56"), so short runs
    # are joined — but only when the join could be one number. Allowing any two or
    # three pieces to concatenate lets unrelated tokens manufacture a match: "1" next
    # to "10.00" would ground a claimed "110.00".
    joined_all = ["".join(pieces[i:i + n]) for n in (2, 3)
                  for i in range(max(0, len(pieces) - n + 1))]
    # Note: joined_all is deliberately *not* consulted for amounts. Any two adjacent
    # tokens concatenate into something, and accepting that would let unrelated pieces
    # manufacture a value. Amounts use the seam-checked list below.
    # For the numeric comparison below, keep only joins that could be one number that
    # was split while being extracted.
    joined = [j for n in (2, 3)
              for i in range(max(0, len(pieces) - n + 1))
              for j in ["".join(pieces[i:i + n])]
              if _plausible_split(pieces[i:i + n]) and _is_single_number(j)]

    if cls == "date":
        # A date may legitimately join across tokens ("18" + "Mar" + "2026"), so the
        # unfiltered joins apply here; the numeric filter below does not.
        haystack = _JOIN.join(pieces) + _JOIN + _JOIN.join(joined_all)
        # A date may contain letters ("18Mar2026"), so the numeric-run test does not
        # apply. What must be excluded is a date that is a fragment of a longer number:
        # "1/01/2026" inside "11/01/2026" is a different date. Only an adjacent *digit*
        # can do that. An adjacent letter comes from a label glued to the value
        # ("desde18/03/2026") and does not change what the date says.
        start = 0
        while True:
            i = haystack.find(needle, start)
            if i < 0:
                return False
            before = haystack[i - 1] if i > 0 else ""
            after = haystack[i + len(needle)] if i + len(needle) < len(haystack) else ""
            if not before.isdigit() and not after.isdigit():
                return True
            start = i + 1

    for run in _NUMBER_RUN.findall(_JOIN.join(pieces + joined)):
        if run == needle:
            return True
        # A bracket may be dropped by tokenisation, but a sign may not: a printed
        # -10.00 and a claimed 10.00 are different balances, and treating them as
        # interchangeable would let a sign error ground itself.
        if _sign_of(run) == _sign_of(needle) and run.strip("()") == needle.strip("()"):
            return True
    return False


def _plausible_split(parts: list[str]) -> bool:
    """Could these pieces be one number that extraction broke apart?

    A number is split at a separator, not through the middle of an integer: a cell
    reading 1.234,56 can arrive as "1.234" + ",56" or "1.234," + "56". It does not
    arrive as "1" + "10.00". Without this, two unrelated tokens sitting next to each
    other manufacture a value that is on the page only as an artefact of the join, and
    a claimed 110.00 grounds itself against a printed 1 and a printed 10.00.
    """
    for left, right in zip(parts, parts[1:]):
        if not (left.endswith((",", ".")) or right.startswith((",", "."))):
            return False
    return True


def _is_single_number(text: str) -> bool:
    """Could this joined text be one printed number rather than two run together?

    A number carries at most one decimal separator. Two complete amounts concatenated
    carry two, which is how "3.454,93" and "8.011,48" used to merge into a value that
    was on the page only as an artefact of the join.
    """
    body = text.strip("()+-")
    if not body or not any(c.isdigit() for c in body):
        return False
    if not all(c.isdigit() or c in ".," for c in body):
        return False
    # At most one group of two decimals, at the end.
    tail = body.rsplit(",", 1)[-1] if "," in body else body.rsplit(".", 1)[-1]
    return len(tail) <= 3 and body.count(",") + body.count(".") <= 4


def _sign_of(text: str) -> int:
    """-1 when the text reads as negative (leading or trailing minus, or brackets)."""
    t = text.strip()
    if not t:
        return 1
    if t.startswith("(") and t.endswith(")"):
        return -1
    if t.startswith("-") or t.endswith("-"):
        return -1
    return 1


def _union(boxes: list[BBox]) -> BBox:
    return BBox(boxes[0].page, min(b.x0 for b in boxes), min(b.y0 for b in boxes),
                max(b.x1 for b in boxes), max(b.y1 for b in boxes))


AMOUNT_FIELDS = {"debit", "credit", "balance", "opening_balance", "closing_balance", "carried_forward"}
DATE_FIELDS = {"date", "period_start", "period_end"}


def field_class(name: str) -> str:
    if name in AMOUNT_FIELDS:
        return "amount"
    if name in DATE_FIELDS:
        return "date"
    return "text"


@dataclass
class GroundingReport:
    results: list[GroundingResult]

    @property
    def failures(self) -> list[GroundingResult]:
        """Fields the policy required and could not confirm.

        A SKIPPED result is not a failure: the policy did not ask for that field class
        to be grounded, so reporting it would put noise at the top of every log and
        make ``first_failure`` point at a currency code instead of the broken row.
        """
        return [r for r in self.results
                if not r.ok and r.code is not GroundingCode.SKIPPED]

    def invented(self) -> list[GroundingResult]:
        """Values that appear nowhere on the page. The fingerprint of an invented value."""
        return [r for r in self.results
                if r.code in {GroundingCode.NOT_ON_PAGE, GroundingCode.BOX_SAYS_OTHERWISE,
                              GroundingCode.BOX_EMPTY}]

    def fraction_grounded(self) -> float:
        considered = [r for r in self.results if r.code is not GroundingCode.SKIPPED]
        if not considered:
            return 1.0
        return sum(1 for r in considered if r.ok) / len(considered)

    def codes(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[str(r.code)] = out.get(str(r.code), 0) + 1
        return dict(sorted(out.items()))

    def to_json(self) -> dict[str, Any]:
        return {"fraction_grounded": round(self.fraction_grounded(), 4),
                "codes": self.codes(),
                "failures": [r.to_json() for r in self.failures]}

    def explain(self, limit: int = 12) -> str:
        if not self.failures:
            return f"all {len(self.results)} fields grounded on the page"
        lines = [f"{len(self.failures)}/{len(self.results)} fields not grounded:"]
        for r in self.failures[:limit]:
            lines.append(f"  [{r.code}] {r.field_name}: {r.message}")
        if len(self.failures) > limit:
            lines.append(f"  ... and {len(self.failures) - limit} more")
        return "\n".join(lines)


def ground_statement(st: Statement, index: DocumentIndex, spec) -> GroundingReport:
    """Ground every field the acceptance policy cares about, and mark them.

    Fields outside the required classes are still checked when a box is available
    (the information is free and goes in the certificate), but they are marked SKIPPED
    when the policy does not require them, so the fraction is not diluted.
    """
    required = set(spec.acceptance.require_grounding_on)
    results: list[GroundingResult] = []
    for f in st.all_fields():
        if f.value is None:
            continue
        cls = field_class(f.name)
        res = ground_field(f, index, spec.locale)
        if cls not in required and not res.ok:
            res = GroundingResult(f.name, False, GroundingCode.SKIPPED, probe=res.probe,
                                  bbox=f.bbox, detail={"would_have_been": str(res.code)})
        f.grounded = res.ok
        f.grounding_detail = {"code": str(res.code), "iou": round(res.iou, 3)}
        results.append(res)
    return GroundingReport(results)
