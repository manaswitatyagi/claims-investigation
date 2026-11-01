"""Live ingestion: grounding, normalisation, incremental recompute, events.

No network. A stub client returns canned extraction payloads, so the tests
exercise the real locator, the real ontology, and the real classifier.
"""
import json
import os

import pytest

from src.llm.client import LLMClient
from src.runtime import events as ev
from src.runtime import ingest
from src.runtime.claim_state import ClaimState

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIM = "claim_001"

DOC = ("The witness says the vehicle was heading southbound before it began to turn.\n\n"
       "The witness recalls that the road was wet at the time.\n\n"
       "The witness says the vehicle was turning right when the contact happened.\n")


class StubClient(LLMClient):
    """Canned extraction; relationship classification falls to the real
    deterministic path or a fixed verdict."""
    model_id, prompt_version = "stub", "test"

    def __init__(self, facts, relationship="CONTRADICTORY"):
        self._facts, self._rel = facts, relationship
        self.calls = []

    def complete_json(self, system, user, schema, tag=""):
        self.calls.append(tag)
        if tag.startswith("neighborhood__"):
            return {"relationship": self._rel, "rationale": "stub"}
        return {"facts": self._facts}


def fact(assertion, quote, entity="vehicle_1", predicate="travel_direction",
         value="south", kind="witness"):
    return {"assertion": assertion, "asserter_kind": kind, "asserter_name": None,
            "subject": predicate, "subject_entity_id": entity,
            "predicate": predicate, "value_raw": value, "quoted_text": quote,
            "raw_time_expression": None, "revised": None, "superseded_text": None}


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr("src.runtime.claim_state.RUNTIME_DIR", str(tmp_path))
    return ClaimState.reset(CLAIM)


def store(text=DOC, name="witness.md"):
    return ingest.store_document(CLAIM, name, text.encode("utf-8"))


# --- upload ---------------------------------------------------------------

def test_only_md_and_txt_are_accepted(fresh):
    for bad in ("scan.pdf", "photo.png", "records.docx"):
        with pytest.raises(ingest.UnsupportedDocument, match="only .md and .txt"):
            ingest.store_document(CLAIM, bad, b"x")
    assert ingest.store_document(CLAIM, "a.txt", b"hello")["document_id"]


def test_empty_and_binary_files_are_rejected(fresh):
    with pytest.raises(ingest.UnsupportedDocument, match="empty"):
        ingest.store_document(CLAIM, "a.md", b"   ")
    with pytest.raises(ingest.UnsupportedDocument, match="UTF-8"):
        ingest.store_document(CLAIM, "a.md", b"\xff\xfe\x00binary")


def test_uploaded_document_becomes_a_source(fresh):
    stored = store()
    client = StubClient([fact("The vehicle was heading southbound.",
                              "the vehicle was heading southbound")])
    ingest.process_document(CLAIM, stored, client, "s1")
    state = ClaimState.load(CLAIM)
    src = [s for s in state.view["sources"] if s["source_id"] == stored["document_id"]]
    assert len(src) == 1
    assert src[0]["name"] == "witness.md"
    assert src[0]["verification_status"] == "processed"
    assert src[0]["verified_assertion_count"] == 1


# --- grounding is not relaxed for the demo --------------------------------

def test_resolvable_evidence_enters_claim_state(fresh):
    stored = store()
    ingest.process_document(CLAIM, stored, StubClient([
        fact("The vehicle was heading southbound.", "the vehicle was heading southbound")]), "s1")
    state = ClaimState.load(CLAIM)
    added = [a for a in state.view["assertions"].values()
             if a["source_id"] == stored["document_id"]]
    assert len(added) == 1
    ev_ = added[0]["evidence"]
    assert ev_["verified"] is True
    assert ev_["passage_text"][ev_["char_start"]:ev_["char_end"]] == ev_["quote"]


