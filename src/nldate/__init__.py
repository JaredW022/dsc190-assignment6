import re
from calendar import monthrange
from datetime import date, timedelta

_DAY_OFFSETS = {
    "today": 0,
    "later today": 0,
    "now": 0,
    "yesterday": -1,
    "previous day": -1,
    "last day": -1,
    "tomorrow": 1,
    "next day": 1,
    "day before yesterday": -2,
    "day after tomorrow": 2,
}

_WEEKDAYS = {
    name: number
    for number, day in enumerate(
        ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    )
    for name in (day, day[:3])
}
_MONTHS = {
    name: number
    for number, month in enumerate(
        (
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ),
        start=1,
    )
    for name in (month, month[:3])
}
_MONTHS["sept"] = 9

_NUMBERS = {
    word: number
    for number, word in enumerate(
        (
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        )
    )
}
_NUMBERS.update({"a": 1, "an": 1})
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_UNIT = r"days?|weeks?|months?|years?"
_DURATION_PART = re.compile(rf"([a-z]+(?:[ -][a-z]+)?|[0-9]+) ({_UNIT})")
_DAY = r"([0-9]{1,2})(?:st|nd|rd|th)?"
_MONTH = r"([a-z]+)\.?"
_YEAR = r"(?:,? ([0-9]{4}))?"


def parse(s: str, today: date | None = None) -> date:
    """Convert an English date expression to a date using today as its reference."""
    reference = date.today() if today is None else today
    expression = " ".join(s.casefold().split())
    try:
        return _parse_expression(expression, reference)
    except (ValueError, OverflowError, RecursionError) as error:
        raise ValueError(f"Unrecognized or out-of-range date: {s!r}") from error


def _parse_expression(expression: str, today: date) -> date:
    if expression in _DAY_OFFSETS:
        return today + timedelta(days=_DAY_OFFSETS[expression])

    match = re.fullmatch(r"(?:(next|last|previous|this) )?([a-z]+)", expression)
    if match and match[2] in _WEEKDAYS:
        difference = _WEEKDAYS[match[2]] - today.weekday()
        if match[1] in {"last", "previous"}:
            difference = -(-difference % 7 or 7)
        elif match[1] == "next":
            difference = difference % 7 or 7
        elif match[1] != "this":
            difference %= 7
        return today + timedelta(days=difference)

    match = re.fullmatch(r"(next|last|previous|this) (week|month|year)", expression)
    if match:
        direction = {"next": 1, "last": -1, "previous": -1, "this": 0}[match[1]]
        return _shift(today, {match[2]: 1}, direction)

    match = re.fullmatch(r"(.+?) (before|after|from) (.+)", expression)
    if match:
        duration = _duration(match[1])
        anchor = _parse_expression(match[3], today)
        return _shift(anchor, duration, -1 if match[2] == "before" else 1)

    match = re.fullmatch(r"in (.+)|(.+?) (ago|later|hence)", expression)
    if match:
        return _shift(
            today, _duration(match[1] or match[2]), -1 if match[3] == "ago" else 1
        )

    return _absolute_date(expression, today.year)


def _absolute_date(expression: str, default_year: int) -> date:
    match = re.fullmatch(r"([0-9]{4})([-/])([0-9]{1,2})\2([0-9]{1,2})", expression)
    if match:
        return date(int(match[1]), int(match[3]), int(match[4]))

    match = re.fullmatch(r"([0-9]{1,2})([-/])([0-9]{1,2})\2([0-9]{4})", expression)
    if match:
        return date(int(match[4]), int(match[1]), int(match[3]))

    match = re.fullmatch(rf"{_MONTH} {_DAY}{_YEAR}", expression)
    if match and match[1] in _MONTHS:
        return date(int(match[3] or default_year), _MONTHS[match[1]], int(match[2]))

    match = re.fullmatch(rf"{_DAY} (?:of )?{_MONTH}{_YEAR}", expression)
    if match and match[2] in _MONTHS:
        return date(int(match[3] or default_year), _MONTHS[match[2]], int(match[1]))

    raise ValueError("Expected a date expression")


def _duration(expression: str) -> dict[str, int]:
    units: dict[str, int] = {}
    for part in re.split(r",\s*(?:and )?| and ", expression):
        match = _DURATION_PART.fullmatch(part)
        if not match:
            raise ValueError("Expected a number and a unit")
        unit = match[2].removesuffix("s")
        units[unit] = units.get(unit, 0) + _quantity(match[1])
    return units


def _quantity(word: str) -> int:
    if word.isdecimal():
        return int(word)
    if word in _NUMBERS:
        return _NUMBERS[word]
    if word in _TENS:
        return _TENS[word]
    first, separator, last = word.replace("-", " ").partition(" ")
    if separator and first in _TENS and last in _NUMBERS and 1 <= _NUMBERS[last] <= 9:
        return _TENS[first] + _NUMBERS[last]
    raise ValueError("Expected a number")


def _shift(anchor: date, units: dict[str, int], direction: int) -> date:
    months = 12 * units.get("year", 0) + units.get("month", 0)
    if months:
        year, month = divmod(
            anchor.year * 12 + anchor.month - 1 + direction * months, 12
        )
        month += 1
        # A calendar shift can land in a month with fewer days.
        anchor = date(year, month, min(anchor.day, monthrange(year, month)[1]))
    days = 7 * units.get("week", 0) + units.get("day", 0)
    return anchor + timedelta(days=direction * days)
