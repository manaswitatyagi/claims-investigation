"""Stage 6 (part) — NORMALIZE dates.

The rule that matters here is negative: a vague expression stays vague.

DOCMAP §2.2 — "a few minutes later", "that evening". These cannot be
normalised to a timestamp without inventing precision, and inventing precision
on a timeline is exactly the incorrect-chronology risk. `precision: "vague"`
with `raw_expression` preserved is how the system carries an unusable date
without either discarding it or falsifying it.

The default for anything unparseable is *also* vague. Guessing is the failure
mode; refusing to guess is not.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, Optional

from src.claim_model import date_value

#: Expressions that are inherently unanchored. Matching any of these means the
#: value is vague no matter what else is in the string.
VAGUE_MARKERS = (
    "that evening", "that night", "that morning", "that afternoon",
    "later that day", "earlier that day", "the next morning",
    "a few minutes", "a few hours", "a couple of", "some time",
    "sometime", "shortly after", "shortly before", "a while",
    "around lunchtime", "after lunch", "before lunch",
    "a little later", "right after", "just after", "just before",
    "at some point", "later on", "eventually", "recently",
)

_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_ISO_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_ISO_YEAR = re.compile(r"^(\d{4})$")
_US = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_LONG = re.compile(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$")
_LONG_MY = re.compile(r"^([A-Za-z]+)\s+(\d{4})$")


def is_vague(raw: str) -> bool:
    low = raw.strip().lower()
    return any(m in low for m in VAGUE_MARKERS)


def normalise_date(raw: str) -> Dict[str, Any]:
    """Return a `Date` normalised value for a raw expression.

    Never raises on unparseable input — returns `precision: "vague"`, which is
    the honest answer.
    """
    raw = (raw or "").strip()
    if not raw:
        return date_value(None, "vague", raw)

    if is_vague(raw):
        return date_value(None, "vague", raw)

    m = _ISO.match(raw)
    if m and _valid(int(m.group(1)), int(m.group(2)), int(m.group(3))):
        return date_value(raw, "day", raw)

    m = _US.match(raw)
    if m:
        mo, dy, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid(yr, mo, dy):
            return date_value("%04d-%02d-%02d" % (yr, mo, dy), "day", raw)

    m = _LONG.match(raw)
    if m:
        mo = _MONTHS.get(m.group(1).lower())
        if mo and _valid(int(m.group(3)), mo, int(m.group(2))):
            return date_value("%04d-%02d-%02d" % (int(m.group(3)), mo, int(m.group(2))),
                              "day", raw)

    m = _ISO_MONTH.match(raw)
    if m and 1 <= int(m.group(2)) <= 12:
        return date_value(raw + "-01", "month", raw)

    m = _LONG_MY.match(raw)
    if m:
        mo = _MONTHS.get(m.group(1).lower())
        if mo:
            return date_value("%04d-%02d-01" % (int(m.group(2)), mo), "month", raw)

    m = _ISO_YEAR.match(raw)
    if m:
        return date_value(raw + "-01-01", "year", raw)

    # Unparseable. Do not guess.
    return date_value(None, "vague", raw)


def _valid(year: int, month: int, day: int) -> bool:
    try:
        date(year, month, day)
        return True
    except ValueError:
        return False


def sort_key(normalised: Optional[Dict[str, Any]]) -> Optional[str]:
    """Sortable key, or None when the value cannot be ordered.

    None does not mean "drop the event" — it means the event is placed with
    `ordering_confidence: "unorderable"` and given no false position.
    """
    if not normalised or "Date" not in normalised:
        return None
    return normalised["Date"].get("value")


def ordering_confidence(normalised: Optional[Dict[str, Any]]) -> str:
    if not normalised or "Date" not in normalised:
        return "unorderable"
    precision = normalised["Date"].get("precision")
    if precision == "day":
        return "exact"
    if precision in ("month", "year"):
        return "approximate"
    return "unorderable"


def days_between(earlier: str, later: str) -> int:
    """Date arithmetic is code. An LLM never does this (PRD §10.4)."""
    a = date.fromisoformat(earlier)
    b = date.fromisoformat(later)
    return (b - a).days
