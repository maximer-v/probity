"""Exact money parsing across locales, currencies and the notations banks really use."""

from __future__ import annotations

import pytest

from probity.money import (AmountParseError, Money, get_locale, minor_units,
                          normalise_numeric_text, parse_amount)

ES = get_locale("es-VE")
US = get_locale("en-US")
BR = get_locale("pt-BR")


@pytest.mark.parametrize("raw,locale,ccy,expected", [
    ("1.234,56", ES, "VES", 123456),
    ("1,234.56", US, "USD", 123456),
    ("0,01", ES, "EUR", 1),
    ("1.000.000,00", ES, "EUR", 100000000),
    ("12,34", ES, "EUR", 1234),
    ("999", US, "USD", 99900),
    ("1.234,56-", ES, "EUR", -123456),
    ("-1.234,56", ES, "EUR", -123456),
    ("(1.234,56)", ES, "EUR", -123456),
    ("1,234.56 CR", US, "USD", 123456),
    ("1,234.56 DR", US, "USD", -123456),
    ("Bs. 1.234,56", ES, "VES", 123456),
    ("$1,234.56", US, "USD", 123456),
    ("R$ 1.234,56", BR, "BRL", 123456),
    ("1 234,56", ES, "EUR", 123456),          # thin space as a thousands separator
    ("−1.234,56", ES, "EUR", -123456),   # unicode minus
])
def test_parses_exactly(raw, locale, ccy, expected):
    assert parse_amount(raw, locale, ccy).minor == expected


def test_zero_decimal_currency():
    assert parse_amount("1,234", US, "JPY").minor == 1234
    assert minor_units("JPY") == 0


def test_three_decimal_currency():
    assert parse_amount("1,234.567", US, "KWD").minor == 1234567
    assert minor_units("KWD") == 3


def test_never_goes_through_a_float():
    """0.1 + 0.2 != 0.3 in binary floating point; these must stay exact."""
    a = parse_amount("0,10", ES, "EUR")
    b = parse_amount("0,20", ES, "EUR")
    assert (a + b).minor == 30
    total = Money.zero("EUR")
    for _ in range(10):
        total = total + parse_amount("0,10", ES, "EUR")
    assert total.minor == 100          # a float loop lands on 0.9999999999999999


@pytest.mark.parametrize("raw", ["1.23.45", "12.34.56", "1.2345,67", "1.234.5,67"])
def test_rejects_bad_grouping(raw):
    """A thousands separator that does not group in threes was misread."""
    with pytest.raises(AmountParseError) as exc:
        parse_amount(raw, ES, "EUR")
    assert exc.value.code in {"BAD_THOUSANDS_GROUPING", "TOO_MANY_DECIMALS",
                              "MULTIPLE_DECIMAL_SEPARATORS"}


def test_refuses_too_many_decimals_rather_than_rounding():
    """A third decimal in a EUR amount means the separators were misread.

    Rounding here would hide exactly the error the invariants exist to catch.
    """
    with pytest.raises(AmountParseError) as exc:
        parse_amount("1.234,567", ES, "EUR")
    assert exc.value.code == "TOO_MANY_DECIMALS"


def test_blank_is_none_not_zero():
    """An empty debit column on a credit row is information, not a zero."""
    assert parse_amount("", ES, "EUR") is None
    assert parse_amount("   ", ES, "EUR") is None
    with pytest.raises(AmountParseError):
        parse_amount("", ES, "EUR", allow_blank=False)


def test_rejects_garbage_with_a_reason_code():
    for raw in ("abc", "12x34", "--"):
        try:
            value = parse_amount(raw, ES, "EUR", allow_blank=False)
        except AmountParseError as exc:
            assert exc.code
        else:
            assert value is None


def test_locale_confusion_is_a_failure_not_a_guess():
    """1,234.56 read with a decimal-comma locale must fail, not silently become 1.23."""
    with pytest.raises(AmountParseError):
        parse_amount("1,234.56", ES, "EUR")


def test_currency_mismatch_refused():
    with pytest.raises(ValueError):
        Money(100, "EUR") + Money(100, "USD")


