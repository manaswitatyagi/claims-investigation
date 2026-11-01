"""Evaluation runner: matching, metrics, and the materiality guard."""
import json
import os

import pytest

from src.evaluation.matching import match_differences, match_facts, span_overlap
from src.evaluation.metrics import (MaterialityScoringAttempt, evaluate,
                                    guard_metric_name)
from src.evaluation.runner import run_once

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- the D-033 guard -------------------------------------------------------

@pytest.mark.parametrize("name", [
    "materiality_agreement", "difference_materiality", "importance_score",
    "severity_recall", "suspicion_rate", "credibility_accuracy",
])
def test_guard_refuses_materiality_metrics(name):
    with pytest.raises(MaterialityScoringAttempt):
        guard_metric_name(name)


def test_guard_allows_the_e1_metrics():
    for name in ("fact_recall", "span_exactness", "asserter_accuracy",
                 "difference_recall", "hallucination_rate"):
        guard_metric_name(name)


def test_materiality_intent_is_never_scored():
    """It is §12 human-study metadata. A model reproducing labels we authored
    measures our own consistency, not performance."""
    scored = run_once("claim_000_smoke", "recorded")
    blob = json.dumps({k: v for k, v in scored.items() if k != "_result"}).lower()
    assert "materiality" not in blob


# --- matching --------------------------------------------------------------

def test_span_overlap():
    assert span_overlap(0, 10, 0, 10) == 1.0
    assert span_overlap(0, 10, 20, 30) == 0.0
    # Jaccard over character ranges: intersection 5, union 15.
    assert span_overlap(0, 10, 5, 15) == pytest.approx(1 / 3)
    # Half-overlap on one side still clears the 0.30 match threshold.
    assert span_overlap(0, 10, 3, 10) > 0.30


def test_facts_in_different_passages_never_match():
    gold = [{"match_key": "g", "assertion": "x", "subject": "s", "provenance": "extracted",
             "asserter_kind": "claimant", "passage_id": "a.body",
             "span": {"char_start": 0, "char_end": 10, "quoted_text": "x"}}]
    out = [{"fact_id": "o", "assertion": "x", "subject": "s", "provenance": "extracted",
            "asserter": {"kind": "claimant"},
            "citations": [{"locator": {"TextSpan": {"passage_id": "b.body",
                                                    "char_start": 0, "char_end": 10}}}]}]
    assert match_facts(gold, out)["matches"] == []


def test_deterministic_facts_match_on_subject_and_field_path():
    gold = [{"match_key": "g", "assertion": "x", "subject": "loss_date",
             "provenance": "deterministic", "asserter_kind": "system_record",
             "field_path": "loss_date"}]
    out = [{"fact_id": "o", "assertion": "x", "subject": "loss_date",
            "provenance": "deterministic", "asserter": {"kind": "system_record"},
            "citations": [{"locator": {"Field": {"record": "claim_record",
                                                 "field_path": "loss_date"}}}]}]
    m = match_facts(gold, out)
    assert len(m["matches"]) == 1 and m["matches"][0]["score"] == 1.0


def test_difference_matching_uses_positions_not_subject_wording():
    fact_matches = [
        {"gold": {"match_key": "a"}, "output": {"fact_id": "x"}},
        {"gold": {"match_key": "b"}, "output": {"fact_id": "y"}},
    ]
    gold = [{"difference_id": "gd", "position_match_keys": ["a", "b"]}]
    out = [{"difference_id": "d1", "subject": "a completely different label",
            "positions": [{"fact_id": "x"}, {"fact_id": "y"}]}]
    m = match_differences(gold, out, fact_matches)
    assert len(m["matched"]) == 1 and m["missed"] == [] and m["spurious"] == []


def test_spurious_difference_is_reported():
    gold = []
    out = [{"difference_id": "d1", "positions": [{"fact_id": "x"}, {"fact_id": "y"}]}]
    assert len(match_differences(gold, out, [])["spurious"]) == 1


# --- metrics ---------------------------------------------------------------

def test_no_composite_score_is_emitted():
    scored = run_once("claim_000_smoke", "recorded")
    for banned in ("score", "overall", "composite", "total_score", "grade"):
        assert banned not in scored, "a single number would hide the failures that matter"


