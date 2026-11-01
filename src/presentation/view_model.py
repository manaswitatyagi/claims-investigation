"""Presentation DTO for the claim view.

This is the ONLY thing the UI sees. It is a deliberate boundary: React never
touches `Fact`, `Difference`, evaluation internals, or the E2 artifact layout, so
the pipeline can be reshaped without rewriting the screen.

TWO INVARIANTS THIS LAYER EXISTS TO HOLD
----------------------------------------
1. **The UI never infers a relationship.** `relationship` is computed in the
   domain layer and shipped as data. There is no code path by which the frontend
   could decide two assertions disagree.

2. **"Verified" means traced, not true.** Every assertion carries the exact quote,
   passage, and offsets that were checked against the source. It does not carry,
   and this layer will not compute, any claim about whether the assertion is
   correct. Materiality, liability, credibility, and fraud remain unasserted
   (D-014, D-017, D-033).

SHAPE
-----
Normalised, not nested: assertions live in one map keyed by id, and
neighbourhoods reference them. That is what makes the streaming milestone a
patch rather than a rewrite — a later `/events` stream can emit
`assertion_added` / `neighborhood_changed` against these same ids and the screen
updates in place.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VIEW_VERSION = "claim-view/1"

#: Human labels for the controlled vocabulary. Presentation only — the ontology
#: keys stay canonical everywhere else.
PREDICATE_LABELS = {
    "travel_direction": "Travel direction", "maneuver": "Maneuver",
    "approximate_speed": "Approximate speed", "loss_of_control": "Loss of control",
    "contact_point": "Contact point", "occupant_count": "Occupant count",
    "occupant_observation": "Occupants observed", "vehicle_make": "Make",
    "vehicle_model": "Model", "vehicle_year": "Year", "unit_type": "Unit type",
    "road_surface": "Road surface", "lighting": "Lighting",
    "posted_speed_limit": "Posted speed limit",
    "weather_before_loss": "Weather before loss", "occurred_at": "Occurred at",
    "location_text": "Location", "crash_type": "Crash type",
    "injuries_total": "Injuries recorded", "damage_band": "Damage band",
    "post_collision_action": "Post-collision actions",
    "reason_for_leaving": "Stated reason for leaving",
    "intended_to_report": "Intended to report", "injury_belief": "Belief about injury",
    "awareness_of_severity": "Awareness of severity",
    "recall_limitation": "Stated limits of recall",
}

SOURCE_LABELS = {
    "rec_anchor": ("Structured crash record", "crash_record"),
    "doc_fnol": ("First Notice of Loss", "fnol"),
    "doc_statement": ("Recorded statement", "recorded_statement"),
    "rec_claim": ("Claim record", "claim_record"),
    "rec_policy": ("Policy record", "policy_record"),
}


def build_claim_view(run_dir: str, fixture_dir: str) -> Dict[str, Any]:
    result = _load(os.path.join(run_dir, "result.json"))
    neighborhoods = _load(os.path.join(run_dir, "neighborhoods.json"))
    ungrouped = _load(os.path.join(run_dir, "ungrouped.json"))
    meta = _load(os.path.join(run_dir, "run_meta.json"))
    claim_raw = _load(os.path.join(fixture_dir, "claim.json"))

    passages = _passages(fixture_dir, claim_raw)
    assertions = _assertions(result, neighborhoods, passages)
    nbs = _neighborhoods(neighborhoods, assertions)

    return {
        "view_version": VIEW_VERSION,
        "claim": _claim_header(claim_raw, result, meta),
        "sources": _sources(assertions, passages),
        "entities": _entities(nbs),
        "neighborhoods": nbs,
        "assertions": assertions,
        "timeline": _timeline(result),
        "ungrouped": [
            {"assertion_id": u["fact_id"], "text": u["assertion"],
             "provenance": u["provenance"], "reason": u["reason"]}
            for u in ungrouped],
        "not_assessed": result.get("not_assessed", []),
    }


# ---------------------------------------------------------------------------

def _load(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _claim_header(claim_raw, result, meta) -> Dict[str, Any]:
    cr = claim_raw["claim_record"]
    return {
        "claim_id": result["claim_id"],
        "claim_number": cr.get("claim_number"),
        "checkpoint": result.get("checkpoint"),
        "status": cr.get("status"),
        "loss_date": cr.get("loss_date"),
        "loss_location": cr.get("loss_location"),
        "generated_at": result.get("generated_at"),
        "model_id": meta.get("model") or result.get("model_id"),
        "prompt_version": result.get("prompt_version"),
        "provenance_disclaimer": claim_raw["provenance"]["disclaimer"],
        # Stated on the screen, not buried in a tooltip.
        "verified_means": ("Verified means this assertion was traced to exact text in a "
                           "source document and that citation was checked in code. It does "
                           "NOT mean the assertion is true. No stage of this system decides "
                           "which source is correct, which differences matter, or anything "
                           "about credibility, liability, or fraud."),
    }


def _passages(fixture_dir: str, claim_raw) -> Dict[str, Dict[str, Any]]:
    out = {}
    for entry in claim_raw.get("documents", []):
        doc = entry
        if isinstance(entry, str):
            doc = _load(os.path.join(fixture_dir, entry))
        for p in doc.get("passages", []) or []:
            out[p["passage_id"]] = {"passage_id": p["passage_id"], "label": p["label"],
                                    "text": p["text"], "document_id": doc["document_id"]}
    return out


def _assertions(result, neighborhoods, passages) -> Dict[str, Dict[str, Any]]:
    """Only assertions that reached a neighbourhood, plus their evidence.

    An assertion in the view has, by construction, a citation that resolved.
    Nothing ungrounded appears on the screen at all (D-020 P2).
    """
    in_view = {m["fact_id"] for n in neighborhoods for m in n["members"]}
    by_id = {f["fact_id"]: f for f in result["facts"]}

    out: Dict[str, Dict[str, Any]] = {}
    for n in neighborhoods:
        for m in n["members"]:
            fid = m["fact_id"]
            if fid in out:
                continue
            fact = by_id.get(fid, {})
            cit = m.get("citation") or (fact.get("citations") or [{}])[0]
            # The Fact carries the real normalised value. The neighbourhood
            # member carries repr() of it for debug display, which would never
            # compare equal to a freshly normalised value on ingestion.
            value = fact.get("value") if "value" in fact else _unrepr(m.get("value"))
            out[fid] = {
                "assertion_id": fid,
                "entity_id": n["entity_id"],
                "event_id": n["event_id"],
                "predicate": n["predicate"],
                "predicate_label": _label(n["predicate"]),
                "value": _value_display(value),
                "value_normalised": value,
                "text": m["assertion"],
                "asserter_kind": m["asserter"],
                "asserter_name": (fact.get("asserter") or {}).get("name"),
                "provenance": fact.get("provenance", "extracted"),
                "source_id": m["document_id"],
                "source_name": _source_name(m["document_id"]),
                "evidence": _evidence(cit, passages),
            }
    return out


def _evidence(cit: Dict[str, Any], passages) -> Dict[str, Any]:
    loc = cit.get("locator") or {}
    ev: Dict[str, Any] = {
        "quote": cit.get("quoted_text"),
        "verified": bool(cit.get("resolved", True)),
        "resolution_note": cit.get("resolution_note"),
        "document_id": cit.get("document_id"),
        "document_version": cit.get("document_version"),
        "locator_kind": next(iter(loc), None),
        "passage_id": None, "char_start": None, "char_end": None,
        "field_record": None, "field_path": None, "passage_label": None,
        "passage_text": None,
    }
    if "TextSpan" in loc:
        ts = loc["TextSpan"]
        ev.update(passage_id=ts["passage_id"], char_start=ts["char_start"],
                  char_end=ts["char_end"])
        p = passages.get(ts["passage_id"])
        if p:
            ev["passage_label"] = p["label"]
            ev["passage_text"] = p["text"]
    elif "Field" in loc:
        ev.update(field_record=loc["Field"]["record"], field_path=loc["Field"]["field_path"])
    return ev


def _neighborhoods(neighborhoods, assertions) -> List[Dict[str, Any]]:
    out = []
    for i, n in enumerate(neighborhoods, 1):
        ids = [m["fact_id"] for m in n["members"]]
        sources = []
        for a in (assertions[i_] for i_ in ids if i_ in assertions):
            if a["source_id"] not in sources:
                sources.append(a["source_id"])
        out.append({
            "neighborhood_id": "nb_%03d" % i,
            "entity_id": n["entity_id"],
            "event_id": n["event_id"],
            "predicate": n["predicate"],
            "predicate_label": _label(n["predicate"]),
            "relationship": n["relationship"],
            "relationship_method": n["method"],
            "rationale": n["rationale"],
            "singleton": n["singleton"],
            "assertion_ids": ids,
            "source_ids": sources,
            "distinct_value_count": len(n.get("distinct_values") or []),
        })
    return out


def _entities(nbs) -> List[Dict[str, Any]]:
    """Entities in display order, each carrying its neighbourhood ids."""
    order = ["vehicle_1", "vehicle_2", "roadway_1", "crash_001", "claimant_1"]
    labels = {"vehicle_1": "Vehicle 1 — claimant's vehicle",
              "vehicle_2": "Vehicle 2 — the parked vehicle",
              "roadway_1": "Roadway and conditions",
              "crash_001": "The collision", "claimant_1": "The claimant"}
    kinds = {"vehicle_1": "vehicle", "vehicle_2": "vehicle", "roadway_1": "roadway",
             "crash_001": "collision", "claimant_1": "party"}
    seen: Dict[str, List[str]] = {}
    for n in nbs:
        seen.setdefault(n["entity_id"], []).append(n["neighborhood_id"])
    ordered = [e for e in order if e in seen] + [e for e in seen if e not in order]
    return [{"entity_id": e, "label": labels.get(e, e), "type": kinds.get(e, "entity"),
             "neighborhood_ids": seen[e],
             "contradiction_count": sum(
                 1 for n in nbs if n["entity_id"] == e
                 and n["relationship"] == "CONTRADICTORY")}
            for e in ordered]


def _sources(assertions, passages) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for a in assertions.values():
        counts[a["source_id"]] = counts.get(a["source_id"], 0) + 1
    order = ["rec_anchor", "doc_fnol", "doc_statement"]
    ids = [s for s in order if s in counts] + [s for s in counts if s not in order]
    out = []
    for sid in ids:
        name, kind = SOURCE_LABELS.get(sid, (sid, "other"))
        out.append({
            "source_id": sid, "name": name, "type": kind,
            "verified_assertion_count": counts[sid],
            # Structured records are read by code; narrative is extracted then
            # its citation verified. Both are "verified"; the route differs.
            "processing": ("read deterministically" if sid.startswith("rec_")
                           else "extracted, quote located in code, citation verified"),
            "verification_status": "verified",
            "passage_ids": [p["passage_id"] for p in passages.values()
                            if p["document_id"] == sid],
        })
    return out


def _timeline(result) -> Dict[str, List[Dict[str, Any]]]:
    """Deterministic, both axes. No model orders this (PRD §10.4)."""
    out: Dict[str, List[Dict[str, Any]]] = {"occurred": [], "became_known": []}
    for e in result.get("timeline", []):
        date = (e.get("when") or {}).get("Date") or {}
        out.setdefault(e["axis"], []).append({
            "event_id": e["event_id"], "label": e["label"],
            "when": date.get("value"), "precision": date.get("precision"),
            "raw_expression": date.get("raw_expression"),
            "ordering_confidence": e["ordering_confidence"],
            "source_assertion_ids": e.get("source_fact_ids", []),
        })
    return out


def _unrepr(raw: Any) -> Any:
    """Recover a value from the debug repr in an E2 neighbourhood member.

    Only needed for artifacts whose Fact lost its `value`; new ingestion never
    goes through here.
    """
    if not isinstance(raw, str):
        return raw
    try:
        import ast
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return raw


def _label(predicate: Optional[str]) -> str:
    if not predicate:
        return "Unclassified"
    return PREDICATE_LABELS.get(predicate, predicate.replace("_", " ").capitalize())


def _source_name(source_id: str) -> str:
    return SOURCE_LABELS.get(source_id, (source_id, ""))[0]


def _value_display(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, dict) and "min" in value:
        lo, hi, unit = value.get("min"), value.get("max"), value.get("unit") or ""
        fmt = lambda v: ("%g" % v) if isinstance(v, (int, float)) else str(v)
        base = fmt(lo) if lo == hi else "%s–%s" % (fmt(lo), fmt(hi))
        return ("%s %s" % (base, unit)).strip()
    if isinstance(value, list):
        return ", ".join(str(v).replace("_", " ") for v in value)
    return str(value).replace("_", " ")
