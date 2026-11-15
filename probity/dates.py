"""Strict date parsing. The format comes from the document spec, never from a guess.

03/04 is March in one country and April in another. A parser that decides for itself
produces a plausible wrong date, which is the definition of a silent error, so probity
refuses: a cell that does not match the declared format fails and is reported.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Final

_MONTHS: Final[dict[str, int]] = {}
# English, Spanish, Portuguese, French, Dutch, German and Italian abbreviations. A
# statement printed in a language the parser does not know produces an unreadable date,
# which refuses the document; adding the language is a one-line change here.
for _names, _idx in [
    (("jan", "ene", "gen", "janv", "january", "enero", "januar", "januari",
      "gennaio", "janvier"), 1),
    (("feb", "fev", "febr", "fév", "fevr", "february", "febrero", "fevereiro",
      "février", "februar", "februari", "febbraio"), 2),
    (("mar", "mars", "mrt", "march", "marzo", "março", "marco", "märz", "maart"), 3),
    (("apr", "abr", "avr", "april", "abril", "avril", "aprile"), 4),
    (("may", "mai", "mayo", "mei", "magg", "maio", "maggio"), 5),
    (("jun", "juin", "juni", "giu", "june", "junio", "junho", "giugno"), 6),
    (("jul", "juil", "juli", "lug", "july", "julio", "julho", "juillet", "luglio"), 7),
    (("aug", "ago", "aout", "août", "august", "agosto", "augustus"), 8),
    (("sep", "sept", "set", "september", "septiembre", "setembro", "septembre",
      "settembre"), 9),
    (("oct", "out", "okt", "ott", "october", "octubre", "outubro", "octobre",
      "oktober", "ottobre"), 10),
    (("nov", "november", "noviembre", "novembro", "novembre"), 11),
    (("dec", "dic", "dez", "déc", "december", "diciembre", "dezembro", "décembre",
      "dezember", "dicembre"), 12),
]:
    for _n in _names:
        _MONTHS[_n] = _idx


class DateParseError(ValueError):
    def __init__(self, code: str, raw: str, detail: str = "") -> None:
        self.code = code
        self.raw = raw
        self.detail = detail
        super().__init__(f"{code}: {raw!r}" + (f" ({detail})" if detail else ""))


# Supported directives, deliberately few. %b accepts the abbreviated month names of the
# locales we ship; %y maps 00-69 to 2000-2069 and 70-99 to 1970-1999.
_DIRECTIVES: Final[dict[str, str]] = {
    "%d": r"(?P<d>\d{1,2})",
    "%m": r"(?P<m>\d{1,2})",
    "%Y": r"(?P<Y>\d{4})",
    "%y": r"(?P<y>\d{2})",
    # Accented letters and an optional abbreviating full stop: "août", "janv.", "déc."
    "%b": r"(?P<b>[A-Za-zÀ-ÖØ-öø-ÿ]{3,9}\.?)",
}


def _compile(fmt: str) -> re.Pattern[str]:
    out, i = [], 0
    while i < len(fmt):
        if fmt[i] == "%" and i + 1 < len(fmt):
            key = fmt[i : i + 2]
            if key not in _DIRECTIVES:
                raise ValueError(f"unsupported date directive {key!r} in {fmt!r}")
            out.append(_DIRECTIVES[key])
            i += 2
        elif fmt[i] == " ":
            # A literal space in the format may be lost when text is extracted from a
            # PDF ("08 Aug 2026" can come back as "08Aug2026"), so spaces are optional.
            out.append(r"\s*")
            i += 1
        else:
            out.append(re.escape(fmt[i]))
            i += 1
    return re.compile(r"^\s*" + "".join(out) + _TIME_SUFFIX + r"\s*\.?\s*$")


#: A time of day may follow the date, and only a time of day.
#:
#: Statements that stamp a transaction print the clock under or beside the date, and a
#: reader that hands over the whole cell returns "01-01-2024 11:30:55". Refusing that
#: cost 129 of 162 rows on one external document whose every amount and balance had been
#: read correctly -- the date was right, and the strict parser threw the row away over a
#: trailing clock.
#:
#: This is not a relaxation of P6. A time of day cannot change which date was printed, so
#: accepting it adds no ambiguity. Arbitrary trailing text is still refused, because text
#: after a date is evidence that the match landed on the wrong thing -- which is the same
#: reasoning that keeps month names matching exactly rather than by prefix.
_TIME_SUFFIX = (
    r"(?:\s*,?\s*\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?"      # 11:30, 11:30:55, 11:30:55.1
    r"(?:\s*[APap]\.?[Mm]\.?)?"                            # optional AM/PM
    r"(?:\s*(?:[+-]\d{2}:?\d{2}|Z|[A-Z]{2,5}))?)?"         # optional offset or zone
)


_CACHE: dict[str, re.Pattern[str]] = {}


def parse_date(raw: str, fmt: str) -> date:
    """Parse ``raw`` strictly against ``fmt``. Raises :class:`DateParseError`."""
    if raw is None or not str(raw).strip():
        raise DateParseError("EMPTY", str(raw))
    text = " ".join(str(raw).split())
    pattern = _CACHE.setdefault(fmt, _compile(fmt))
    match = pattern.match(text)
    if not match:
        raise DateParseError("FORMAT_MISMATCH", raw, f"expected {fmt}")
    g = match.groupdict()
    if g.get("b") is not None:
        # Exact match only. Matching on a prefix accepted "januaryxx" as January,
        # which is precisely the plausible-but-wrong value a strict parser exists to
        # refuse; every abbreviation a statement actually prints is listed above.
        raw_month = g["b"].lower().rstrip(".")
        month = _MONTHS.get(raw_month)
        if month is None:
            raise DateParseError("UNKNOWN_MONTH_NAME", raw, g["b"])
    else:
        month = int(g["m"])
    year = int(g["Y"]) if g.get("Y") else (2000 + int(g["y"]) if int(g["y"]) < 70 else 1900 + int(g["y"]))
    day = int(g["d"])
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise DateParseError("IMPOSSIBLE_DATE", raw, str(exc)) from None


def parse_date_result(raw: str, fmt: str) -> tuple[date | None, str | None]:
    try:
        return parse_date(raw, fmt), None
    except DateParseError as exc:
        return None, exc.code


def format_date(value: date, fmt: str) -> str:
    """Render a date back into the document's own notation (for log messages)."""
    return value.strftime(fmt)