def test_undefined_ratios_are_none_not_zero_or_one():
    """A metric with no denominator is undefined. Reporting 1.0 would flatter
    the zero-conflict control; reporting 0.0 would libel it."""
    scored = run_once("claim_000_zero_conflict", "recorded")
    assert scored["difference_recall"] is None
    assert scored["difference_precision"] is None


def test_zero_conflict_control_reports_a_count(recorded_client):
    scored = run_once("claim_000_zero_conflict", "recorded")
    assert scored["is_zero_conflict_control"] is True
    assert scored["false_differences_on_zero_conflict_control"] == 0


def test_smoke_control_field_is_none_when_not_a_control():
    scored = run_once("claim_000_smoke", "recorded")
    assert scored["false_differences_on_zero_conflict_control"] is None


def test_fabricated_span_counts_as_hallucination_despite_being_dropped():
    """The drop rule must not silently flatter the model."""
    scored = run_once("claim_000_smoke", "recorded")
    assert scored["counts"]["dropped_as_fabricated_span"] >= 1
    assert scored["hallucination_rate"] > 0


def test_offset_drift_is_counted_separately_from_fabrication():
    scored = run_once("claim_000_smoke", "recorded")
    assert scored["counts"]["dropped_as_offset_drift"] >= 1


def test_misattribution_is_caught_by_asserter_accuracy():
    """The recording credits a witness statement to the claimant. The span
    resolves, so only this metric catches it."""
    scored = run_once("claim_000_smoke", "recorded")
    assert scored["asserter_accuracy"] < 1.0


def test_forbidden_detector_does_not_fire_on_the_opposite_assertion():
    """"moving" must not match a must-not-appear "parked": the one word that
    carries the meaning cannot be outvoted by shared scaffolding."""
    scored = run_once("claim_000_zero_conflict", "recorded")
    assert scored["detail"]["forbidden_hits"] == []


def test_forbidden_detector_does_not_fire_on_a_longer_containing_fact():
    """A fact reciting what a document does NOT establish shares most of its
    vocabulary with the forbidden claim that it DOES. Containment fires on it;
    a symmetric measure does not."""
    from src.evaluation.metrics import _forbidden_hits
    forbidden = [{"match_key": "f",
                  "assertion": "The claimant's account is inconsistent with the official "
                               "crash record."}]
    out = [{"fact_id": "o1",
            "assertion": "The FNOL states that it does not establish exact speed, exact point "
                         "of impact, whether the claimant's vehicle slid, whether anyone "
                         "witnessed the event, or whether the account matches the official "
                         "crash record."}]
    assert _forbidden_hits(forbidden, out) == []


def test_forbidden_detector_still_fires_on_a_genuine_restatement():
    from src.evaluation.metrics import _forbidden_hits
    forbidden = [{"match_key": "f",
                  "assertion": "The claimant stated that the vehicle was stopped at a traffic "
                               "light."}]
    out = [{"fact_id": "o1",
            "assertion": "The claimant stated the vehicle was stopped at a traffic light."}]
    assert len(_forbidden_hits(forbidden, out)) == 1


def test_claim_001_clean_recording_emits_no_forbidden_facts():
    scored = run_once("claim_001", "recorded")
    assert scored["detail"]["forbidden_hits"] == []
    assert scored["hallucination_rate"] == 0.0


def test_human_rated_metrics_are_not_approximated():
    scored = run_once("claim_000_smoke", "recorded")
    assert scored["specificity"] == "requires_human_rating"
    assert scored["open_question_usefulness"] == "requires_human_rating"


def test_invented_precision_is_zero_on_a_correct_run():
    scored = run_once("claim_000_smoke", "recorded")
    assert scored["invented_precision_count"] == 0


def test_deterministic_only_run_recalls_deterministic_facts_and_no_others():
    scored = run_once("claim_000_smoke", "null")
    assert scored["fact_precision"] == 1.0
    assert 0 < scored["fact_recall"] < 1.0
    assert scored["hallucination_rate"] == 0.0


# --- D-034: granularity must not be scored as error -------------------------

def _gold(key, quote, text, asserter="claimant"):
    i = text.index(quote)
    return {"match_key": key, "assertion": quote, "subject": "s",
            "provenance": "extracted", "asserter_kind": asserter,
            "passage_id": "p.body",
            "span": {"char_start": i, "char_end": i + len(quote), "quoted_text": quote}}


