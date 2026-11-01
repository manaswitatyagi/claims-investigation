"""Stage 4 — EXTRACT. LLM call 1, once per passage.

The only place a model reads source text. Output is `(assertion, asserter,
span)` triples; nothing without a locatable span survives stage 5.
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.claim_model import Asserter, Citation, Claim, Fact, Passage, text_span
from src.ingestion.passages import assert_llm_readable
from src.llm.client import LLMClient
from src.llm.prompts import (EXTRACT_SCHEMA, EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE)
from src.normalization.dates import normalise_date

VALID_ASSERTER_KINDS = {"claimant", "insured", "witness", "police_officer",
                        "adjuster", "provider", "system_record", "attorney"}


def extract_from_passages(claim: Claim, passages: List[Passage],
                          llm: LLMClient) -> List[Fact]:
    facts: List[Fact] = []
    counter = 0
    for passage in passages:
        doc = claim.document(passage.document_id)
        if doc is not None:
            assert_llm_readable(doc)
        payload = llm.complete_json(
            system=EXTRACT_SYSTEM,
            user=EXTRACT_USER_TEMPLATE.format(
                passage_id=passage.passage_id,
                document_type=doc.type if doc else "unknown",
                document_id=passage.document_id,
                label=passage.label,
                speaker_note=_speaker_note(passage),
                text=passage.text,
            ),
            schema=EXTRACT_SCHEMA,
            tag="extract__%s" % passage.passage_id,
        )
        for item in payload.get("facts", []) or []:
            counter += 1
            fact = _to_fact(item, passage, "ex_%03d" % counter)
            if fact is not None:
                facts.append(fact)
    return facts


def _speaker_note(passage: Passage) -> str:
    if not passage.speaker_turns:
        return ""
    speakers = []
    for t in passage.speaker_turns:
        label = "%s (%s)" % (t["speaker"], t.get("speaker_kind") or "unknown")
        if label not in speakers:
            speakers.append(label)
    return ("\nSPEAKERS IN THIS TRANSCRIPT: %s\nAttribute each fact to the speaker "
            "whose turn contains the span.\n" % "; ".join(speakers))


def _to_fact(item: Dict[str, Any], passage: Passage, fact_id: str):
    """Build a Fact from one model item.

    Malformed items are dropped here rather than allowed to fail validation
    later, so a single bad row cannot take down a run.
    """
    kind = item.get("asserter_kind")
    if kind not in VALID_ASSERTER_KINDS:
        return None
    try:
        start = int(item["char_start"])
        end = int(item["char_end"])
    except (KeyError, TypeError, ValueError):
        return None
    if not item.get("assertion") or not item.get("quoted_text"):
        return None

    normalised = None
    raw_time = item.get("raw_time_expression")
    if raw_time:
        # normalise_date returns precision "vague" for anything unanchored, so a
        # model that ignores rule 4 and hands back "that evening" still cannot
        # produce a timestamp here.
        normalised = normalise_date(raw_time)

    return Fact(
        fact_id=fact_id,
        assertion=item["assertion"],
        asserter=Asserter(kind=kind, name=item.get("asserter_name")),
        provenance="extracted",
        subject=item.get("subject"),
        normalised_value=normalised,
        citations=[Citation(
            document_id=passage.document_id,
            document_version=passage.document_version,
            locator=text_span(passage.passage_id, start, end),
            quoted_text=item["quoted_text"],
        )],
    )
