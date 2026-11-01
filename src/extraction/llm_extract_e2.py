"""E2 extraction — E1b's verified-quote contract plus ontology tagging.

The quote/locate path is unchanged from E1b and is imported, not reimplemented:
the model gives a verbatim quote, `quote_locator` computes the offsets, and
`Citation.quoted_text` is the passage's own text. What is added is that the model
also selects an entity from a closed roster and a predicate from a closed
vocabulary, and reports the value as the source expresses it. The VALUE is then
normalised deterministically by lookup table — never by the model.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.claim_model import Asserter, Citation, Claim, Fact, Passage, text_span
from src.extraction.llm_extract import VALID_ASSERTER_KINDS, _speaker_note
from src.extraction.quote_locator import RESOLVED, locate
from src.llm.client import LLMClient
from src.llm.prompts_e2 import (EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE, extract_schema)
from src.normalization.dates import normalise_date
from src.ontology.claim_mapping import EVENT_ID, build_roster
from src.ontology.vocabulary import PREDICATES, is_event_scoped, normalise_value


def extract_from_passages(claim: Claim, passages: List[Passage],
                          llm: LLMClient) -> Tuple[List[Fact], List[Dict[str, Any]]]:
    from src.ingestion.passages import assert_llm_readable

    roster = build_roster(claim)
    entity_ids = [e["entity_id"] for e in roster]
    predicate_names = sorted(PREDICATES)
    schema = extract_schema(entity_ids, predicate_names)

    roster_block = "\n".join("  %-12s (%s) — %s" % (e["entity_id"], e["type"],
                                                    e["description"]) for e in roster)
    predicate_block = "\n".join(
        "  %-24s subject=%-10s %s" % (p, PREDICATES[p]["subject_type"],
                                      PREDICATES[p].get("note", ""))
        for p in predicate_names)

    facts: List[Fact] = []
    unlocatable: List[Dict[str, Any]] = []
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
                document_id=passage.document_id, label=passage.label,
                speaker_note=_speaker_note(passage),
                roster=roster_block, predicates=predicate_block, text=passage.text),
            schema=schema, tag="extract__%s" % passage.passage_id)

        cursor = 0
        for item in payload.get("facts", []) or []:
            counter += 1
            fact, note = _to_fact(item, passage, "ex_%03d" % counter, cursor)
            if fact is not None:
                facts.append(fact)
                cursor = fact.citations[0].locator["TextSpan"]["char_end"]
            elif note is not None:
                unlocatable.append(note)

    return facts, unlocatable


def _to_fact(item: Dict[str, Any], passage: Passage, fact_id: str, cursor: int):
    kind = item.get("asserter_kind")
    if kind not in VALID_ASSERTER_KINDS:
        return None, {"fact_id": fact_id, "reason": "invalid_asserter_kind",
                      "assertion": item.get("assertion"), "value": kind}
    if not item.get("assertion") or not item.get("quoted_text"):
        return None, {"fact_id": fact_id, "reason": "missing_assertion_or_quote",
                      "assertion": item.get("assertion")}

    located = locate(passage.text, item["quoted_text"], search_from=cursor)
    if located.status != RESOLVED:
        return None, {"fact_id": fact_id, "assertion": item.get("assertion"),
                      "reason": "quote_not_located", "notes": [located.status],
                      "passage_id": passage.passage_id,
                      "model_quote": item["quoted_text"],
                      "occurrences": located.occurrences}

    predicate = item.get("predicate")
    if predicate not in PREDICATES:
        predicate = None
    # Value normalisation is a lookup, never a model call. A value outside the
    # predicate's space becomes None, which leaves the fact ungrouped — a
    # finding, not something to paper over.
    value = normalise_value(predicate, item.get("value_raw")) if predicate else None

    normalised = None
    if item.get("raw_time_expression"):
        normalised = normalise_date(item["raw_time_expression"])

    return Fact(
        fact_id=fact_id, assertion=item["assertion"],
        asserter=Asserter(kind=kind, name=item.get("asserter_name")),
        provenance="extracted", subject=item.get("subject"),
        normalised_value=normalised,
        subject_entity_id=item.get("subject_entity_id"),
        predicate=predicate, value=value,
        event_id=EVENT_ID if (predicate and is_event_scoped(predicate)) else None,
        citations=[Citation(
            document_id=passage.document_id, document_version=passage.document_version,
            locator=text_span(passage.passage_id, located.char_start, located.char_end),
            quoted_text=located.canonical_text,
            resolution_note="located_by:%s" % located.method)],
    ), None
