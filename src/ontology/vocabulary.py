"""Minimal controlled vocabulary — only what Claim 001 requires.

This is NOT a general insurance ontology and must not become one speculatively.
Later fixtures force its expansion; that is the intended growth path (D-036).

THE POINT OF A CONTROLLED VOCABULARY
------------------------------------
`north` / `N` / `northbound` must collapse to one value so three sources can be
compared. `25 mph` / `moving quickly` / `failing to reduce speed` must NOT, even
though they all sound like speed — one is a measurement, one is a qualitative
impression, one is a causal judgement. Collapsing them would manufacture
agreement or conflict that no source asserted.

Two distinctions in here are doing real work and are easy to erode:

1. `posted_speed_limit` is an EVENT property (a road attribute); `approximate_speed`
   is a VEHICLE property (how fast it was going). They are never comparable. The
   gold answer names exactly this as a difference that must not be reported.

2. `occupant_count` (what a record states) is separate from `occupant_observation`
   (what a person reports seeing). "The record says zero occupants" and "the
   claimant did not see anyone" are not the same claim — a failure to observe is
   not an absence. Grouping them would invite a corroboration the sources do not
   support, and the gold `facts_must_not_appear` list forbids exactly that
   inference.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

ENTITY_TYPES = {"vehicle", "party", "roadway"}
EVENT_TYPES = {"collision"}
DOCUMENT_TYPES = {"fnol", "recorded_statement", "crash_record"}

#: Which entity type each predicate attaches to, and how its value behaves.
#:
#: value_space:
#:   enum        - closed set; equality is meaningful
#:   quantity    - numeric range or point with a unit; overlap is meaningful
#:   text        - free text; NOT deterministically comparable, LLM required
#:   set         - unordered set of enum members; subset/overlap is meaningful
#:   temporal    - date/time, possibly vague
PREDICATES: Dict[str, Dict[str, Any]] = {
    # -- vehicle ------------------------------------------------------------
    "travel_direction": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "enum",
        "values": ["north", "south", "east", "west",
                   "northeast", "northwest", "southeast", "southwest"],
        "note": "Compass heading of travel. Distinct from `maneuver`."},
    "maneuver": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "enum",
        "values": ["right_turn", "left_turn", "straight", "parked", "reversing",
                   "stopped", "u_turn", "changing_lanes"],
        "note": "What the vehicle was doing. `parked` is a maneuver value AND a "
                "unit type; both are recorded rather than merged."},
    "approximate_speed": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "quantity",
        "unit": "mph",
        "note": "MEASURED OR ESTIMATED speed of this vehicle. A range stays a "
                "range. Qualitative impressions ('moving quickly') are NOT "
                "admitted here — they have no numeric value and forcing one "
                "invents precision. They stay ungrouped, which is a finding."},
    "loss_of_control": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "enum",
        "values": ["slid", "skidded", "none_reported"],
        "note": "Reported loss of control. Silence is NOT `none_reported` — "
                "absence of an assertion is not an assertion."},
    "contact_point": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "enum",
        "values": ["front", "rear", "left_side", "right_side", "front_nearside",
                   "front_offside", "rear_right_corner", "rear_left_corner"],
        "note": "Contact point ON THIS VEHICLE. Two vehicles' contact points are "
                "different facts, not competing accounts of one."},
    "occupant_count": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "quantity",
        "unit": "occupants",
        "note": "A count stated by a record. See `occupant_observation`."},
    "occupant_observation": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "enum",
        "values": ["none_observed", "occupant_observed"],
        "note": "What an observer REPORTS SEEING. Deliberately distinct from "
                "`occupant_count`: a failure to observe is not an absence."},
    "vehicle_make": {"subject_type": "vehicle", "event_scoped": False,
                     "value_space": "text"},
    "vehicle_model": {"subject_type": "vehicle", "event_scoped": False,
                      "value_space": "text"},
    "vehicle_year": {"subject_type": "vehicle", "event_scoped": False,
                     "value_space": "quantity", "unit": "year"},
    "unit_type": {
        "subject_type": "vehicle", "event_scoped": True, "value_space": "enum",
        "values": ["driving", "parked"],
        "note": "Crash-record classification of the unit's state."},

    # -- event / roadway ----------------------------------------------------
    "road_surface": {
        "subject_type": "roadway", "event_scoped": True, "value_space": "enum",
        "values": ["wet", "dry", "snow", "ice", "sand_mud_dirt", "unknown"]},
    "lighting": {
        "subject_type": "roadway", "event_scoped": True, "value_space": "enum",
        "values": ["daylight", "darkness", "darkness_lighted_road", "dusk", "dawn"]},
    "posted_speed_limit": {
        "subject_type": "roadway", "event_scoped": True, "value_space": "quantity",
        "unit": "mph",
        "note": "A ROAD attribute. NEVER comparable with `approximate_speed`, "
                "which is a vehicle attribute. Different properties of different "
                "entities."},
    "weather_before_loss": {
        "subject_type": "roadway", "event_scoped": True, "value_space": "enum",
        "values": ["rain", "clear", "snow", "fog", "unknown"]},
    "occurred_at": {"subject_type": "collision", "event_scoped": True,
                    "value_space": "temporal"},
    "location_text": {"subject_type": "collision", "event_scoped": True,
                      "value_space": "text"},
    "crash_type": {"subject_type": "collision", "event_scoped": True,
                   "value_space": "text"},
    "injuries_total": {"subject_type": "collision", "event_scoped": True,
                       "value_space": "quantity", "unit": "persons"},
    "damage_band": {"subject_type": "collision", "event_scoped": True,
                    "value_space": "text"},

    # -- party --------------------------------------------------------------
    "post_collision_action": {
        "subject_type": "party", "event_scoped": True, "value_space": "set",
        "values": ["stopped", "inspected_vehicles", "left_scene",
                   "exchanged_details", "called_police", "rendered_aid"]},
    "reason_for_leaving": {
        "subject_type": "party", "event_scoped": True, "value_space": "text",
        "note": "Free text by necessity. A stated reason is not enumerable "
                "without deciding what counts as the same reason, which is a "
                "judgement no stage of this system may make."},
    "intended_to_report": {
        "subject_type": "party", "event_scoped": True, "value_space": "enum",
        "values": ["yes", "no"],
        "note": "An INTENTION. Never conflated with whether a report was made."},
    "injury_belief": {
        "subject_type": "party", "event_scoped": True, "value_space": "enum",
        "values": ["believed_none", "believed_injury"],
        "note": "A BELIEF held by a person, never an injury fact. The claim "
                "record's injury coding is `injuries_total` on the event."},
    "awareness_of_severity": {
        "subject_type": "party", "event_scoped": True, "value_space": "text"},
    "recall_limitation": {
        "subject_type": "party", "event_scoped": True, "value_space": "text",
        "note": "A stated inability to recall. Takes no position on the "
                "underlying fact and therefore cannot conflict with one."},
}

#: Deterministic value normalisation. Lookup tables, never a model call.
_VALUE_ALIASES: Dict[str, Dict[str, str]] = {
    "travel_direction": {
        "n": "north", "north": "north", "northbound": "north", "nb": "north",
        "s": "south", "south": "south", "southbound": "south", "sb": "south",
        "e": "east", "east": "east", "eastbound": "east", "eb": "east",
        "w": "west", "west": "west", "westbound": "west", "wb": "west",
    },
    "maneuver": {
        "turning right": "right_turn", "right turn": "right_turn",
        "right_turn": "right_turn", "turning left": "left_turn",
        "left turn": "left_turn", "left_turn": "left_turn",
        "parked": "parked", "straight ahead": "straight", "straight": "straight",
    },
    "road_surface": {"wet": "wet", "dry": "dry", "snow": "snow", "ice": "ice"},
    "lighting": {
        "darkness, lighted road": "darkness_lighted_road",
        "darkness_lighted_road": "darkness_lighted_road",
        "darkness": "darkness", "daylight": "daylight",
    },
    "unit_type": {"parked": "parked", "driving": "driving"},
    "contact_point": {
        "front": "front", "rear": "rear",
        "rear-right-corner": "rear_right_corner", "rear_right_corner": "rear_right_corner",
        "rear right corner": "rear_right_corner",
        "rear-left-corner": "rear_left_corner", "rear_left_corner": "rear_left_corner",
        "front nearside": "front_nearside", "front-nearside": "front_nearside",
        "front_nearside": "front_nearside",
        "left side": "left_side", "right side": "right_side",
    },
    "loss_of_control": {"slid": "slid", "skidded": "skidded",
                        "none_reported": "none_reported"},
    "post_collision_action": {},
    "weather_before_loss": {"rain": "rain", "raining": "rain", "clear": "clear"},
    "injury_belief": {"believed_none": "believed_none",
                      "believed_injury": "believed_injury"},
    "occupant_observation": {"none_observed": "none_observed",
                             "occupant_observed": "occupant_observed"},
    "intended_to_report": {"yes": "yes", "no": "no", "true": "yes", "false": "no"},
}


def normalise_value(predicate: str, raw: Any) -> Optional[Any]:
    """Deterministic normalisation. Returns None when the raw value is not in
    the predicate's value space — which is a finding, not a failure to paper over.
    """
    spec = PREDICATES.get(predicate)
    if spec is None or raw is None:
        return None
    space = spec["value_space"]

    if space == "enum":
        key = str(raw).strip().lower()
        alias = _VALUE_ALIASES.get(predicate, {})
        mapped = alias.get(key, key if key in spec.get("values", []) else None)
        return mapped
    if space == "set":
        items = raw if isinstance(raw, list) else [raw]
        out = sorted({str(i).strip().lower() for i in items}
                     & set(spec.get("values", [])))
        return out or None
    if space == "quantity":
        return _quantity(raw, spec.get("unit"))
    if space in ("text", "temporal"):
        return str(raw).strip() or None
    return None


def _quantity(raw: Any, unit: Optional[str]):
    """A range stays a range. Never collapsed to a midpoint."""
    if isinstance(raw, dict) and ("min" in raw or "max" in raw):
        lo, hi = raw.get("min"), raw.get("max")
        if lo is None and hi is None:
            return None
        return {"min": lo, "max": hi if hi is not None else lo, "unit": unit}
    try:
        v = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return {"min": v, "max": v, "unit": unit}


def is_event_scoped(predicate: str) -> bool:
    return bool(PREDICATES.get(predicate, {}).get("event_scoped"))


def value_space(predicate: str) -> Optional[str]:
    return (PREDICATES.get(predicate) or {}).get("value_space")


def comparable(predicate: str) -> bool:
    """Whether equality of normalised values is deterministically meaningful."""
    return value_space(predicate) in ("enum", "set", "quantity")
