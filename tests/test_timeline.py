"""Two axes, ordered in code, with vague events placed but not positioned."""
from src.claim_model import Asserter, Citation, Fact, field_locator
from src.normalization.dates import normalise_date
from src.timeline.build import axis_for, build_timeline


def _dated(fid, subject, raw):
    return Fact(fact_id=fid, assertion=subject, asserter=Asserter(kind="system_record"),
                provenance="deterministic", subject=subject,
                normalised_value=normalise_date(raw),
                citations=[Citation("d", "v1", field_locator("r", "f"), raw)])


def test_both_axes_are_produced():
    facts = [_dated("a", "loss_date", "2026-02-14"),
             _dated("b", "reported_date", "2026-02-20"),
             _dated("c", "document_received:doc_fnol", "2026-02-21")]
    axes = {e.axis for e in build_timeline(facts)}
    assert axes == {"occurred", "became_known"}


def test_became_known_covers_documents_and_reserve_changes():
    assert axis_for(_dated("x", "document_received:doc_fnol", "2026-02-21")) == "became_known"
    assert axis_for(_dated("x", "reserve_change:0", "2026-02-21")) == "became_known"
    assert axis_for(_dated("x", "reported_date", "2026-02-20")) == "became_known"
    assert axis_for(_dated("x", "loss_date", "2026-02-14")) == "occurred"


def test_events_are_sorted_within_each_axis():
    facts = [_dated("a", "document_received:z", "2026-03-11"),
             _dated("b", "document_received:y", "2026-02-21"),
             _dated("c", "reported_date", "2026-02-20")]
    order = [e.when["Date"]["value"] for e in build_timeline(facts)]
    assert order == sorted(order)


def test_vague_events_appear_but_are_marked_unorderable():
    facts = [_dated("a", "loss_date", "2026-02-14"),
             _dated("b", "time_of_loss", "that evening")]
    events = build_timeline(facts)
    assert len(events) == 2, "a vague event is carried, not silently dropped"
    vague = [e for e in events if e.source_fact_ids == ["b"]][0]
    assert vague.ordering_confidence == "unorderable"
    assert vague.when["Date"]["value"] is None


def test_unorderable_events_are_placed_after_ordered_ones():
    facts = [_dated("a", "time_of_loss", "that evening"),
             _dated("b", "loss_date", "2026-02-14")]
    events = [e for e in build_timeline(facts) if e.axis == "occurred"]
    assert events[-1].ordering_confidence == "unorderable"


def test_facts_without_dates_produce_no_events():
    f = Fact(fact_id="n", assertion="no date", asserter=Asserter(kind="system_record"),
             provenance="deterministic", subject="x",
             citations=[Citation("d", "v1", field_locator("r", "f"), "v")])
    assert build_timeline([f]) == []


def test_every_event_traces_to_a_source_fact():
    facts = [_dated("a", "loss_date", "2026-02-14")]
    for e in build_timeline(facts):
        assert e.source_fact_ids