def _out(fid, quote, text, asserter="claimant"):
    i = text.index(quote)
    return {"fact_id": fid, "assertion": quote, "subject": "s",
            "provenance": "extracted", "asserter": {"kind": asserter},
            "citations": [{"locator": {"TextSpan": {
                "passage_id": "p.body", "char_start": i, "char_end": i + len(quote)}}}]}


SENTENCE = ("The claimant does not recall the exact distance, whether traction control "
            "activated, or whether there was a witness.")


def test_atomic_split_of_one_gold_fact_is_not_a_precision_penalty():
    """Gold authors the sentence as one fact; the model returns three."""
    gold = [_gold("g.whole", SENTENCE[:-1], SENTENCE)]
    out = [_out("o1", "the exact distance", SENTENCE),
           _out("o2", "whether traction control activated", SENTENCE),
           _out("o3", "whether there was a witness", SENTENCE)]
    m = match_facts(gold, out)
    credited = ({x["output"]["fact_id"] for x in m["matches"]}
                | {x["output"]["fact_id"] for x in m["co_extractions"]})
    assert credited == {"o1", "o2", "o3"}, "atomic sub-assertions are not false positives"
    assert m["unmatched_output"] == []
    assert m["unmatched_gold"] == [], "the gold fact is recalled by its parts"


def test_one_output_fact_covering_several_gold_facts_is_not_an_omission():
    """The mirror case: gold authors three, the model returns one spanning all."""
    gold = [_gold("g1", "the exact distance", SENTENCE),
            _gold("g2", "whether traction control activated", SENTENCE),
            _gold("g3", "whether there was a witness", SENTENCE)]
    out = [_out("o1", SENTENCE[:-1], SENTENCE)]
    m = match_facts(gold, out)
    assert m["unmatched_gold"] == [], "granularity is not an omission"
    assert m["unmatched_output"] == []


def test_a_fact_outside_every_gold_span_is_still_a_false_positive():
    """The relaxation must not swallow genuine noise."""
    other = "Something else entirely was written in another part of the passage."
    text = SENTENCE + " " + other
    gold = [_gold("g.whole", SENTENCE[:-1], text)]
    out = [_out("o1", "the exact distance", text),
           _out("o2", "Something else entirely", text)]
    m = match_facts(gold, out)
    assert [f["fact_id"] for f in m["unmatched_output"]] == ["o2"]


def test_containment_does_not_cross_passages():
    gold = [_gold("g", "the exact distance", SENTENCE)]
    out = [_out("o1", "the exact distance", SENTENCE)]
    out[0]["citations"][0]["locator"]["TextSpan"]["passage_id"] = "other.body"
    m = match_facts(gold, out)
    assert m["matches"] == [] and m["co_extractions"] == []


def test_asserter_is_still_scored_on_sub_assertions():
    """Attribution is checkable at any granularity, so a misattributed
    sub-assertion must not escape by being a sub-assertion."""
    gold = [_gold("g.whole", SENTENCE[:-1], SENTENCE)]
    out = [_out("o1", "the exact distance", SENTENCE),
           _out("o2", "whether there was a witness", SENTENCE, asserter="adjuster")]
    m = match_facts(gold, out)
    scored = {x["output"]["fact_id"]: x["asserter_correct"]
              for x in m["matches"] + m["co_extractions"]}
    assert scored["o1"] is True
    assert scored["o2"] is False, "a misattributed sub-assertion must still be caught"


def test_split_facts_still_resolve_a_difference():
    """A difference whose position lands on a sub-assertion must still match."""
    fact_matches = [{"gold": {"match_key": "a"}, "output": {"fact_id": "x"}}]
    co = [{"gold": {"match_key": "b"}, "output": {"fact_id": "y"},
           "relation": "output_within_gold"}]
    gold = [{"difference_id": "gd", "position_match_keys": ["a", "b"]}]
    out = [{"difference_id": "d1", "positions": [{"fact_id": "x"}, {"fact_id": "y"}]}]
    m = match_differences(gold, out, fact_matches, co)
    assert len(m["matched"]) == 1 and m["spurious"] == []
