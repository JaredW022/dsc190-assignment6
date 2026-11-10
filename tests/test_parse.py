from datetime import date

import pytest

from nldate import parse


def test_in_three_days():
    assert parse("in 3 days", today=date(2025, 12, 1)) == date(2025, 12, 4)


def test_previous_day():
    assert parse("previous day", today=date(2025, 12, 1)) == date(2025, 11, 30)


def test_yesterday_day():
    assert parse("yesterday", today=date(2025, 12, 1)) == date(2025, 11, 30)


def test_later_today():
    assert parse("later today", today=date(2025, 12, 1)) == date(2025, 12, 1)


def test_five_days_before_explicit_date():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_one_year_from_now():
    assert parse("one year from now", today=date(2025, 12, 1)) == date(2026, 12, 1)


def test_one_week_from_now():
    assert parse("one week from now", today=date(2025, 12, 1)) == date(2025, 12, 8)


def test_next_tuesday():
    # December 1, 2025 is a Monday.
    assert parse("next Tuesday", today=date(2025, 12, 1)) == date(2025, 12, 2)


def test_empty_string_raises_value_error():
    with pytest.raises(ValueError):
        parse("")


def test_unrecognized_text_raises_value_error():
    with pytest.raises(ValueError):
        parse("testing")


@pytest.mark.parametrize(
    ("expression", "reference", "expected"),
    [
        ("the day after tomorrow", date(2025, 12, 31), date(2026, 1, 2)),
        ("the day before yesterday", date(2026, 1, 1), date(2025, 12, 30)),
        (
            "two weeks from the day after tomorrow",
            date(2025, 12, 1),
            date(2025, 12, 17),
        ),
    ],
)
def test_day_phrases_with_the(expression, reference, expected):
    assert parse(expression, today=reference) == expected