def test_unresolvable_quote_never_enters_claim_state(fresh):
    stored = store()
    summary = ingest.process_document(CLAIM, stored, StubClient([
        fact("Invented.", "a sentence that is nowhere in this document")]), "s1")
    assert summary["dropped"] == 1 and summary["verified"] == 0
    state = ClaimState.load(CLAIM)
    assert not [a for a in state.view["assertions"].values()
                if a["source_id"] == stored["document_id"]]
    src = [s for s in state.view["sources"] if s["source_id"] == stored["document_id"]][0]
    assert src["verification_status"] == "processed_with_dropped_assertions"
    assert src["dropped_assertion_count"] == 1


def test_ambiguous_quote_is_dropped(fresh):
    text = "The car was red. The car was red.\n"
    stored = store(text, "dup.md")
    summary = ingest.process_document(CLAIM, stored, StubClient([
        fact("The car was red.", "The car was red")]), "s1")
    assert summary["dropped"] == 1


# --- ontology -------------------------------------------------------------

def test_known_values_normalise(fresh):
    stored = store()
    ingest.process_document(CLAIM, stored, StubClient([
        fact("Heading southbound.", "the vehicle was heading southbound",
             value="southbound")]), "s1")
    a = [x for x in ClaimState.load(CLAIM).view["assertions"].values()
         if x["source_id"] == stored["document_id"]][0]
    assert a["value_normalised"] == "south"


def test_unmappable_concept_is_kept_but_left_unresolved(fresh):
    """No fake ontology mapping to make the demo look complete."""
    stored = store()
    summary = ingest.process_document(CLAIM, stored, StubClient([
        dict(fact("Something with no predicate.", "the road was wet at the time"),
             predicate=None, subject_entity_id=None)]), "s1")
    assert summary["verified"] == 1 and summary["unresolved"] == 1
    state = ClaimState.load(CLAIM)
    added = [a for a in state.view["assertions"].values()
             if a["source_id"] == stored["document_id"]][0]
    assert added["evidence"]["verified"] is True
    assert added["predicate"] is None
    assert any(u["assertion_id"] == added["assertion_id"] for u in state.view["ungrouped"])


# --- incremental recompute + relationship events --------------------------

def _events(session):
    return [e for e in ev.bus_for(CLAIM).recent(400) if e["session_id"] == session]


def test_affected_neighborhood_recomputes_and_others_do_not(fresh):
    before = ClaimState.load(CLAIM)
    untouched = before.neighborhood_key("vehicle_2", "crash_001", "unit_type")
    stored = store()
    ingest.process_document(CLAIM, stored, StubClient([
        fact("Heading southbound.", "the vehicle was heading southbound")]), "s2")
    after = ClaimState.load(CLAIM)
    nb = after.neighborhood_key("vehicle_1", "crash_001", "travel_direction")
    assert len(nb["assertion_ids"]) == 4, "the new position joined the neighbourhood"
    assert after.neighborhood_key("vehicle_2", "crash_001", "unit_type") == untouched


def test_relationship_change_emits_an_event(fresh):
    """approximate_speed is single-source at baseline; a second, non-overlapping
    value makes it a relationship state change."""
    stored = store("The witness says the vehicle was doing about forty.\n", "spd.md")
    ingest.process_document(CLAIM, stored, StubClient(
        [fact("About forty mph.", "the vehicle was doing about forty",
              predicate="approximate_speed", value="40")],
        relationship="CONTRADICTORY"), "s3")
    changes = [e for e in _events("s3") if e["type"] == ev.RELATIONSHIP_CHANGED]
    assert len(changes) == 1
    p = changes[0]["payload"]
    assert p["predicate"] == "approximate_speed"
    assert p["from"] is None and p["to"] == "CONTRADICTORY"
    assert "does not mean any source is right or wrong" in p["note"]


