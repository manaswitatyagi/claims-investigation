"""structure_class routes the pipeline, and the router raises rather than warns."""
import json
import os
import shutil

import pytest

from src.claim_model import Document, Passage
from src.ingestion.loader import (CHECKPOINT_ORDER, FixtureIncompleteError,
                                  documents_available_at, load_claim)
from src.ingestion.passages import (StructureClassViolation, assert_llm_readable,
                                    enumerate_passages)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_only_narrative_passages_reach_the_extractor(smoke_claim):
    passages = enumerate_passages(smoke_claim)
    assert {p.passage_id for p in passages} == {
        "fnol.description_of_accident", "statement.body", "independent.body"}


def test_fnol_structured_fields_do_not_become_passages(smoke_claim):
    fnol = smoke_claim.document("doc_fnol")
    assert len(fnol.structured_fields) > 5, "the FNOL carries many structured fields"
    passages = [p for p in enumerate_passages(smoke_claim) if p.document_id == "doc_fnol"]
    assert len(passages) == 1, "only the narrative box is exposed to a model"


def test_a_structured_document_carrying_passages_raises(smoke_claim):
    smoke_claim.documents.append(Document(
        document_id="doc_estimate", type="repair_estimate", version="v1",
        received_date="2026-03-01", checkpoint_available="C3",
        structure_class="structured",
        passages=[Passage("est.body", "doc_estimate", "v1", "lines", "text")]))
    with pytest.raises(StructureClassViolation, match="read by code"):
        enumerate_passages(smoke_claim)


def test_assert_llm_readable_refuses_structured_documents():
    doc = Document(document_id="d", type="repair_estimate", version="v1",
                   received_date="2026-01-01", checkpoint_available="C3",
                   structure_class="structured")
    with pytest.raises(StructureClassViolation, match="refusing to send"):
        assert_llm_readable(doc)


def test_documents_after_the_checkpoint_are_withheld(smoke_claim):
    smoke_claim.documents.append(Document(
        document_id="doc_future", type="repair_estimate", version="v1",
        received_date="2026-05-01", checkpoint_available="C5",
        structure_class="structured"))
    available = documents_available_at(smoke_claim)
    assert "doc_future" not in {d.document_id for d in available}, \
        "evaluating against documents that would not yet exist is target leakage"


def test_checkpoint_ordering_is_monotonic():
    assert [CHECKPOINT_ORDER[c] for c in ("C1", "C2", "C3", "C4", "C5")] == [1, 2, 3, 4, 5]


def test_todo_skeleton_refuses_to_load(tmp_path):
    """A placeholder must never be silently evaluated and reported as a result.

    Written against the mechanism rather than a named fixture, so it keeps
    working once every fixture is complete.
    """
    src = os.path.join(ROOT, "data", "fixtures", "claim_000_smoke")
    dst = tmp_path / "fixture"
    shutil.copytree(src, str(dst))
    path = dst / "claim.json"
    raw = json.loads(path.read_text())
    raw["claim_record"]["claim_number"] = "__TODO__"
    path.write_text(json.dumps(raw))
    with pytest.raises(FixtureIncompleteError, match="skeleton"):
        load_claim(str(path))


def test_a_complete_fixture_loads():
    load_claim(os.path.join(ROOT, "data", "fixtures", "claim_001", "claim.json"))


def test_speaker_turns_locate_the_speaker_for_an_offset(smoke_claim):
    p = smoke_claim.passage("statement.body")
    # 488 is inside the claimant's "No, I was still moving" turn.
    assert p.speaker_at(488)["speaker_kind"] == "claimant"
    # 383 is inside the adjuster's leading question.
    assert p.speaker_at(383)["speaker_kind"] == "adjuster"
