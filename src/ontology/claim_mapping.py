"""Deterministic entity roster and anchor -> ontology mapping.

No model is involved here. The anchor's `N` becomes `north` through a lookup
table, exactly as instructed: a language model is not needed to convert
structured values that a dictionary already covers.

The ROSTER matters as much as the mapping. Entities are enumerated
deterministically from the claim record and the anchor, then offered to the
extractor as a CLOSED SET. The model selects from it; it never invents an
entity and never merges two. That keeps §7.1's propose-never-merge rule intact:
there is nothing to merge when the roster is fixed in advance.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.claim_model import Claim, Fact
from src.ontology.vocabulary import normalise_value

EVENT_ID = "crash_001"

#: anchor field -> (entity id, predicate). Fields with no entry are deliberately
#: left unmapped and surface as ungrouped facts, which is a finding.
ANCHOR_MAP: Dict[str, tuple] = {
    "CRASH_DATE": (EVENT_ID, "occurred_at"),
    "LOCATION_TEXT": (EVENT_ID, "location_text"),
    "ROADWAY_SURFACE_COND": ("roadway_1", "road_surface"),
    "LIGHTING_CONDITION": ("roadway_1", "lighting"),
    "FIRST_CRASH_TYPE": (EVENT_ID, "crash_type"),
    "POSTED_SPEED_LIMIT": ("roadway_1", "posted_speed_limit"),
    "UNIT_1_TRAVEL_DIRECTION": ("vehicle_1", "travel_direction"),
    "UNIT_1_MANEUVER": ("vehicle_1", "maneuver"),
    "UNIT_1_OCCUPANT_CNT": ("vehicle_1", "occupant_count"),
    "UNIT_2_UNIT_TYPE": ("vehicle_2", "unit_type"),
    "UNIT_2_OCCUPANT_CNT": ("vehicle_2", "occupant_count"),
    "UNIT_2_FIRST_CONTACT_POINT": ("vehicle_2", "contact_point"),
    "INJURIES_TOTAL": (EVENT_ID, "injuries_total"),
    "DAMAGE": (EVENT_ID, "damage_band"),
    # UNIT_1_VEHICLE / UNIT_2_VEHICLE are composite objects; unpacked below.
    # MOST_SEVERE_INJURY has no predicate in the Claim 001 vocabulary and is
    # left ungrouped rather than absorbed into injuries_total, which counts
    # people rather than grading severity.
}

_COMPOSITE = {"UNIT_1_VEHICLE": "vehicle_1", "UNIT_2_VEHICLE": "vehicle_2"}


def build_roster(claim: Claim) -> List[Dict[str, Any]]:
    """The closed set of entities the extractor may reference."""
    anchor = (claim.structured_records or {}).get("anchor") or {}
    by_field = {e["field"]: e["value"] for e in anchor.values()}

    def describe(field: str, fallback: str) -> str:
        v = by_field.get(field)
        if isinstance(v, dict):
            return "%s %s %s" % (v.get("year"), v.get("make"), v.get("model"))
        return fallback

    roster = [
        {"entity_id": "vehicle_1", "type": "vehicle",
         "description": "The claimant's vehicle (crash unit 1): %s"
                        % describe("UNIT_1_VEHICLE", "unknown")},
        {"entity_id": "vehicle_2", "type": "vehicle",
         "description": "The other vehicle (crash unit 2), parked: %s"
                        % describe("UNIT_2_VEHICLE", "unknown")},
        {"entity_id": "roadway_1", "type": "roadway",
         "description": "The roadway and conditions at the loss location"},
        {"entity_id": EVENT_ID, "type": "collision",
         "description": "The collision itself"},
    ]
    for p in claim.claim_record.get("parties", []):
        if p["role"] in ("claimant", "insured", "driver"):
            roster.append({"entity_id": "claimant_1", "type": "party",
                           "description": "The claimant, driver of vehicle_1"})
            break
    return roster


def annotate_anchor_facts(facts: List[Fact]) -> Dict[str, int]:
    """Attach entity/predicate/value to anchor facts. Pure lookup."""
    stats = {"mapped": 0, "unmapped": 0, "value_not_in_space": 0}
    for f in facts:
        subject = f.subject or ""
        if not subject.startswith("anchor:"):
            continue
        field = subject.split("anchor:", 1)[1]

        if field in _COMPOSITE:
            stats["unmapped"] += 1      # composite object; see _unpack_composite
            continue
        target = ANCHOR_MAP.get(field)
        if target is None:
            stats["unmapped"] += 1
            continue

        entity_id, predicate = target
        raw = f.citations[0].quoted_text if f.citations else None
        value = normalise_value(predicate, raw)
        f.subject_entity_id = entity_id
        f.predicate = predicate
        f.event_id = EVENT_ID
        f.value = value
        if value is None:
            stats["value_not_in_space"] += 1
        else:
            stats["mapped"] += 1
    return stats


def unpack_composite_vehicle_facts(claim: Claim, facts: List[Fact]) -> List[Fact]:
    """Split UNIT_n_VEHICLE into make / model / year assertions.

    A composite value cannot participate in a comparison — `{'year': 2015,
    'make': ...}` has no predicate. Splitting is deterministic and each part
    keeps the original citation, so provenance is preserved exactly.
    """
    from src.claim_model import Asserter, Citation, field_locator

    anchor = (claim.structured_records or {}).get("anchor") or {}
    out: List[Fact] = []
    n = 0
    for entry_id, entry in sorted(anchor.items()):
        entity_id = _COMPOSITE.get(entry.get("field"))
        if not entity_id or not isinstance(entry.get("value"), dict):
            continue
        for part, predicate in (("make", "vehicle_make"), ("model", "vehicle_model"),
                                ("year", "vehicle_year")):
            raw = entry["value"].get(part)
            if raw is None:
                continue
            n += 1
            out.append(Fact(
                fact_id="anv_%03d" % n,
                assertion="The structured crash record codes %s %s as %s."
                          % (entry["field"], part, raw),
                asserter=Asserter(kind="system_record"),
                provenance="deterministic",
                subject="anchor:%s.%s" % (entry["field"], part),
                subject_entity_id=entity_id, predicate=predicate,
                event_id=None, value=normalise_value(predicate, raw),
                citations=[Citation(document_id="rec_anchor", document_version="v1",
                                    locator=field_locator("anchor_record",
                                                          "%s.value" % entry_id),
                                    quoted_text=str(entry["value"]))]))
    return out


def ungrouped(facts: List[Fact]) -> List[Fact]:
    """Facts that cannot enter a neighbourhood, and why."""
    return [f for f in facts if f.neighborhood_key() is None]


def ungrouped_reason(f: Fact) -> str:
    if not f.subject_entity_id and not f.predicate:
        return "no entity and no predicate"
    if not f.subject_entity_id:
        return "no entity"
    if not f.predicate:
        return "no predicate in the Claim 001 vocabulary"
    return "unknown"
