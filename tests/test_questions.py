"""The completeness checklist — deterministic, and the D-026 hedge."""
from src.claim_model import Document
from src.questions.checklist import build_open_questions


def test_absent_expected_document_becomes_a_question(smoke_claim):
    qs = build_open_questions(smoke_claim)
    kinds = {q.kind for q in qs}
    assert "expected_document_absent" in kinds
    assert any("adjuster notes" in q.question for q in qs)


def test_an_absent_document_question_carries_no_citations(smoke_claim):
    """The one place drop-if-uncitable cannot apply, and why OpenQuestion is
    not a Fact with a status (D-027)."""
    qs = [q for q in build_open_questions(smoke_claim)
          if q.kind == "expected_document_absent"]
    assert qs
    for q in qs:
        assert q.supporting_citations == []


def test_present_documents_are_not_questioned(smoke_claim):
    qs = build_open_questions(smoke_claim)
    text = " ".join(q.question for q in qs)
    assert "FNOL" not in text
    assert "recorded statement" not in text


def test_documents_not_yet_expected_are_not_questioned(smoke_claim):
    """A repair estimate is a C4 document. At C3 its absence is not a finding."""
    qs = build_open_questions(smoke_claim)
    assert not any("repair estimate" in q.question for q in qs)


def test_repair_estimate_is_questioned_at_c4(smoke_claim):
    smoke_claim.checkpoint = "C4"
    qs = build_open_questions(smoke_claim)
    assert any("repair estimate" in q.question for q in qs)


def test_independent_account_satisfies_the_police_report_slot(smoke_claim):
    qs = build_open_questions(smoke_claim)
    assert not any("independent account" in q.question for q in qs)


def test_unanswered_request_becomes_a_cited_question(smoke_claim):
    smoke_claim.documents.append(Document(
        document_id="doc_corr", type="correspondence", version="v1",
        received_date="2026-03-01", checkpoint_available="C3",
        structure_class="unstructured",
        structured_fields={"requests": [
            {"item_type": "police_report", "item_label": "The police report",
             "requested_on": "2026-02-26"}]}))
    qs = build_open_questions(smoke_claim)
    assert any(q.kind == "requested_never_received" for q in qs)


def test_a_request_that_arrived_is_not_questioned(smoke_claim):
    smoke_claim.documents.append(Document(
        document_id="doc_corr", type="correspondence", version="v1",
        received_date="2026-03-01", checkpoint_available="C3",
        structure_class="unstructured",
        structured_fields={"requests": [
            {"item_type": "recorded_statement", "item_label": "The recorded statement",
             "requested_on": "2026-02-22"}]}))
    qs = build_open_questions(smoke_claim)
    assert not any(q.kind == "requested_never_received" for q in qs)
