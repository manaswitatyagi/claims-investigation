"""Fixture and gold integrity.

Gold spans are character offsets into fixture passage text. Edit the text and
they break silently — every metric would then be computed against coordinates
that no longer point where they claim to. These tests make that failure loud.
"""
import json
import os
import re

import pytest

from src.ingestion.loader import load_claim, validate_against

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "data", "fixtures")
GOLD = os.path.join(ROOT, "data", "gold")

RUNNABLE = ["claim_000_smoke", "claim_000_zero_conflict", "claim_001"]
ALL_FIXTURES = sorted(d for d in os.listdir(FIXTURES)
                      if os.path.isdir(os.path.join(FIXTURES, d)))


@pytest.mark.parametrize("fixture", ALL_FIXTURES)
def test_every_fixture_has_a_gold_answer(fixture):
    assert os.path.exists(os.path.join(GOLD, fixture + ".gold.json"))


@pytest.mark.parametrize("fixture", ALL_FIXTURES)
def test_gold_answers_validate(fixture):
    gold = json.load(open(os.path.join(GOLD, fixture + ".gold.json")))
    assert validate_against("gold_answer.schema.json", gold) == []


@pytest.mark.parametrize("fixture", RUNNABLE)
def test_gold_spans_resolve_against_fixture_text(fixture):
    """The test that stops fixture drift from silently invalidating every metric."""
    claim = load_claim(os.path.join(FIXTURES, fixture, "claim.json"))
    gold = json.load(open(os.path.join(GOLD, fixture + ".gold.json")))
    checked = 0
    for f in gold["expected_facts"]:
        span = f.get("span")
        if not span:
            continue
        passage = claim.passage(f["passage_id"])
        assert passage is not None, "gold fact %s names an unknown passage" % f["match_key"]
        actual = passage.text[span["char_start"]:span["char_end"]]
        assert actual == span["quoted_text"], (
            "gold fact %s span drifted: expected %r, passage holds %r"
            % (f["match_key"], span["quoted_text"], actual))
        checked += 1
    assert checked > 0, "this fixture should carry span-cited gold facts"


@pytest.mark.parametrize("fixture", RUNNABLE)
def test_gold_match_keys_are_unique(fixture):
    gold = json.load(open(os.path.join(GOLD, fixture + ".gold.json")))
    keys = [f["match_key"] for f in gold["expected_facts"]]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("fixture", RUNNABLE)
def test_planted_differences_reference_real_gold_facts(fixture):
    gold = json.load(open(os.path.join(GOLD, fixture + ".gold.json")))
    keys = {f["match_key"] for f in gold["expected_facts"]}
    for d in gold["planted_differences"]:
        for mk in d["position_match_keys"]:
            assert mk in keys, "%s references unknown gold fact %s" % (d["difference_id"], mk)


@pytest.mark.parametrize("fixture", ALL_FIXTURES)
def test_every_fixture_declares_its_provenance(fixture):
    """D-003 — the disclaimer lives in the artifact, not only in a research note."""
    claim = json.load(open(os.path.join(FIXTURES, fixture, "claim.json")))
    prov = claim["provenance"]
    assert prov["documents_are_synthetic"] is True
    assert prov["disclaimer"].strip()


@pytest.mark.parametrize("fixture", ALL_FIXTURES)
def test_gold_answers_carry_a_disclaimer(fixture):
    gold = json.load(open(os.path.join(GOLD, fixture + ".gold.json")))
    assert gold["disclaimer"].strip()


def test_the_anchored_fixture_asserts_no_unverified_source():
    """CLAUDE.md forbids inventing datasets, sources, licences, or URLs.

    The supplied anchor file asserts no URL, licence, or retrieval date, so
    neither may this fixture. `source_name` records only what the supplier
    called it.
    """
    claim = json.load(open(os.path.join(FIXTURES, "claim_001", "claim.json")))
    anchor = claim["provenance"]["anchor"]
    for field in ("source_url", "licence", "retrieved_at"):
        assert anchor[field] is None, (
            "%s must stay unasserted until verified against a real source" % field)
    assert anchor["todo"], "the fixture must say what is still missing"


