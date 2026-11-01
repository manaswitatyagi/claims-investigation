"""Vague stays vague. This is the test that stops the chronology risk."""
import pytest

from src.claim_model import date_value
from src.normalization.dates import (is_vague, normalise_date, ordering_confidence,
                                     days_between, sort_key)
from src.normalization.values import normalise_money


@pytest.mark.parametrize("raw,expected", [
    ("2026-02-14", "2026-02-14"),
    ("February 14, 2026", "2026-02-14"),
    ("Feb 14 2026", "2026-02-14"),
    ("2/14/2026", "2026-02-14"),
])
def test_explicit_dates_parse_to_day_precision(raw, expected):
    d = normalise_date(raw)["Date"]
    assert d["value"] == expected
    assert d["precision"] == "day"
    assert d["raw_expression"] == raw


@pytest.mark.parametrize("raw", [
    "that evening", "a few minutes later", "later that day", "around lunchtime",
    "shortly after", "sometime last week", "That evening, after I had my tea",
])
def test_vague_expressions_never_acquire_a_value(raw):
    d = normalise_date(raw)["Date"]
    assert d["precision"] == "vague"
    assert d["value"] is None, "inventing a timestamp is a chronology error"
    assert d["raw_expression"] == raw


def test_unparseable_input_defaults_to_vague_rather_than_guessing():
    d = normalise_date("banana o'clock")["Date"]
    assert d["precision"] == "vague"
    assert d["value"] is None


def test_constructing_a_vague_date_with_a_value_is_refused():
    with pytest.raises(ValueError, match="invented precision"):
        date_value("2026-02-14", "vague", "that evening")


def test_partial_precision_is_approximate_not_exact():
    assert ordering_confidence(normalise_date("2026-02")) == "approximate"
    assert ordering_confidence(normalise_date("2026")) == "approximate"
    assert ordering_confidence(normalise_date("2026-02-14")) == "exact"
    assert ordering_confidence(normalise_date("that evening")) == "unorderable"


def test_vague_dates_have_no_sort_key():
    assert sort_key(normalise_date("that evening")) is None
    assert sort_key(normalise_date("2026-02-14")) == "2026-02-14"


def test_invalid_calendar_dates_are_not_accepted():
    assert normalise_date("2026-02-30")["Date"]["precision"] == "vague"


def test_date_arithmetic():
    assert days_between("2026-02-14", "2026-02-20") == 6
    assert days_between("2026-02-20", "2026-02-14") == -6


def test_money():
    assert normalise_money("$3,200.50")["Money"]["amount"] == 3200.50
    assert normalise_money("not money") is None
