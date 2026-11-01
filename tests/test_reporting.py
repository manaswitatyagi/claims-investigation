"""Reporting layer: capture, classification, credit accounting, and the freeze.

None of this is part of the frozen set. These tests exist to prove that the
reporting layer observes the pipeline without altering it.
"""
import json
import os

import pytest

from src.evaluation.freeze import FreezeViolation, digest, load_manifest, verify
from src.evaluation.report import (CapturingClient, classify, credit_split,
                                   match_detail, rescore_open_questions)
from src.ingestion.loader import load_claim
from src.pipeline import run_pipeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "data", "fixtures")
RECORDINGS = os.path.join(ROOT, "src", "llm", "recordings")
STAGES = ["extraction", "grounding", "attribution", "normalization", "difference_proposal"]


def _run(fixture):
    from src.llm.client import RecordedClient
    claim = load_claim(os.path.join(FIXTURES, fixture, "claim.json"))
    gold = json.load(open(os.path.join(ROOT, "data", "gold", fixture + ".gold.json")))
    client = CapturingClient(RecordedClient.from_dir(os.path.join(RECORDINGS, fixture)))
    run = run_pipeline(claim, client)
    return claim, gold, run, client


# --- the freeze -------------------------------------------------------------

def test_freeze_manifest_covers_the_pipeline_and_the_fixture():
    files = load_manifest()["files"]
    assert len(files) == 22
    for required in ("src/llm/prompts.py", "src/pipeline.py",
                     "data/fixtures/claim_001/claim.json",
                     "data/gold/claim_001.gold.json"):
        assert required in files


def test_frozen_digests_are_unchanged():
    """The reporting layer must not have moved a single frozen byte."""
    for rel, expected in load_manifest()["files"].items():
        assert digest(rel) == expected, "%s drifted" % rel
    assert verify()["verified"] is True


def test_freeze_verification_fails_loudly_on_drift(tmp_path):
    m = load_manifest()
    m["files"]["src/pipeline.py"] = "0" * 16
    p = tmp_path / "m.json"
    p.write_text(json.dumps(m))
    with pytest.raises(FreezeViolation, match="not comparable"):
        verify(str(p))


def test_reporting_modules_are_not_in_the_frozen_set():
    files = load_manifest()["files"]
    for rel in ("src/evaluation/report.py", "src/evaluation/freeze.py",
                "tools/run_e1_live.py"):
        assert rel not in files, "%s must stay outside the freeze" % rel


# --- capture ----------------------------------------------------------------

def test_capturing_client_records_both_sides_of_every_exchange():
    _, _, _, client = _run("claim_001")
    assert [e["tag"] for e in client.exchanges] == [
        "extract__fnol.description_of_accident", "extract__statement.body", "differences"]
    for e in client.exchanges:
        assert e["request"]["system"] and e["request"]["user"]
        assert "response" in e


def test_capture_preserves_facts_the_drop_rule_removes():
    """A fabricated span vanishes from the result. It must not vanish from the
    record, or the failure becomes invisible."""
    _, _, run, client = _run("claim_000_smoke")
    assert run.dropped_facts
    raw = json.dumps([e["response"] for e in client.exchanges])
    assert "I was stopped at the light waiting to turn" in raw
    assert "stopped at the light waiting" not in json.dumps(run.result.to_dict())


def test_capturing_client_passes_model_identity_through():
    _, _, run, _ = _run("claim_001")
    assert run.result.to_dict()["prompt_version"] == "e1-v2"


# --- classification ---------------------------------------------------------

def test_every_planted_defect_is_classified_to_a_stage():
    claim, gold, run, _ = _run("claim_000_smoke")
    from src.evaluation.metrics import evaluate
    result = run.result.to_dict()
    metrics = evaluate(result, gold, run.dropped_facts)
    failures = classify(claim, result, gold, run.dropped_facts, metrics)
    kinds = {f["kind"] for f in failures}
    notes = {n for f in failures for n in (f["evidence"].get("all_notes") or [])}
    assert "text_absent_from_passage" in notes, "fabricated span"
    assert "offset_drift" in notes, "offset drift"
    assert "wrong_asserter" in kinds, "misattribution"
    assert all(f["stage"] in STAGES for f in failures)


def test_every_failure_carries_evidence_not_just_a_label():
    claim, gold, run, _ = _run("claim_000_smoke")
    from src.evaluation.metrics import evaluate
    result = run.result.to_dict()
    failures = classify(claim, result, gold, run.dropped_facts,
                        evaluate(result, gold, run.dropped_facts))
    for f in failures:
        assert f["evidence"], "%s has no evidence" % f["kind"]
        assert f["why"], "%s has no rationale" % f["kind"]
        assert f["confidence"] in ("confirmed", "suspected")


def test_grounding_failure_shows_what_the_passage_actually_holds():
    claim, gold, run, _ = _run("claim_000_smoke")
    from src.evaluation.metrics import evaluate
    result = run.result.to_dict()
    failures = classify(claim, result, gold, run.dropped_facts,
                        evaluate(result, gold, run.dropped_facts))
    attribution = [f for f in failures if f["kind"] == "wrong_asserter"]
    assert attribution
    ev = attribution[0]["evidence"]
    assert ev["passage_text_at_output_span"], "the reviewer needs the real text"
    assert ev["expected_asserter"] != ev["actual_asserter"]


