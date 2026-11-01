"""Deterministic quote location (E1b).

The contract: code computes offsets from the model's verbatim quote. D-020 P2 is
unchanged — an unlocatable quote is still dropped, never hedged. These tests pin
the boundary between "tolerant of presentation" and "fuzzy", which is the line
that would quietly erode first.
"""
import pytest

from src.extraction.quote_locator import (ABSENT, AMBIGUOUS, EMPTY, EXACT,
                                          EXACT_ORDERED, RESOLVED, WHITESPACE,
                                          locate)

T = ("The claimant reports that their vehicle was traveling northbound.\n\n"
     "The road was wet.  The road was wet again later.")


def test_unique_quote_resolves_with_exact_offsets():
    r = locate(T, "their vehicle was traveling northbound")
    assert r.status == RESOLVED and r.method == EXACT
    assert T[r.char_start:r.char_end] == "their vehicle was traveling northbound"


def test_returned_text_is_the_passage_not_the_model_string():
    """The Citation quotes the source, so it can never disagree with it."""
    r = locate(T, "  their vehicle was traveling northbound  ")
    assert r.status == RESOLVED
    assert r.canonical_text == T[r.char_start:r.char_end]


def test_absent_quote_is_dropped_not_rescued():
    assert locate(T, "the vehicle was travelling south").status == ABSENT


def test_case_differences_are_not_forgiven():
    """Case is content, not presentation. Forgiving it is fuzzy matching."""
    assert locate(T, "the claimant reports").status == ABSENT


def test_paraphrase_is_not_rescued():
    assert locate(T, "the claimant said the car went north").status == ABSENT


def test_empty_quote():
    assert locate(T, "").status == EMPTY
    assert locate(T, "   ").status == EMPTY


# --- ambiguity --------------------------------------------------------------

def test_repeated_quote_is_ambiguous_not_silently_first():
    r = locate(T, "The road was wet")
    assert r.status == AMBIGUOUS and r.occurrences == 2


def test_reading_order_disambiguates_only_when_one_candidate_remains():
    first = T.index("The road was wet")
    r = locate(T, "The road was wet", search_from=first + 1)
    assert r.status == RESOLVED and r.method == EXACT_ORDERED
    assert r.char_start > first


def test_reading_order_does_not_disambiguate_when_several_remain():
    r = locate(T, "The road was wet", search_from=0)
    assert r.status == AMBIGUOUS, "two candidates ahead of the cursor is still ambiguous"


def test_ambiguity_is_dropped_rather_than_guessed():
    """Identical text in a question and an answer have different asserters.
    Guessing would produce a citation that resolves and misattributes."""
    passage = "ADJUSTER: you were stopped.\nCLAIMANT: I was moving.\nADJUSTER: you were stopped."
    assert locate(passage, "you were stopped").status == AMBIGUOUS


# --- whitespace tolerance ---------------------------------------------------

WS = "First para ends here.\n\nSecond para starts.  Double  spaced   words."


def test_quote_across_a_paragraph_break_maps_back_to_canonical_offsets():
    r = locate(WS, "First para ends here. Second para starts.")
    assert r.status == RESOLVED and r.method == WHITESPACE
    assert WS[r.char_start:r.char_end] == "First para ends here.\n\nSecond para starts."


def test_collapsed_internal_runs_map_back():
    r = locate(WS, "Double spaced words")
    assert r.status == RESOLVED
    assert WS[r.char_start:r.char_end] == "Double  spaced   words"


def test_whitespace_tolerance_does_not_leak_into_character_tolerance():
    """Only whitespace is forgiven. One wrong letter is still absent."""
    assert locate(WS, "First para ends hear. Second para starts.").status == ABSENT


# --- integration with the drop rule -----------------------------------------

def test_located_citations_survive_the_frozen_resolver(claim_001):
    """Code checks its own arithmetic: a locator bug must not be invisible."""
    from src.extraction.spans import resolve_and_drop
    from src.claim_model import Asserter, Citation, Fact, text_span

    p = claim_001.passage("statement.body")
    quote = "the turn was normal until the vehicle suddenly slid"
    r = locate(p.text, quote)
    assert r.status == RESOLVED

    f = Fact(fact_id="f1", assertion="x", asserter=Asserter(kind="claimant"),
             provenance="extracted",
             citations=[Citation("doc_statement", "v1",
                                 text_span("statement.body", r.char_start, r.char_end),
                                 r.canonical_text)])
    kept, dropped = resolve_and_drop([f], claim_001)
    assert len(kept) == 1 and not dropped


def test_e1b_prompt_differs_from_e1_in_exactly_one_rule():
    from src.llm import prompts as e1
    from src.llm import prompts_e1b as e1b
    a, b = e1.EXTRACT_SYSTEM.split("\n"), e1b.EXTRACT_SYSTEM.split("\n")
    changed = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(a) == len(b) and len(changed) == 1, "E1b must differ only in rule 1"
    assert "VERBATIM QUOTE REQUIRED" in b[changed[0]]
    assert e1b.DIFFERENCE_SYSTEM is e1.DIFFERENCE_SYSTEM
    assert e1b.DIFFERENCE_SCHEMA is e1.DIFFERENCE_SCHEMA


def test_e1b_schema_drops_offsets_and_keeps_everything_else():
    from src.llm import prompts as e1
    from src.llm import prompts_e1b as e1b
    a = e1.EXTRACT_SCHEMA["properties"]["facts"]["items"]["properties"]
    b = e1b.EXTRACT_SCHEMA["properties"]["facts"]["items"]["properties"]
    assert set(a) - set(b) == {"char_start", "char_end"}
    assert set(b) - set(a) == set()


def test_e1b_pipeline_matches_e1_on_the_deterministic_path(claim_001):
    """Nothing but extraction changed, so a null-model run must be identical."""
    from src.pipeline import run_pipeline as e1_run
    from src.pipeline_e1b import run_pipeline as e1b_run
    a, b = e1_run(claim_001).result.to_dict(), e1b_run(claim_001).result.to_dict()
    assert [f["fact_id"] for f in a["facts"]] == [f["fact_id"] for f in b["facts"]]
    assert a["header"] == b["header"] and a["timeline"] == b["timeline"]
    assert a["open_questions"] == b["open_questions"]