def test_pure_corroboration_emits_no_relationship_change(fresh):
    """Adding a third agreeing source must not be reported as a change."""
    stored = store("The witness recalls the road was wet at the time.\n", "wet.md")
    ingest.process_document(CLAIM, stored, StubClient([
        fact("The road was wet.", "the road was wet at the time",
             entity="roadway_1", predicate="road_surface", value="wet")]), "s4")
    session = _events("s4")
    assert [e for e in session if e["type"] == ev.NEIGHBORHOOD_UPDATED]
    assert not [e for e in session if e["type"] == ev.RELATIONSHIP_CHANGED]
    nb = ClaimState.load(CLAIM).neighborhood_key("roadway_1", "crash_001", "road_surface")
    assert nb["relationship"] == "CORROBORATING" and len(nb["assertion_ids"]) == 4


def test_event_stream_never_leaks_reasoning_or_judgement(fresh):
    stored = store()
    ingest.process_document(CLAIM, stored, StubClient([
        fact("Heading southbound.", "the vehicle was heading southbound")]), "s5")
    blob = json.dumps(_events("s5")).lower()
    for banned in ("reasoning", "chain_of_thought", "raw_response",
                   "materiality", "credibility", "fraud", "liability"):
        assert banned not in blob


def test_failure_is_surfaced_not_swallowed(fresh):
    class Boom(LLMClient):
        model_id, prompt_version = "boom", "test"
        def complete_json(self, system, user, schema, tag=""):
            raise RuntimeError("extraction exploded")

    stored = store()
    with pytest.raises(RuntimeError):
        ingest.process_document(CLAIM, stored, Boom(), "s6")
    failed = [e for e in _events("s6") if e["type"] == ev.PROCESSING_FAILED]
    assert failed and "extraction exploded" in failed[0]["payload"]["error"]
    src = [s for s in ClaimState.load(CLAIM).view["sources"]
           if s["source_id"] == stored["document_id"]][0]
    assert src["verification_status"] == "failed"


# --- the DTO boundary holds after ingestion -------------------------------

def test_view_still_ships_backend_computed_relationships(fresh):
    stored = store()
    ingest.process_document(CLAIM, stored, StubClient([
        fact("Heading southbound.", "the vehicle was heading southbound")]), "s7")
    view = ClaimState.load(CLAIM).view
    for n in view["neighborhoods"]:
        if not n["singleton"]:
            assert n["relationship"] in ("CORROBORATING", "COMPATIBLE", "CONTRADICTORY")
            assert n["rationale"]


def test_source_filtering_still_resolves_after_ingestion(fresh):
    stored = store()
    ingest.process_document(CLAIM, stored, StubClient([
        fact("Heading southbound.", "the vehicle was heading southbound")]), "s8")
    view = ClaimState.load(CLAIM).view
    for n in view["neighborhoods"]:
        for aid in n["assertion_ids"]:
            assert aid in view["assertions"], "%s dangles after ingestion" % aid
        derived = {view["assertions"][a]["source_id"] for a in n["assertion_ids"]}
        assert set(n["source_ids"]) == derived


def test_react_never_derives_a_relationship():
    """Relationship meaning stays in the domain layer.

    React may READ `relationship` and branch on it for display — opening
    contradictions by default is a presentation choice. What it must never do is
    DERIVE one, which means comparing assertion values to each other.
    """
    web = os.path.join(ROOT, "web", "src")
    derivation = ("computeRelationship", "inferRelationship", "detectContradiction",
                  "classifyRelationship", ".value ===", ".value !==",
                  "value_normalised ===", "value_normalised !==",
                  "distinct_values.length >", "new Set(values)")
    checked = 0
    for base, _dirs, files in os.walk(web):
        for f in files:
            if not f.endswith((".ts", ".tsx")):
                continue
            src = open(os.path.join(base, f), encoding="utf-8").read()
            checked += 1
            for pattern in derivation:
                assert pattern not in src, (
                    "%r in %s looks like the frontend deciding a relationship" % (pattern, f))
    assert checked >= 8


def test_relationship_only_reaches_react_through_the_dto():
    """The DTO is the only carrier of relationship state."""
    types = open(os.path.join(ROOT, "web", "src", "types.ts"), encoding="utf-8").read()
    assert "relationship: Relationship;" in types
    assert "relationship_method" in types
