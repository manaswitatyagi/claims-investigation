"""Deterministic comparison neighbourhoods, and narrow relationship classification.

NOT in any freeze.

    verified assertions
        -> groupby(subject_entity_id, event_id, predicate)      [deterministic]
        -> drop singletons (nothing to compare)                 [deterministic]
        -> all normalised values equal? CORROBORATING           [deterministic]
        -> otherwise, one narrow model call                     [LLM]

The model is never asked which facts concern the same thing. That is now a
`groupby`. Its remaining job is the one that genuinely needs language: given
assertions already known to share an entity, event, and property, say how they
relate.

A SINGLETON IS NOT A RELATIONSHIP. One source asserting something no other
source addresses is not "uncorroborated" — it is simply the only assertion made.
Representing that as a relationship would turn silence into a position, which
the difference contract forbids.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.claim_model import Fact
from src.llm.client import LLMClient
from src.llm.prompts_e2 import (NEIGHBORHOOD_SCHEMA, NEIGHBORHOOD_SYSTEM,
                                NEIGHBORHOOD_USER_TEMPLATE)
from src.ontology.vocabulary import comparable

CORROBORATING, COMPATIBLE, CONTRADICTORY = "CORROBORATING", "COMPATIBLE", "CONTRADICTORY"


def build_neighborhoods(facts: List[Fact]) -> Tuple[List[Dict[str, Any]], List[Fact]]:
    """Group comparable assertions. Returns (neighbourhoods, ungrouped facts)."""
    buckets: Dict[Tuple, List[Fact]] = {}
    ungrouped: List[Fact] = []
    for f in facts:
        key = f.neighborhood_key()
        if key is None:
            ungrouped.append(f)
            continue
        buckets.setdefault(key, []).append(f)

    out = []
    for (entity_id, event_id, predicate), members in sorted(
            buckets.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), kv[0][2])):
        out.append({
            "entity_id": entity_id, "event_id": event_id, "predicate": predicate,
            "members": members,
            "distinct_values": _distinct(members),
            "singleton": len(members) < 2,
        })
    return out, ungrouped


def _distinct(members: List[Fact]) -> List[Any]:
    seen, out = set(), []
    for m in members:
        key = repr(m.value)
        if key not in seen:
            seen.add(key)
            out.append(m.value)
    return out


def classify(neighborhood: Dict[str, Any], llm: Optional[LLMClient]) -> Dict[str, Any]:
    """Relationship for one neighbourhood.

    Deterministic where the ontology makes it deterministic: if the predicate's
    value space supports equality and every member normalised to the same value,
    the assertions agree, and paying a model to confirm that would be waste and
    would introduce variance where there is none.
    """
    members = neighborhood["members"]
    if neighborhood["singleton"]:
        return {"relationship": None, "method": "not_compared",
                "rationale": "Only one source addresses this property. Silence by "
                             "other sources is not a relationship."}

    values = [m.value for m in members]
    if comparable(neighborhood["predicate"]) and all(v is not None for v in values):
        if len({repr(v) for v in values}) == 1:
            return {"relationship": CORROBORATING, "method": "deterministic",
                    "rationale": "All sources normalise to the same value (%r)."
                                 % values[0]}

    if llm is None:
        return {"relationship": None, "method": "not_compared",
                "rationale": "No model available for semantic comparison."}

    payload = llm.complete_json(
        system=NEIGHBORHOOD_SYSTEM,
        user=NEIGHBORHOOD_USER_TEMPLATE.format(
            entity_id=neighborhood["entity_id"],
            event_id=neighborhood["event_id"] or "not event-scoped",
            predicate=neighborhood["predicate"],
            assertions=render_members(members)),
        schema=NEIGHBORHOOD_SCHEMA,
        tag="neighborhood__%s__%s" % (neighborhood["entity_id"],
                                      neighborhood["predicate"]))
    rel = payload.get("relationship")
    if rel not in (CORROBORATING, COMPATIBLE, CONTRADICTORY):
        return {"relationship": None, "method": "llm_invalid",
                "rationale": "Model returned %r" % rel}
    return {"relationship": rel, "method": "llm",
            "rationale": payload.get("rationale", "")}


def render_members(members: List[Fact]) -> str:
    """Assertions only. No quoted source text crosses this boundary — the same
    rule as the flat difference stage (D-020 P4)."""
    lines = []
    for m in members:
        who = m.asserter.kind
        if m.asserter.name:
            who = "%s (%s)" % (m.asserter.name, m.asserter.kind)
        doc = m.citations[0].document_id if m.citations else "unknown"
        lines.append("- id=%s | source=%s | asserted_by=%s | normalised_value=%r | %s"
                     % (m.fact_id, doc, who, m.value, m.assertion))
    return "\n".join(lines)


def to_differences(neighborhoods: List[Dict[str, Any]],
                   relationships: List[Dict[str, Any]]) -> List[Any]:
    """CONTRADICTORY neighbourhoods become Difference objects.

    Only contradictions become Differences: the existing type means "sources
    assert different things about the same thing", and a corroboration is not
    that. Corroborating and compatible relationships are carried in the
    neighbourhood projection, which is where they are useful — the flat model
    has nowhere to put them at all.
    """
    from src.claim_model import Difference, Position

    out, n = [], 0
    for nb, rel in zip(neighborhoods, relationships):
        if rel.get("relationship") != CONTRADICTORY:
            continue
        n += 1
        out.append(Difference(
            difference_id="nd_%03d" % n,
            subject=nb["predicate"],
            positions=[Position(fact_id=m.fact_id, stance=m.assertion)
                       for m in nb["members"]],
            detection_method="extracted"))
    return out