def test_an_omission_caused_by_a_drop_names_its_root_cause():
    """Two failures for one error would point the reader at the wrong stage."""
    claim, gold, run, _ = _run("claim_000_smoke")
    from src.evaluation.metrics import evaluate
    result = run.result.to_dict()
    failures = classify(claim, result, gold, run.dropped_facts,
                        evaluate(result, gold, run.dropped_facts))
    linked = [f for f in failures if f["kind"] == "omitted_gold_fact_caused_upstream"]
    assert linked
    assert linked[0]["evidence"]["root_cause_stage"] == "grounding"
    assert linked[0]["evidence"]["dropped_notes"] == ["offset_drift"]


def test_a_clean_run_produces_no_failures():
    claim, gold, run, _ = _run("claim_001")
    from src.evaluation.metrics import evaluate
    result = run.result.to_dict()
    assert classify(claim, result, gold, run.dropped_facts,
                    evaluate(result, gold, run.dropped_facts)) == []


# --- D-034 credit accounting ------------------------------------------------

def test_credit_split_reports_both_paths():
    _, gold, run, _ = _run("claim_001")
    c = credit_split(gold, run.result.to_dict())
    for key in ("recall_via_one_to_one", "recall_via_containment",
                "precision_via_one_to_one", "precision_via_containment"):
        assert c[key] is not None
    assert c["recall_total"] == pytest.approx(
        c["recall_via_one_to_one"] + c["recall_via_containment"], abs=1e-4)
    assert c["precision_total"] == pytest.approx(
        c["precision_via_one_to_one"] + c["precision_via_containment"], abs=1e-4)


def test_credit_split_states_the_limitation():
    _, gold, run, _ = _run("claim_001")
    assert "spurious" in credit_split(gold, run.result.to_dict())["note"]


def test_match_detail_returns_objects_not_id_lists():
    _, gold, run, _ = _run("claim_001")
    d = match_detail(gold, run.result.to_dict())
    for key in ("one_to_one_matches", "co_extractions", "unmatched_gold",
                "unmatched_output", "differences_matched"):
        assert key in d
    assert d["one_to_one_matches"], "the clean recording matches"
    first = d["one_to_one_matches"][0]
    assert "assertion" in first["gold"] and "fact_id" in first["output"]


# ---------------------------------------------------------------------------
# Open-question re-scoring. The frozen metric matches on one-directional token
# overlap, which every expected_document_absent question clears on its shared
# template alone. These tests pin the corrected behaviour.
# ---------------------------------------------------------------------------

def _oq(qid, kind, question, expected_source):
    return {"question_id": qid, "kind": kind, "question": question,
            "expected_source": expected_source}


def test_the_frozen_matcher_credits_the_wrong_question():
    """Documents the defect the re-scorer exists to correct.

    If this ever fails, the frozen metric has been changed and the re-scorer's
    justification needs rewriting rather than quietly keeping.
    """
    from src.evaluation.metrics import _overlaps
    produced = "The file does not contain adjuster notes. Has it been requested or received?"
    wrong_gold = "The file does not contain a police report."
    assert _overlaps(wrong_gold, produced) is True, (
        "the frozen metric is expected to mis-credit here; see rescore_open_questions")


def test_rescore_pairs_each_question_with_its_own_document():
    gold = {"expected_open_questions": [
        {"match_key": "oq.police", "kind": "expected_document_absent",
         "question": "The file does not contain a police report.",
         "expected_source": "a police report"},
        {"match_key": "oq.notes", "kind": "expected_document_absent",
         "question": "The file does not contain adjuster notes.",
         "expected_source": "adjuster notes"},
    ]}
    result = {"open_questions": [
        _oq("oq_001", "expected_document_absent",
            "The file does not contain adjuster notes. Has it been requested or received?",
            "adjuster notes"),
    ]}
    r = rescore_open_questions(gold, result)
    assert r["open_question_recall"] == 0.5
    assert r["missed"] == ["oq.police"], "the absent police report must NOT be credited"
    assert r["matched"][0]["gold"] == "oq.notes"


def test_rescore_does_not_credit_a_question_of_another_kind():
    gold = {"expected_open_questions": [
        {"match_key": "oq.chased", "kind": "requested_never_received",
         "question": "An estimate was requested and never arrived.",
         "expected_source": "a repair estimate"},
    ]}
    result = {"open_questions": [
        _oq("oq_001", "expected_document_absent",
            "The file does not contain a repair estimate.", "a repair estimate"),
    ]}
    r = rescore_open_questions(gold, result)
    assert r["open_question_recall"] == 0.0, "kind must match even when the source does"


def test_rescore_prose_fallback_is_symmetric():
    """With no expected_source, a short produced question must not match a long
    gold one on shared template words alone."""
    gold = {"expected_open_questions": [
        {"match_key": "oq.long", "kind": "unresolved_by_file",
         "question": ("Whether the second vehicle was stationary or reversing at the "
                      "time of contact is not resolved by any document in the file."),
         "expected_source": None},
    ]}
    result = {"open_questions": [
        _oq("oq_001", "unresolved_by_file", "Not resolved by any document.", None),
    ]}
    assert rescore_open_questions(gold, result)["open_question_recall"] == 0.0


def test_one_produced_question_is_not_counted_twice():
    gold = {"expected_open_questions": [
        {"match_key": "oq.a", "kind": "expected_document_absent",
         "question": "The file does not contain adjuster notes.",
         "expected_source": "adjuster notes"},
        {"match_key": "oq.b", "kind": "expected_document_absent",
         "question": "The file does not contain adjuster notes.",
         "expected_source": "adjuster notes"},
    ]}
    result = {"open_questions": [
        _oq("oq_001", "expected_document_absent",
            "The file does not contain adjuster notes.", "adjuster notes"),
    ]}
    r = rescore_open_questions(gold, result)
    assert r["open_question_recall"] == 0.5, "a single output satisfies one gold row only"
