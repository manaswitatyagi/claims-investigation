"""Presentation DTO. The UI's entire contract.

The two tests that matter most are the last two: the view must never contain an
unverified assertion, and it must never contain a truth, materiality, or
credibility judgement.
"""
import json
import os

import pytest

from src.presentation.view_model import VIEW_VERSION, build_claim_view

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "data", "generated", "e2_ontology", "run_1")
FIX = os.path.join(ROOT, "data", "fixtures", "claim_001")


@pytest.fixture(scope="module")
def view():
    return build_claim_view(RUN, FIX)


def test_view_is_versioned(view):
    assert view["view_version"] == VIEW_VERSION


def test_sources_carry_counts_and_processing_route(view):
    ids = {s["source_id"] for s in view["sources"]}
    assert {"rec_anchor", "doc_fnol", "doc_statement"} <= ids
    for s in view["sources"]:
        assert s["verified_assertion_count"] > 0
        assert s["processing"] and s["verification_status"] == "verified"


def test_every_neighborhood_assertion_id_resolves(view):
    for n in view["neighborhoods"]:
        for aid in n["assertion_ids"]:
            assert aid in view["assertions"], "%s dangles" % aid


def test_every_assertion_carries_verified_evidence(view):
    """Nothing ungrounded reaches the screen (D-020 P2)."""
    for a in view["assertions"].values():
        ev = a["evidence"]
        assert ev["verified"] is True
        assert ev["quote"], "%s has no quote" % a["assertion_id"]
        assert ev["locator_kind"] in ("TextSpan", "Field")
        if ev["locator_kind"] == "TextSpan":
            assert ev["passage_id"] and ev["char_start"] is not None


def test_text_span_offsets_match_the_passage(view):
    """The quote shown to a user is the passage's own text at those offsets."""
    checked = 0
    for a in view["assertions"].values():
        ev = a["evidence"]
        if ev["locator_kind"] != "TextSpan" or not ev["passage_text"]:
            continue
        assert ev["passage_text"][ev["char_start"]:ev["char_end"]] == ev["quote"]
        checked += 1
    assert checked > 0


def test_relationships_are_precomputed_not_left_to_the_ui(view):
    """The frontend must have no reason, and no data, to infer a relationship."""
    for n in view["neighborhoods"]:
        if n["singleton"]:
            assert n["relationship"] is None
        else:
            assert n["relationship"] in ("CORROBORATING", "COMPATIBLE", "CONTRADICTORY")
        assert n["relationship_method"] in (
            "deterministic", "llm", "not_compared", "llm_invalid")


def test_the_planted_contradiction_is_visible(view):
    nb = [n for n in view["neighborhoods"]
          if n["predicate"] == "travel_direction" and n["entity_id"] == "vehicle_1"]
    assert len(nb) == 1
    assert nb[0]["relationship"] == "CONTRADICTORY"
    sources = {view["assertions"][a]["source_id"] for a in nb[0]["assertion_ids"]}
    assert sources == {"rec_anchor", "doc_fnol", "doc_statement"}


def test_corroboration_is_expressible(view):
    """The flat model has nowhere to put agreement. This view does."""
    rels = [n["relationship"] for n in view["neighborhoods"]]
    assert rels.count("CORROBORATING") >= 3


def test_timeline_keeps_both_axes_and_does_not_invent_precision(view):
    assert set(view["timeline"]) == {"occurred", "became_known"}
    for e in view["timeline"]["occurred"] + view["timeline"]["became_known"]:
        if e["ordering_confidence"] == "unorderable":
            assert e["when"] is None, "a vague expression must not acquire a timestamp"


def test_ungrouped_facts_are_surfaced_with_a_reason(view):
    assert view["ungrouped"]
    for u in view["ungrouped"]:
        assert u["reason"]


def test_no_data_section_carries_a_truth_or_materiality_judgement(view):
    """The whole safety property, checked against the payload the browser gets.

    Scoped to the DATA sections. `not_assessed` legitimately names materiality
    and credibility because its job is to say they were NOT assessed — D-020 P5,
    absence stated rather than implied. Asserting on the whole blob would forbid
    the disclaimer along with the thing it disclaims.
    """
    for section in ("assertions", "neighborhoods", "entities", "sources", "timeline"):
        blob = json.dumps(view[section]).lower()
        for banned in ("materiality", "credibility", "liability", "fraud", "suspicious",
                       "likely_true", "is_true", "confidence_score", "score"):
            assert banned not in blob, "%r reached view[%r]" % (banned, section)


def test_not_assessed_declares_what_was_not_judged(view):
    """The positive half: silence about materiality would be worse than a
    disclaimer, because an empty contradiction list would then be ambiguous."""
    joined = " ".join(view["not_assessed"]).lower()
    assert "materiality" in joined and "not assessed" in joined
    assert "credibility" in joined


def test_view_states_that_verified_is_not_true(view):
    text = view["claim"]["verified_means"].lower()
    assert "does not mean" in text or "not mean the assertion is true" in text
    assert view["claim"]["provenance_disclaimer"]
