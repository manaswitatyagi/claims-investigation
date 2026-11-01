"""E2 prompts — ontology-tagged extraction, and narrow neighbourhood comparison.

NOT in any freeze. E1 and E1b prompts are untouched.

TWO CHANGES FROM E1b, BOTH ABOUT STRUCTURE RATHER THAN SEMANTICS
----------------------------------------------------------------
1. Extraction additionally asks for `subject_entity_id` (from a CLOSED roster
   supplied per claim), `predicate` (from a CLOSED vocabulary), and a raw
   `value`. Values are normalised AFTERWARDS by lookup table, not by the model.
   The quote contract from E1b is unchanged.

2. The difference stage is replaced by a NEIGHBOURHOOD stage. The model no
   longer receives every fact and is no longer asked to work out which facts
   concern the same thing — that grouping is now deterministic. It receives one
   already-grouped set and classifies the relationship within it.

The prohibitions are carried over verbatim in spirit and mostly in wording: no
materiality, no credibility, no deciding which source is true, no characterising
anyone.
"""
from __future__ import annotations

from src.llm.prompts_e1b import EXTRACT_SYSTEM as _E1B_EXTRACT_SYSTEM

_ONTOLOGY_RULES = """

10. TAG EACH FACT WITH AN ENTITY AND A PREDICATE. Every fact must name the entity it is about, chosen from the ENTITY ROSTER below, and the property it asserts, chosen from the PREDICATE VOCABULARY below. Both are closed sets: pick from them or return nothing. Never invent an entity id or a predicate name.

11. IF NO PREDICATE FITS, OMIT THE PREDICATE. Returning the fact with `predicate` set to null is correct and useful. Forcing a fact into a nearly-right predicate destroys the comparison it would otherwise feed. In particular, do not map a qualitative impression of speed onto a numeric speed predicate, do not map a causal or fault judgement onto a physical property, and do not map what someone REPORTS SEEING onto a predicate that records what a thing IS.

12. GIVE THE RAW VALUE, NOT A TIDIED ONE. Put the value as the source expresses it into `value_raw`. Code normalises it against a lookup table afterwards. For a range or an approximation, give the range ("25 to 30"), never a midpoint."""

EXTRACT_SYSTEM = _E1B_EXTRACT_SYSTEM + _ONTOLOGY_RULES

EXTRACT_USER_TEMPLATE = """PASSAGE ID: {passage_id}
DOCUMENT: {document_type} ({document_id})
LABEL: {label}
{speaker_note}
ENTITY ROSTER — choose `subject_entity_id` from these ids only:
{roster}

PREDICATE VOCABULARY — choose `predicate` from these names only, or null:
{predicates}

The passage text follows between the markers.

<<<PASSAGE_BEGIN>>>
{text}
<<<PASSAGE_END>>>

Extract the facts this passage asserts."""


def extract_schema(entity_ids, predicate_names):
    """Built per claim so the roster and vocabulary are enforced by the schema,
    not merely requested in prose."""
    return {
        "type": "object", "additionalProperties": False, "required": ["facts"],
        "properties": {"facts": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["assertion", "asserter_kind", "quoted_text", "subject",
                         "subject_entity_id", "predicate", "value_raw"],
            "properties": {
                "assertion": {"type": "string"},
                "asserter_kind": {"enum": ["claimant", "insured", "witness",
                                           "police_officer", "adjuster", "provider",
                                           "system_record", "attorney"]},
                "asserter_name": {"type": ["string", "null"]},
                "subject": {"type": "string",
                            "description": "Short snake_case key for what this fact is about."},
                "subject_entity_id": {"enum": list(entity_ids) + [None]},
                "predicate": {"enum": list(predicate_names) + [None]},
                "value_raw": {"type": ["string", "null"],
                              "description": "The value as the source expresses it. "
                                             "Ranges stay ranges. Code normalises this."},
                "quoted_text": {"type": "string"},
                "raw_time_expression": {"type": ["string", "null"]},
                "revised": {"type": ["boolean", "null"]},
                "superseded_text": {"type": ["string", "null"]},
            }}}},
    }


# ---------------------------------------------------------------------------
# Neighbourhood relationship classification
# ---------------------------------------------------------------------------

NEIGHBORHOOD_SYSTEM = """You classify the relationship between assertions that are ALREADY KNOWN to concern the same entity, the same event, and the same property.

You do not need to work out what these assertions are about. That has been established. Your only task is to characterise how they relate.

Return exactly one relationship for the set:

  CORROBORATING  - the assertions state the same thing. They agree.
  COMPATIBLE     - they differ in wording or precision but one state of affairs satisfies all of them. An approximation that contains or overlaps another value is compatible.
  CONTRADICTORY  - no single state of affairs could satisfy all of them.

RULES

1. NORMAL VARIATION IS NOT CONTRADICTION. People recounting a stressful event are routinely inconsistent in detail. Rounded values, differing precision, and different wording for the same thing are COMPATIBLE, not CONTRADICTORY.

2. SILENCE IS NOT A POSITION. You are only shown assertions that were actually made. A source absent from this set has not disagreed with anything.

3. DO NOT DECIDE WHICH SOURCE IS CORRECT. You report the relationship. You never resolve it, never rank sources by reliability, and never note that one source is official, independent, or objective. A structured record and a person's recollection are two assertions, presented alike.

4. DO NOT CHARACTERISE ANYONE. Never state or imply that a party is lying, mistaken, exaggerating, evasive, impaired, or suspicious. Never infer motive, intent, or state of mind.

5. NO MATERIALITY, NO CREDIBILITY, NO LIKELIHOOD. Do not say which relationships matter, rank them, score them, or estimate which assertion is more probably true. A human makes those judgements. Any such field will be discarded.

6. EXPLAIN BRIEFLY AND FACTUALLY. One sentence stating what differs or agrees, in neutral terms."""

NEIGHBORHOOD_USER_TEMPLATE = """ENTITY: {entity_id}
EVENT: {event_id}
PROPERTY: {predicate}

These assertions all concern that entity, event, and property:

{assertions}

Classify their relationship."""

NEIGHBORHOOD_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["relationship", "rationale"],
    "properties": {
        "relationship": {"enum": ["CORROBORATING", "COMPATIBLE", "CONTRADICTORY"]},
        "rationale": {"type": "string"},
    },
}
