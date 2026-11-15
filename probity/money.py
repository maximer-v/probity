"""Exact money parsing: source string to integer minor units, never through a float.

Principle P1. A float cannot represent 0.10 exactly, so any path that touches one can
silently shift a cent. Every amount in probity is an integer count of the currency's
minor unit, carried together with its currency code.

Principle P2. Comparison is exact integer equality. There is no tolerance anywhere,
because a one-cent tolerance absorbs exactly the last-digit OCR confusion
(8 read as 3, 6 as 0) that the invariants exist to catch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

# ISO 4217 exceptions to the two-decimal default. Never hardcode x100.
MINOR_UNITS: Final[dict[str, int]] = {
    # zero-decimal currencies
    "BIF": 0, "CLP": 0, "DJF": 0, "GNF": 0, "ISK": 0, "JPY": 0, "KMF": 0,
    "KRW": 0, "PYG": 0, "RWF": 0, "UGX": 0, "UYI": 0, "VND": 0, "VUV": 0,
    "XAF": 0, "XOF": 0, "XPF": 0,
    # three-decimal currencies
    "BHD": 3, "IQD": 3, "JOD": 3, "KWD": 3, "LYD": 3, "OMR": 3, "TND": 3,
    # four-decimal
    "CLF": 4, "UYW": 4,
}
DEFAULT_MINOR_UNITS: Final[int] = 2


def minor_units(currency: str) -> int:
    """Number of decimal places for an ISO 4217 code."""
    return MINOR_UNITS.get(currency.upper(), DEFAULT_MINOR_UNITS)


class AmountParseError(ValueError):
    """Raised when a string cannot be parsed into an exact amount.

    Carries a machine-readable ``code`` so the trace log says *why* a cell failed
    rather than only that it failed.
    """

    def __init__(self, code: str, raw: str, detail: str = "") -> None:
        self.code = code
        self.raw = raw
        self.detail = detail
        super().__init__(f"{code}: {raw!r}" + (f" ({detail})" if detail else ""))


@dataclass(frozen=True, order=True)
class Money:
    """An exact amount: an integer number of minor units plus its currency."""

    minor: int
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.minor, int) or isinstance(self.minor, bool):
            raise TypeError(f"Money.minor must be int, got {type(self.minor).__name__}")
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError(f"currency must be an ISO 4217 alpha-3 code, got {self.currency!r}")

    @property
    def exponent(self) -> int:
        return minor_units(self.currency)

    def _check(self, other: "Money") -> None:
        if other.currency != self.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")

    def __add__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.minor + other.minor, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.minor - other.minor, self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.minor, self.currency)

    def __str__(self) -> str:
        exp = self.exponent
        sign = "-" if self.minor < 0 else ""
        digits = str(abs(self.minor)).rjust(exp + 1, "0")
        if exp == 0:
            return f"{sign}{digits}"
        return f"{sign}{digits[:-exp]}.{digits[-exp:]}"

    def format(self, locale: "Locale") -> str:
        """Render back into the locale's own notation (for log messages)."""
        exp = self.exponent
        sign = "-" if self.minor < 0 else ""
        digits = str(abs(self.minor)).rjust(exp + 1, "0")
        whole, frac = (digits[:-exp], digits[-exp:]) if exp else (digits, "")
        groups = []
        while len(whole) > 3:
            groups.insert(0, whole[-3:])
            whole = whole[:-3]
        groups.insert(0, whole)
        out = locale.thousands_sep.join(groups)
        if exp:
            out = out + locale.decimal_sep + frac
        return sign + out

    @classmethod
    def zero(cls, currency: str) -> "Money":
        return cls(0, currency)


@dataclass(frozen=True)
class Locale:
    """How a statement writes its numbers and dates."""

    name: str
    decimal_sep: str
    thousands_sep: str
    date_format: str = "%d/%m/%Y"
    # Some banks put the sign after the number ("1.234,56-") or in brackets.
    trailing_minus: bool = True
    parentheses_negative: bool = True
    # "CR"/"DR" and locale equivalents. Single-letter markers ("H"/"S" on German
    # statements) are deliberately not in the default set: they collide with currency
    # tokens, so a locale that needs them must opt in.
    credit_markers: tuple[str, ...] = ("CR", "CRED", "ABONO", "HABER")
    debit_markers: tuple[str, ...] = ("DR", "DB", "DEB", "CARGO", "DEBE")
    # Accepted digit groupings, each read from the right. Most of the world groups in
    # threes. The Indian system groups the lowest three and then in twos, so 12,345,678
    # is written 1,23,45,678 — but Indian statements print Western grouping too, often
    # in the same document, so en-IN accepts both. Validating grouping is what catches a
    # misread separator, so the rule is per locale rather than a global assumption.
    groupings: tuple[tuple[int, ...], ...] = ((3,),)