def test_format_round_trip():
    m = parse_amount("1.234.567,89", ES, "EUR")
    assert m.format(ES) == "1.234.567,89"
    assert str(m) == "1234567.89"
    assert parse_amount(m.format(ES), ES, "EUR") == m


def test_negative_format_round_trip():
    m = Money(-123456, "EUR")
    assert m.format(ES) == "-1.234,56"
    assert parse_amount(m.format(ES), ES, "EUR") == m


def test_normalise_numeric_text():
    assert normalise_numeric_text("1 234,56") == "1 234,56"
    assert normalise_numeric_text("  a   b ") == "a b"


@pytest.mark.parametrize("raw,expected", [
    ("1,23,456.78", 12345678),        # lakh grouping
    ("12,34,56,789.00", 12345678900),  # crore grouping
    ("1,279,072.17", 127907217),       # Western grouping, also printed on Indian statements
    ("59,131.72", 5913172),
])
def test_indian_grouping_both_conventions(raw, expected):
    """en-IN statements print lakh grouping and Western grouping, sometimes in one file."""
    assert parse_amount(raw, get_locale("en-IN"), "INR").minor == expected


def test_lakh_grouping_is_rejected_outside_india():
    """Accepting it everywhere would absorb a genuinely misread separator."""
    with pytest.raises(AmountParseError) as exc:
        parse_amount("1,23,456.78", US, "USD")
    assert exc.value.code == "BAD_THOUSANDS_GROUPING"


def test_unknown_currency_code_is_refused():
    with pytest.raises(ValueError):
        Money(100, "ZZ")
    with pytest.raises(ValueError):
        Money(100, "usd")


@pytest.mark.parametrize("raw,fmt,expected", [
    ("15 janv. 2025", "%d %b %Y", "2025-01-15"),     # French, abbreviated with a stop
    ("8 août 2025", "%d %b %Y", "2025-08-08"),       # French, accented
    ("12 mei 2025", "%d %b %Y", "2025-05-12"),       # Dutch
    ("5 settembre 2025", "%d %b %Y", "2025-09-05"),  # Italian, full name
    ("01.05.2025", "%d.%m.%Y", "2025-05-01"),        # European dotted
])
def test_month_names_across_languages(raw, fmt, expected):
    """A statement printed in an unsupported language must not silently mis-date."""
    from probity.dates import parse_date
    assert parse_date(raw, fmt).isoformat() == expected


def test_a_month_name_must_match_exactly_not_by_prefix():
    """"januaryxx" parsing as January is a plausible wrong date, which is the one
    outcome a strict parser exists to prevent."""
    from probity.dates import DateParseError, parse_date

    with pytest.raises(DateParseError):
        parse_date("01 januaryxx 2026", "%d %b %Y")


@pytest.mark.parametrize("raw, fmt, expected", [
    ("01-01-2024 11:30:55", "%d-%m-%Y", "2024-01-01"),
    ("28/03/2024 11:59:00 PM", "%d/%m/%Y", "2024-03-28"),
    ("2024-01-01 09:05", "%Y-%m-%d", "2024-01-01"),
    ("01-01-2024 11:30:55 +0530", "%d-%m-%Y", "2024-01-01"),
    ("01-01-2024", "%d-%m-%Y", "2024-01-01"),
])
def test_a_time_of_day_may_follow_the_date(raw, fmt, expected):
    """A statement that stamps the clock on a transaction still prints one date.

    Refusing "01-01-2024 11:30:55" under %d-%m-%Y threw away 129 of 162 rows on an
    external document whose every amount and balance had been read correctly. A time
    cannot change which date was printed, so accepting it introduces no ambiguity.
    """
    from probity.dates import parse_date

    assert parse_date(raw, fmt).isoformat() == expected


@pytest.mark.parametrize("raw", [
    "01-01-2024 and some junk",
    "01-01-2024 extra",
    "01-01-2024 02-02-2024",
])
def test_but_arbitrary_text_after_a_date_is_still_refused(raw):
    """Text after a date says the match landed on the wrong thing. Only a clock is
    allowed to follow it; anything else is the ambiguity P6 exists to refuse."""
    from probity.dates import DateParseError, parse_date

    with pytest.raises(DateParseError):
        parse_date(raw, "%d-%m-%Y")
