"""Pairs 4 and 10 need no model. PRD §11 calls reaching for one first a
mis-sequenced build."""
from src.differences.deterministic import detect
from src.extraction.spans import resolve_and_drop


def test_driver_not_listed_is_detected_without_a_model(smoke_claim):
    facts, diffs = detect(smoke_claim)
    subjects = {d.subject for d in diffs}
    assert "driver_is_a_listed_driver" in subjects
    d = [x for x in diffs if x.subject == "driver_is_a_listed_driver"][0]
    assert d.detection_method == "deterministic"
    assert len(d.positions) == 2


def test_a_listed_driver_produces_no_difference(zero_conflict_claim):
    _, diffs = detect(zero_conflict_claim)
    assert [d for d in diffs if d.subject == "driver_is_a_listed_driver"] == []


def test_scheduled_vehicle_produces_no_difference(smoke_claim):
    _, diffs = detect(smoke_claim)
    assert [d for d in diffs if d.subject == "vehicle_is_a_scheduled_vehicle"] == []


def test_unscheduled_vehicle_is_detected(smoke_claim):
    smoke_claim.document("doc_fnol").structured_fields["vehicle_vin"] = "NOTONPOLICY0000000"
    _, diffs = detect(smoke_claim)
    assert any(d.subject == "vehicle_is_a_scheduled_vehicle" for d in diffs)


def test_report_before_loss_is_detected(smoke_claim):
    smoke_claim.claim_record["reported_date"] = "2026-02-01"
    _, diffs = detect(smoke_claim)
    assert any(d.subject == "report_date_precedes_loss_date" for d in diffs)


def test_normal_chronology_produces_no_difference(smoke_claim):
    _, diffs = detect(smoke_claim)
    assert not any(d.subject == "report_date_precedes_loss_date" for d in diffs)


def test_name_matching_is_exact_not_fuzzy(smoke_claim):
    """"R. Smith" is not silently resolved to "Robert Smith".

    Fuzzy matching here would be entity resolution applied silently, and a
    silent merge is invisible once it has happened.
    """
    smoke_claim.policy_record["listed_drivers"] = ["D. Whitfield"]
    _, diffs = detect(smoke_claim)
    assert any(d.subject == "driver_is_a_listed_driver" for d in diffs), \
        "an abbreviated name is a proposal for a human, not an automatic match"


def test_supporting_facts_carry_resolvable_citations(smoke_claim):
    facts, _ = detect(smoke_claim)
    kept, dropped = resolve_and_drop(facts, smoke_claim)
    assert dropped == [], "a deterministic difference must be checkable at source"
    assert len(kept) == len(facts)
