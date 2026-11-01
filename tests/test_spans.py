"""The gate. Drop, never soften."""
from src.claim_model import Asserter, Citation, Fact, field_locator, text_span
from src.extraction.spans import build_record_index, resolve_and_drop, resolve_citation


def _fact(claim, passage_id, start, end, quoted, fid="f1"):
    return Fact(fact_id=fid, assertion="x", asserter=Asserter(kind="claimant"),
                provenance="extracted", citations=[Citation(
                    document_id="doc_statement", document_version="v1",
                    locator=text_span(passage_id, start, end), quoted_text=quoted)])


def test_exact_span_resolves(smoke_claim):
    p = smoke_claim.passage("statement.body")
    quoted = p.text[488:510]
    kept, dropped = resolve_and_drop([_fact(smoke_claim, "statement.body", 488, 510, quoted)],
                                     smoke_claim)
    assert len(kept) == 1 and not dropped
    assert kept[0].citations[0].resolved is True


def test_offset_drift_is_dropped_and_diagnosed(smoke_claim):
    p = smoke_claim.passage("statement.body")
    quoted = p.text[488:510]
    kept, dropped = resolve_and_drop(
        [_fact(smoke_claim, "statement.body", 495, 517, quoted)], smoke_claim)
    assert kept == []
    assert dropped[0]["notes"] == ["offset_drift"]


def test_fabricated_text_is_dropped_and_diagnosed_differently(smoke_claim):
    kept, dropped = resolve_and_drop(
        [_fact(smoke_claim, "statement.body", 10, 40, "a sentence nobody wrote")], smoke_claim)
    assert kept == []
    assert dropped[0]["notes"] == ["text_absent_from_passage"], \
        "a model that invents is a different failure from one that miscounts"


def test_missing_passage_is_dropped(smoke_claim):
    kept, dropped = resolve_and_drop(
        [_fact(smoke_claim, "no.such.passage", 0, 5, "hello")], smoke_claim)
    assert kept == [] and dropped[0]["notes"] == ["passage_not_found"]


def test_out_of_range_offsets_are_dropped(smoke_claim):
    kept, dropped = resolve_and_drop(
        [_fact(smoke_claim, "statement.body", 0, 999999, "x")], smoke_claim)
    assert kept == [] and dropped[0]["notes"] == ["offsets_out_of_range"]


def test_fact_with_no_citations_is_dropped(smoke_claim):
    f = Fact(fact_id="f9", assertion="x", asserter=Asserter(kind="claimant"),
             provenance="extracted", citations=[])
    kept, dropped = resolve_and_drop([f], smoke_claim)
    assert kept == [] and dropped[0]["reason"] == "no_citations"


def test_all_citations_must_resolve_for_a_derived_fact(smoke_claim):
    good = Citation("rec_claim", "v1", field_locator("claim_record", "loss_date"), "2026-02-14")
    bad = Citation("rec_claim", "v1", field_locator("claim_record", "loss_date"), "1999-01-01")
    f = Fact(fact_id="f2", assertion="delay", asserter=Asserter(kind="system_record"),
             provenance="deterministic", citations=[good, bad])
    kept, dropped = resolve_and_drop([f], smoke_claim)
    assert kept == [], "a derived fact is only checkable if BOTH operands are"


def test_field_locator_resolves_against_structured_records(smoke_claim):
    idx = build_record_index(smoke_claim)
    c = Citation("rec_policy", "v1", field_locator("policy_record", "inception_date"), "2026-01-04")
    assert resolve_citation(c, smoke_claim, idx).resolved is True


def test_field_locator_value_mismatch_is_caught(smoke_claim):
    idx = build_record_index(smoke_claim)
    c = Citation("rec_policy", "v1", field_locator("policy_record", "inception_date"), "2020-01-01")
    c = resolve_citation(c, smoke_claim, idx)
    assert c.resolved is False and c.resolution_note == "field_value_mismatch"
