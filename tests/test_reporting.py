"""Reporting layer: capture, classification, credit accounting, and the freeze.

None of this is part of the frozen set. These tests exist to prove that the
reporting layer observes the pipeline without altering it.
"""
import json
import os

import pytest

from src.evaluation.freeze import FreezeViolation, digest, load_manifest, verify
from src.evaluation.report import (CapturingClient, classify, credit_split,
                                   match_detail)
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
