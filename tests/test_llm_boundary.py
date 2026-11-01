"""D-020 P4, checked rather than intended.

The generation stage must never see a raw document. This file asserts it against
the actual outbound payload, so the invariant survives refactoring.
"""
import pytest

from src.claim_model import Asserter, Citation, Fact, field_locator
from src.differences.llm_propose import propose_differences, render_facts
from src.extraction.llm_extract import extract_from_passages
from src.ingestion.passages import enumerate_passages
from src.llm.client import NullClient


def _fact(fid, subject, assertion, quoted):
    return Fact(fact_id=fid, assertion=assertion, asserter=Asserter(kind="claimant", name="D W"),
                provenance="extracted", subject=subject,
                citations=[Citation("doc", "v1", field_locator("r", "f"), quoted)])


def _assert_payload_is_exactly_the_rendered_facts(client, facts):
    """The real invariant, tested exactly.

    An earlier version of this test asserted that no 40-character verbatim run
    from a passage appears in the payload. That was wrong, and instructively so:
    a *faithful* assertion reuses its source's wording, because clauses like
    "because they were concerned about being stranded late at night" have no
    shorter faithful paraphrase. Sharing words with the source is what a correct
    extraction does; it is not a leak.

    What D-020 P4 actually requires is that the difference stage sees the
    extracted-and-cited fact set AND NOTHING ELSE. That is an equality, so it is
    tested as one.
    """
    from src.llm.prompts import DIFFERENCE_USER_TEMPLATE

    diff_calls = [c for c in client.calls if c["tag"] == "differences"]
    assert diff_calls, "the difference stage must have been exercised"
    expected = DIFFERENCE_USER_TEMPLATE.format(facts_block=render_facts(facts))
    assert diff_calls[0]["user"] == expected, (
        "the difference payload carries content beyond the rendered fact set")


def _assert_no_wholesale_passage_paste(client, passages):
    """Independent coarse guard.

    The equality check above is computed from `render_facts`, so it would still
    pass if `render_facts` itself started emitting source text. This catches
    that: 150 characters is far longer than any clause an assertion would
    legitimately reuse, and far shorter than the smallest passage in any fixture.
    """
    payload = "".join(c["system"] + c["user"] for c in client.calls
                      if c["tag"] == "differences")
    for passage in passages:
        for chunk in _chunks(passage.text, 150):
            assert chunk not in payload, (
                "passage %s was pasted into the difference payload"
                % passage.passage_id)


def test_difference_payload_contains_no_passage_text(smoke_claim, recorded_client):
    """The core structural defence: the model cannot fabricate from a source it
    cannot see."""
    client = recorded_client("claim_000_smoke")
    passages = enumerate_passages(smoke_claim)
    facts = extract_from_passages(smoke_claim, passages, client)
    propose_differences(facts, client)
    _assert_payload_is_exactly_the_rendered_facts(client, facts)
    _assert_no_wholesale_passage_paste(client, passages)


def test_rendered_facts_exclude_quoted_source_text():
    facts = [_fact("f1", "s", "The vehicle was parked.", "my car was parked at the kerb")]
    rendered = render_facts(facts)
    assert "The vehicle was parked." in rendered
    assert "my car was parked at the kerb" not in rendered, \
        "quoted_text is source text and must not cross the boundary"


def test_rendered_facts_carry_asserter_and_subject():
    facts = [_fact("f1", "vehicle_state", "The vehicle was parked.", "q")]
    rendered = render_facts(facts)
    assert "f1" in rendered and "vehicle_state" in rendered and "claimant" in rendered


def test_no_facts_means_no_difference_call():
    client = NullClient()
    assert propose_differences([], client) == []


def test_positions_citing_unknown_facts_are_discarded():
    class Ghost(NullClient):
        def complete_json(self, system, user, schema, tag=""):
            return {"differences": [{"subject": "x", "positions": [
                {"fact_id": "f1", "stance": "a"},
                {"fact_id": "does_not_exist", "stance": "b"}]}]}

    facts = [_fact("f1", "s", "A", "q")]
    assert propose_differences(facts, Ghost()) == [], \
        "a difference with one resolvable position is not a difference"


