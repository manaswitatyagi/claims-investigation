"""Output invariants. Each maps to a decision, and each raises rather than warns."""
import pytest

from src.claim_model import Asserter, Citation, Fact, Position, field_locator
from src.pipeline import run_pipeline
from src.synthesis_assembly import InvariantViolation, assert_invariants


def test_materiality_is_never_populated(smoke_claim, recorded_client):
    result = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.to_dict()
    assert result["differences"], "the fixture plants differences"
    for d in result["differences"]:
        assert d["materiality"] is None
        assert d["materiality_rationale"] is None


def test_a_populated_materiality_field_raises(smoke_claim, recorded_client):
    run = run_pipeline(smoke_claim, recorded_client("claim_000_smoke"))
    result = run.result

    class Leaky:
        def to_dict(self):
            d = result.to_dict()
            d["differences"][0]["materiality"] = "high"
            return d

    with pytest.raises(InvariantViolation, match="materiality"):
        assert_invariants(Leaky())


def test_not_assessed_always_states_materiality(smoke_claim, recorded_client):
    result = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.to_dict()
    assert result["not_assessed"]
    assert any("materiality" in n for n in result["not_assessed"]), \
        "an empty differences list must not be ambiguous with 'not assessed'"


def test_document_set_records_what_the_system_saw(smoke_claim, recorded_client):
    result = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.to_dict()
    ids = {d["document_id"] for d in result["document_set"]}
    assert ids == {"doc_fnol", "doc_statement", "doc_independent"}
    assert all(d["version"] for d in result["document_set"])


def test_no_unresolved_citation_reaches_the_output(smoke_claim, recorded_client):
    run = run_pipeline(smoke_claim, recorded_client("claim_000_smoke"))
    assert run.dropped_facts, "the recording deliberately contains bad spans"
    for f in run.result.to_dict()["facts"]:
        for c in f["citations"]:
            assert c["resolved"] is True


def test_dropped_facts_are_auditable_but_absent_from_the_result(smoke_claim, recorded_client):
    run = run_pipeline(smoke_claim, recorded_client("claim_000_smoke"))
    dropped_ids = {d["fact_id"] for d in run.dropped_facts}
    output_ids = {f["fact_id"] for f in run.result.to_dict()["facts"]}
    assert dropped_ids and not (dropped_ids & output_ids)


def test_every_difference_position_points_at_a_surviving_fact(smoke_claim, recorded_client):
    result = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.to_dict()
    fact_ids = {f["fact_id"] for f in result["facts"]}
    for d in result["differences"]:
        for p in d["positions"]:
            assert p["fact_id"] in fact_ids


def test_header_states_absence_explicitly(smoke_claim, recorded_client):
    result = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.to_dict()
    header = result["header"]
    assert set(header) == {"coverage", "loss_description", "jurisdiction",
                           "damages", "status", "reserve"}
    for name, field in header.items():
        assert field["state"] in ("present", "absent_from_file", "not_assessed")
        if field["state"] != "present":
            assert field["fact_ids"] == []
    assert header["jurisdiction"]["state"] == "absent_from_file", \
        "the fixture leaves jurisdiction null; that is an output, not silence"
    assert header["damages"]["state"] == "absent_from_file", \
        "no repair estimate exists at C3"


def test_header_fields_are_individually_cited(smoke_claim, recorded_client):
    result = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.to_dict()
    coverage = result["header"]["coverage"]
    assert coverage["state"] == "present" and coverage["fact_ids"]


def test_synthesis_id_is_stable_across_identical_runs(smoke_claim, recorded_client):
    a = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.synthesis_id
    b = run_pipeline(smoke_claim, recorded_client("claim_000_smoke")).result.synthesis_id
    assert a == b


def test_zero_conflict_control_produces_no_differences(zero_conflict_claim, recorded_client):
    """PRD §12.2 decision rule 1. If this fails, no other metric matters."""
    run = run_pipeline(zero_conflict_claim, recorded_client("claim_000_zero_conflict"))
    assert run.result.differences == []


def test_deterministic_only_run_records_a_null_model(smoke_claim):
    result = run_pipeline(smoke_claim).result.to_dict()
    assert result["model_id"] is None
    assert any("no model was run" in n for n in result["not_assessed"])
    assert result["facts"], "the deterministic path stands on its own"