LOCALES: Final[dict[str, Locale]] = {
    "es-VE": Locale("es-VE", ",", ".", "%d/%m/%Y"),
    "es-ES": Locale("es-ES", ",", ".", "%d/%m/%Y"),
    "pt-BR": Locale("pt-BR", ",", ".", "%d/%m/%Y"),
    "en-US": Locale("en-US", ".", ",", "%m/%d/%Y"),
    "en-GB": Locale("en-GB", ".", ",", "%d/%m/%Y"),
    "de-DE": Locale("de-DE", ",", ".", "%d.%m.%Y"),
    "fr-FR": Locale("fr-FR", ",", " ", "%d/%m/%Y"),
    # Indian statements use lakh/crore grouping and Western grouping, sometimes both
    # in one document, so both are accepted here.
    "en-IN": Locale("en-IN", ".", ",", "%d/%m/%Y", groupings=((3,), (3, 2))),
}


def get_locale(name: str) -> Locale:
    try:
        return LOCALES[name]
    except KeyError:
        raise ValueError(f"unknown locale {name!r}; known: {sorted(LOCALES)}") from None


# Characters that behave as a minus sign in scanned or copy-pasted text.
_MINUS_CHARS = "-−‒–—‐－"
# Whitespace variants that appear as thousands separators.
_SPACE_CHARS = "     \t"
# Multi-character symbols are matched before the bare symbol class, so "R$" is removed
# whole rather than losing only its "$" and leaving a stray "R" behind.
_CURRENCY_TOKENS = re.compile(
    r"(?i)R\$|US\$|BS\.S"
    r"|\b(?:VES|VEF|VED|USD|EUR|BRL|GBP|JPY|MXN|COP|ARS|CLP|PEN|INR|BS|RS)\.?(?![A-Za-z])"
    r"|[$€£¥₡₲₱₦₹﷼]"
)


def normalise_numeric_text(raw: str) -> str:
    """Collapse the cosmetic variation that scanners and copy-paste introduce.

    Used by the grounding engine so that "1.234,56" on the page and the value the
    proposer reported compare equal without either being parsed as a number.
    """
    out = raw
    for ch in _MINUS_CHARS:
        out = out.replace(ch, "-")
    for ch in _SPACE_CHARS:
        out = out.replace(ch, " ")
    return " ".join(out.split())


_CODE_RE = re.compile(r"(?i)\b(VES|VEF|VED|USD|EUR|BRL|GBP|JPY|MXN|COP|ARS|CLP|PEN|INR)\b")
_SYMBOL_CCY = {"€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR", "R$": "BRL"}


def _currency_mismatch(text: str, currency: str) -> str | None:
    """Return the currency the cell is labelled with, when it contradicts the spec."""
    want = currency.upper()
    found = {m.group(1).upper() for m in _CODE_RE.finditer(text)}
    for symbol, code in _SYMBOL_CCY.items():
        if symbol in text:
            found.add(code)
    other = {c for c in found if c != want}
    return sorted(other)[0] if other and not (found & {want}) else None


def _grouping_ok(groups: list[str], grouping: tuple[int, ...]) -> bool:
    """Do these separator-delimited groups match the locale's grouping rule?

    ``grouping`` is read from the right: ``(3,)`` means every group is three digits,
    ``(3, 2)`` means the lowest is three and the rest are pairs. The leading group may
    be shorter than its rule (1,234 has a leading group of one digit) but never longer.
    """
    if not groups or not groups[0] or not all(g.isdigit() for g in groups):
        return False
    sizes = [len(g) for g in groups][::-1]          # right to left
    for i, size in enumerate(sizes):
        expected = grouping[i] if i < len(grouping) else grouping[-1]
        if i == len(sizes) - 1:                     # the leading group
            if not 1 <= size <= expected:
                return False
        elif size != expected:
            return False
    return True


def _strip_marker(text: str, markers: tuple[str, ...]) -> tuple[str, bool]:
    """Remove the first leading or trailing marker found; report whether one matched."""
    for marker in markers:
        for pat in (rf"^{re.escape(marker)}\b", rf"\b{re.escape(marker)}$"):
            if re.search(pat, text):
                return re.sub(pat, "", text).strip(), True
    return text, False