def test_null_client_runs_the_deterministic_path_alone(smoke_claim):
    passages = enumerate_passages(smoke_claim)
    assert extract_from_passages(smoke_claim, passages, NullClient()) == []


def _chunks(text, size):
    for i in range(0, max(1, len(text) - size), size):
        chunk = text[i:i + size].strip()
        if len(chunk) >= size - 5:
            yield chunk


# --- Claim 001 specific surfaces -------------------------------------------

def test_claim_001_passages_do_not_leak_into_the_difference_payload(
        claim_001, recorded_client):
    client = recorded_client("claim_001")
    passages = enumerate_passages(claim_001)
    facts = extract_from_passages(claim_001, passages, client)
    propose_differences(facts, client)
    _assert_payload_is_exactly_the_rendered_facts(client, facts)
    _assert_no_wholesale_passage_paste(client, passages)


def test_the_structured_anchor_never_reaches_any_model(claim_001, recorded_client):
    """The anchor is structured source data. It is read by code and cited by
    Field locator; no stage sends it to a model."""
    client = recorded_client("claim_001")
    passages = enumerate_passages(claim_001)
    facts = extract_from_passages(claim_001, passages, client)
    propose_differences(facts, client)

    everything = "".join(c["system"] + c["user"] for c in client.calls)
    anchor = claim_001.structured_records["anchor"]
    assert anchor, "the fixture carries an anchor"
    for entry_id, entry in anchor.items():
        assert entry_id not in everything, "anchor id %s leaked" % entry_id
        assert entry["field"] not in everything, "anchor field %s leaked" % entry["field"]


def test_anchor_facts_are_deterministic_and_cited_to_their_source_entry(claim_001):
    from src.extraction.structured import read_anchor_facts
    facts = read_anchor_facts(claim_001)
    assert len(facts) == len(claim_001.structured_records["anchor"])
    for f in facts:
        assert f.provenance == "deterministic"
        assert f.asserter.kind == "system_record"
        loc = f.citations[0].locator
        assert "Field" in loc and loc["Field"]["record"] == "anchor_record"
        assert loc["Field"]["field_path"].endswith(".value")


def test_anchor_facts_are_attributed_not_asserted_as_truth(claim_001):
    """The system says the record CODES a value. It never says the value is so."""
    from src.extraction.structured import read_anchor_facts
    for f in read_anchor_facts(claim_001):
        assert f.assertion.startswith("The structured crash record codes ")


# --- prompt contracts -------------------------------------------------------
# These pin behaviour that is easy to erode in an edit and expensive to notice.

def test_extraction_prompt_forbids_strengthening_and_preserves_hedging():
    from src.llm.prompts import EXTRACT_SYSTEM
    lowered = EXTRACT_SYSTEM.lower()
    for required in ("never strengthen a claim", "a belief is not a fact",
                     "preserve approximation and uncertainty",
                     "do not normalise vague time expressions"):
        assert required in lowered, "extraction prompt lost: %s" % required


def test_extraction_prompt_forbids_judgement():
    from src.llm.prompts import EXTRACT_SYSTEM
    lowered = EXTRACT_SYSTEM.lower()
    for required in ("credibility", "fault", "liability", "materiality"):
        assert required in lowered


def test_difference_prompt_treats_silence_as_no_position():
    from src.llm.prompts import DIFFERENCE_SYSTEM
    lowered = DIFFERENCE_SYSTEM.lower()
    for required in ("silence is not a position", "missing corroboration",
                     "compatible approximations are not differences"):
        assert required in lowered, "difference prompt lost: %s" % required


def test_difference_prompt_refuses_to_adjudicate():
    from src.llm.prompts import DIFFERENCE_SYSTEM
    lowered = DIFFERENCE_SYSTEM.lower()
    for required in ("do not decide which source is correct",
                     "do not assess materiality",
                     "return an empty list"):
        assert required in lowered


def test_difference_prompt_never_asks_for_a_materiality_field():
    from src.llm.prompts import DIFFERENCE_SCHEMA
    props = DIFFERENCE_SCHEMA["properties"]["differences"]["items"]["properties"]
    assert set(props) == {"subject", "positions"}, \
        "the difference response schema must have no field materiality could occupy"
