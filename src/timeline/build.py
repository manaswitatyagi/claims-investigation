"""Stage 7 — BUILD TIMELINE.

Two axes, both required in the output. Ordering is arithmetic over normalised
dates; no model sorts this. PRD §10.4 lists "sort the timeline" among the
things an LLM must never do, and DOCMAP §4 calls a model touching it a
regression.

The `became_known` axis is the one a successor actually needs: a chronology of
the loss alone does not tell them when the file learned each thing.
"""
from __future__ import annotations

from typing import List, Optional

from src.claim_model import Fact, TimelineEvent
from src.normalization.dates import ordering_confidence, sort_key

#: Subjects that describe when the FILE learned something, rather than when
#: something happened in the world.
BECAME_KNOWN_SUBJECTS = {"reported_date"}
BECAME_KNOWN_PREFIXES = ("document_received:", "reserve_change:")


def axis_for(fact: Fact) -> str:
    subject = fact.subject or ""
    if subject in BECAME_KNOWN_SUBJECTS:
        return "became_known"
    if subject.startswith(BECAME_KNOWN_PREFIXES):
        return "became_known"
    return "occurred"


def build_timeline(facts: List[Fact]) -> List[TimelineEvent]:
    """Derive events from every Fact carrying a Date normalised value."""
    dated = [f for f in facts if f.normalised_value and "Date" in f.normalised_value]

    events: List[TimelineEvent] = []
    for i, fact in enumerate(dated, start=1):
        events.append(TimelineEvent(
            event_id="ev_%03d" % i,
            axis=axis_for(fact),
            when=fact.normalised_value,
            label=fact.assertion,
            source_fact_ids=[fact.fact_id],
            ordering_confidence=ordering_confidence(fact.normalised_value),
        ))

    ordered: List[TimelineEvent] = []
    for axis in ("occurred", "became_known"):
        in_axis = [e for e in events if e.axis == axis]
        orderable = [e for e in in_axis if sort_key(e.when) is not None]
        unorderable = [e for e in in_axis if sort_key(e.when) is None]
        orderable.sort(key=lambda e: (sort_key(e.when), e.label))
        # Unorderable events still appear. They are not silently dropped and
        # they are not given a false position — they are appended, flagged.
        ordered.extend(orderable + unorderable)
    return ordered


def first_date(facts: List[Fact], subject: str) -> Optional[str]:
    for f in facts:
        if f.subject == subject and f.normalised_value and "Date" in f.normalised_value:
            return f.normalised_value["Date"].get("value")
    return None