def parse_amount(raw: str, locale: Locale, currency: str, *, allow_blank: bool = True) -> Money | None:
    """Parse an amount string into exact minor units.

    Returns ``None`` for a blank cell when ``allow_blank`` (an empty debit column on a
    credit row is information, not an error). Raises :class:`AmountParseError` with a
    reason code otherwise — it never guesses and never falls back to zero.
    """
    if raw is None:
        if allow_blank:
            return None
        raise AmountParseError("EMPTY", "")
    text = normalise_numeric_text(str(raw))
    if not text or text in {"-", "--"}:
        if allow_blank:
            return None
        raise AmountParseError("EMPTY", raw)

    negative = False

    # Parenthesised negatives: (1.234,56)
    if locale.parentheses_negative and text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    # CR / DR markers, in either position. A debit marker *asserts* that the amount is
    # negative; it does not toggle. Toggling made two redundant negative indicators
    # cancel, so "-10.00 DR" and "(10.00 DR)" both came out positive — a sign error
    # that parses cleanly and is exactly what the invariants are meant to catch
    # rather than produce.
    text, saw_debit = _strip_marker(text.upper(), locale.debit_markers)
    if not saw_debit:
        text, _ = _strip_marker(text, locale.credit_markers)

    # A currency label that disagrees with the declared currency means the cell is not
    # what the spec says it is. Silently discarding it turned "USD 10.00" into GBP.
    mismatch = _currency_mismatch(text, currency)
    if mismatch:
        raise AmountParseError("CURRENCY_MISMATCH", raw,
                               f"cell is labelled {mismatch}, spec says {currency}")
    text = _CURRENCY_TOKENS.sub("", text).strip()

    # Leading or trailing minus.
    if text.startswith("-"):
        negative = not negative
        text = text[1:].strip()
    if text.endswith("-"):
        if not locale.trailing_minus:
            raise AmountParseError("TRAILING_MINUS_NOT_ALLOWED", raw)
        negative = not negative
        text = text[:-1].strip()
    if text.startswith("+"):
        text = text[1:].strip()

    text = text.replace(" ", "")
    if not text:
        raise AmountParseError("NO_DIGITS", raw)
    if not re.fullmatch(r"[0-9" + re.escape(locale.decimal_sep + locale.thousands_sep) + r"]+", text):
        raise AmountParseError("UNEXPECTED_CHARS", raw, f"after cleaning: {text!r}")

    exp = minor_units(currency)
    dsep, tsep = locale.decimal_sep, locale.thousands_sep

    if dsep and text.count(dsep) > 1:
        raise AmountParseError("MULTIPLE_DECIMAL_SEPARATORS", raw)

    if dsep and dsep in text:
        whole, frac = text.split(dsep)
    else:
        whole, frac = text, ""

    if tsep and tsep in whole:
        groups = whole.split(tsep)
        # The separator must group the integer part exactly as the locale does.
        # Anything else means the separators were misread, which is precisely what we
        # want to surface rather than absorb.
        if not any(_grouping_ok(groups, rule) for rule in locale.groupings):
            raise AmountParseError(
                "BAD_THOUSANDS_GROUPING", raw,
                f"groups={groups}; {locale.name} accepts "
                + " or ".join("+".join(map(str, r)) for r in locale.groupings)
                + " from the right")
        whole = "".join(groups)
    if tsep and tsep in frac:
        raise AmountParseError("THOUSANDS_SEP_IN_FRACTION", raw)

    if not whole.isdigit() and whole != "":
        raise AmountParseError("NON_DIGIT_INTEGER_PART", raw, whole)
    if frac and not frac.isdigit():
        raise AmountParseError("NON_DIGIT_FRACTION", raw, frac)
    if not whole and not frac:
        raise AmountParseError("NO_DIGITS", raw)

    if len(frac) > exp:
        # Refuse rather than round: a third decimal in a EUR amount means the
        # separators were read wrongly, and rounding would hide it.
        raise AmountParseError(
            "TOO_MANY_DECIMALS", raw, f"{len(frac)} decimals, {currency} has {exp}"
        )

    minor = int((whole or "0") + frac.ljust(exp, "0"))
    if saw_debit:
        negative = True        # an explicit DR asserts the sign, it does not toggle it
    return Money(-minor if negative else minor, currency.upper())


def parse_amount_result(raw: str, locale: Locale, currency: str, **kw) -> tuple[Money | None, str | None]:
    """Non-raising variant: ``(money, None)`` or ``(None, error_code)``."""
    try:
        return parse_amount(raw, locale, currency, **kw), None
    except AmountParseError as exc:
        return None, exc.code