def test_no_person_level_demographics_reach_the_anchored_fixture():
    """The supplied usage constraint, enforced.

    Crash datasets are person-level records of real incidents. This fixture
    attaches invented statements to the events in them, which is a different act
    from analysing them.
    """
    banned = {"age", "sex", "gender", "race", "ethnicity", "ethnic_group",
              "date_of_birth", "dob", "birth_date", "drivers_license",
              "driver_license", "license_number", "person_id", "bac_result",
              "physical_condition", "injury_classification", "ems_agency",
              "hospital", "safety_equipment", "airbag_deployed"}
    claim = json.load(open(os.path.join(FIXTURES, "claim_001", "claim.json")))

    def walk(node, path="claim"):
        if isinstance(node, dict):
            for key, value in node.items():
                norm = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
                assert norm not in banned, (
                    "person-level attribute %r reached the fixture at %s" % (key, path))
                walk(value, path + "." + key)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, "%s[%d]" % (path, i))

    walk(claim)

    # The anchor's own field names are the highest-risk surface: they come
    # straight from a person-level public dataset.
    for entry in (claim["structured_records"]["anchor"] or {}).values():
        norm = re.sub(r"[^a-z0-9]+", "_", entry["field"].lower()).strip("_")
        assert norm not in banned, "anchor field %r is person-level" % entry["field"]


def test_zero_conflict_control_plants_nothing():
    gold = json.load(open(os.path.join(GOLD, "claim_000_zero_conflict.gold.json")))
    assert gold["is_zero_conflict_control"] is True
    assert gold["planted_differences"] == []


# --- Claim 001 E1 surface ---------------------------------------------------

def test_claim_001_exposes_exactly_two_extraction_passages():
    """E1's model surface is fixed and small: the FNOL claimant narrative and
    the recorded statement body. Nothing else."""
    from src.ingestion.passages import enumerate_passages
    claim = load_claim(os.path.join(FIXTURES, "claim_001", "claim.json"))
    assert [p.passage_id for p in enumerate_passages(claim)] == [
        "fnol.description_of_accident", "statement.body"]


def test_claim_001_makes_exactly_three_model_calls():
    from src.llm.client import RecordedClient
    from src.pipeline import run_pipeline
    claim = load_claim(os.path.join(FIXTURES, "claim_001", "claim.json"))
    client = RecordedClient.from_dir(
        os.path.join(ROOT, "src", "llm", "recordings", "claim_001"))
    run_pipeline(claim, client)
    assert [c["tag"] for c in client.calls] == [
        "extract__fnol.description_of_accident",
        "extract__statement.body",
        "differences",
    ]


def test_excluded_anchor_entries_are_recorded_and_absent():
    """Withheld entries are visible as a decision, not an unexplained gap in the
    id sequence."""
    claim = json.load(open(os.path.join(FIXTURES, "claim_001", "claim.json")))
    excluded = claim["provenance"]["anchor"]["excluded_entries"]
    assert {e["fact_id"] for e in excluded} == {"A006", "A007"}
    for e in excluded:
        assert e["reason"].strip(), "an exclusion without a reason is a silent drop"
        assert e["fact_id"] not in (claim["structured_records"]["anchor"] or {})


def test_excluded_anchor_fields_never_become_facts_or_reach_a_model():
    from src.llm.client import RecordedClient
    from src.pipeline import run_pipeline
    claim = load_claim(os.path.join(FIXTURES, "claim_001", "claim.json"))
    client = RecordedClient.from_dir(
        os.path.join(ROOT, "src", "llm", "recordings", "claim_001"))
    run = run_pipeline(claim, client)

    blob = json.dumps(run.result.to_dict())
    payload = "".join(c["system"] + c["user"] for c in client.calls)
    for token in ("HIT_AND_RUN", "PRIM_CONTRIBUTORY_CAUSE",
                  "FAILING TO REDUCE SPEED", "A006", "A007"):
        assert token not in blob, "%s reached the output" % token
        assert token not in payload, "%s reached a model" % token


def test_claim_001_computes_no_reporting_delay_and_says_so():
    """The file states no report date, so none is invented and the absence is an
    output rather than silence (D-020 P5)."""
    from src.pipeline import run_pipeline
    claim = load_claim(os.path.join(FIXTURES, "claim_001", "claim.json"))
    assert claim.claim_record["reported_date"] is None
    result = run_pipeline(claim).result

    subjects = {f.subject for f in result.facts}
    assert "reporting_delay_days" not in subjects
    assert "reported_date" not in subjects
    assert any("reporting delay" in n for n in result.not_assessed)
    assert any("doc_fnol" in n and "not recorded" in n for n in result.not_assessed)


def test_a_document_without_an_arrival_date_contributes_no_timeline_event():
    from src.pipeline import run_pipeline
    claim = load_claim(os.path.join(FIXTURES, "claim_001", "claim.json"))
    result = run_pipeline(claim).result
    became_known = [e for e in result.timeline if e.axis == "became_known"]
    assert len(became_known) == 1, "only the statement records its own arrival"
    assert became_known[0].when["Date"]["value"] == "2026-08-13"
