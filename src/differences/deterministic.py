"""Stage 8a — DETERMINISTIC DIFFERENCES.

PRD §11: three of the ten DOCMAP §3 conflict pairs need no LLM at all — pair 4
(stated driver is not a listed driver), pair 8 (requested but never received,
which lands in Open Questions), and pair 10 (impossible chronology). They are
among the most materially consequential rows in the table and the cheapest to
implement. "Any V1 that reaches for a model first has mis-sequenced its own
build."

Each detector returns supporting Facts alongside the Difference, because a
Difference's positions must point at Facts that carry their own citations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.claim_model import (Asserter, Citation, Claim, Difference, Fact,
                             Position, boolean_value, field_locator)
from src.normalization.dates import days_between

SYSTEM = Asserter(kind="system_record", name=None)


def detect(claim: Claim) -> Tuple[List[Fact], List[Difference]]:
    facts: List[Fact] = []
    diffs: List[Difference] = []
    n = _Counter("dd")
    d = _Counter("ddiff")

    _driver_not_listed(claim, facts, diffs, n, d)
    _vehicle_not_scheduled(claim, facts, diffs, n, d)
    _impossible_chronology(claim, facts, diffs, n, d)

    return facts, diffs


def _driver_not_listed(claim, facts, diffs, n, d) -> None:
    """DOCMAP pair 4. Deterministic, and materially consequential."""
    pol = claim.policy_record
    if not pol:
        return
    stated = _stated_driver(claim)
    if not stated:
        return
    driver_name, record, path = stated
    listed = pol.get("listed_drivers", [])
    if _name_in(driver_name, listed):
        return

    f_stated = Fact(
        fact_id=n(), assertion="The driver of record for this loss is %s." % driver_name,
        asserter=SYSTEM, provenance="deterministic", subject="driver_identity",
        citations=[Citation(document_id=_doc_for(claim, record), document_version="v1",
                            locator=field_locator(record, path), quoted_text=driver_name)])
    f_listed = Fact(
        fact_id=n(),
        assertion="The policy lists %s as driver(s)." % (", ".join(listed) or "no drivers"),
        asserter=SYSTEM, provenance="deterministic", subject="driver_identity",
        normalised_value=boolean_value(False),
        citations=[Citation(document_id="rec_policy", document_version="v1",
                            locator=field_locator("policy_record", "listed_drivers"),
                            quoted_text=str(listed))])
    facts.extend([f_stated, f_listed])
    diffs.append(Difference(
        difference_id=d(), subject="driver_is_a_listed_driver",
        detection_method="deterministic",
        positions=[Position(fact_id=f_stated.fact_id, stance=f_stated.assertion),
                   Position(fact_id=f_listed.fact_id, stance=f_listed.assertion)]))


def _vehicle_not_scheduled(claim, facts, diffs, n, d) -> None:
    pol = claim.policy_record
    if not pol:
        return
    vin = _stated_vin(claim)
    if not vin:
        return
    scheduled = [v.get("vin") for v in pol.get("scheduled_vehicles", [])]
    if vin[0] in scheduled:
        return
    value, record, path = vin

    f_a = Fact(
        fact_id=n(), assertion="The vehicle involved has VIN %s." % value,
        asserter=SYSTEM, provenance="deterministic", subject="vehicle_scheduled",
        citations=[Citation(document_id=_doc_for(claim, record), document_version="v1",
                            locator=field_locator(record, path), quoted_text=value)])
    f_b = Fact(
        fact_id=n(),
        assertion="The policy schedules VIN(s) %s." % (", ".join(x for x in scheduled if x) or "none"),
        asserter=SYSTEM, provenance="deterministic", subject="vehicle_scheduled",
        citations=[Citation(document_id="rec_policy", document_version="v1",
                            locator=field_locator("policy_record", "scheduled_vehicles"),
                            quoted_text=str(pol.get("scheduled_vehicles", [])))])
    facts.extend([f_a, f_b])
    diffs.append(Difference(
        difference_id=d(), subject="vehicle_is_a_scheduled_vehicle",
        detection_method="deterministic",
        positions=[Position(fact_id=f_a.fact_id, stance=f_a.assertion),
                   Position(fact_id=f_b.fact_id, stance=f_b.assertion)]))


def _impossible_chronology(claim, facts, diffs, n, d) -> None:
    """DOCMAP pair 10. Pure date arithmetic, no LLM."""
    cr = claim.claim_record
    if not cr.get("loss_date") or not cr.get("reported_date"):
        return          # nothing to compare; absence is reported in not_assessed
    try:
        delta = days_between(cr["loss_date"], cr["reported_date"])
    except ValueError:
        return
    if delta >= 0:
        return

    f_a = Fact(
        fact_id=n(), assertion="The reported date of loss is %s." % cr["loss_date"],
        asserter=SYSTEM, provenance="deterministic", subject="chronology_consistency",
        citations=[Citation(document_id="rec_claim", document_version="v1",
                            locator=field_locator("claim_record", "loss_date"),
                            quoted_text=cr["loss_date"])])
    f_b = Fact(
        fact_id=n(),
        assertion="The claim was reported on %s, which precedes the reported date of loss."
                  % cr["reported_date"],
        asserter=SYSTEM, provenance="deterministic", subject="chronology_consistency",
        citations=[Citation(document_id="rec_claim", document_version="v1",
                            locator=field_locator("claim_record", "reported_date"),
                            quoted_text=cr["reported_date"])])
    facts.extend([f_a, f_b])
    diffs.append(Difference(
        difference_id=d(), subject="report_date_precedes_loss_date",
        detection_method="deterministic",
        positions=[Position(fact_id=f_a.fact_id, stance=f_a.assertion),
                   Position(fact_id=f_b.fact_id, stance=f_b.assertion)]))


def _stated_driver(claim: Claim) -> Optional[Tuple[str, str, str]]:
    for doc in claim.documents:
        sf = doc.structured_fields or {}
        if sf.get("driver_name"):
            return sf["driver_name"], doc.document_id, "driver_name"
    people = (claim.structured_records or {}).get("people", []) or []
    for i, p in enumerate(people):
        if p.get("role") == "driver" and p.get("name"):
            return p["name"], "people_records", "%d.name" % i
    return None


def _stated_vin(claim: Claim) -> Optional[Tuple[str, str, str]]:
    for doc in claim.documents:
        sf = doc.structured_fields or {}
        if sf.get("vehicle_vin"):
            return sf["vehicle_vin"], doc.document_id, "vehicle_vin"
    vehicles = (claim.structured_records or {}).get("vehicles", []) or []
    for i, v in enumerate(vehicles):
        if v.get("vin") and v.get("is_insured_vehicle"):
            return v["vin"], "vehicle_records", "%d.vin" % i
    return None


def _name_in(name: str, listed: List[str]) -> bool:
    """Exact, case-insensitive, whitespace-normalised.

    Deliberately NOT fuzzy. Treating "R. Smith" as "Robert Smith" is entity
    resolution, and entity resolution is proposed to a human, never applied
    silently — a silent merge is invisible once it has happened.
    """
    norm = " ".join(name.split()).lower()
    return any(" ".join(x.split()).lower() == norm for x in listed)


def _doc_for(claim: Claim, record: str) -> str:
    for doc in claim.documents:
        if doc.document_id == record:
            return doc.document_id
    return {"people_records": "rec_people", "vehicle_records": "rec_vehicles"}.get(record, record)


class _Counter:
    def __init__(self, prefix: str) -> None:
        self.prefix, self.i = prefix, 0

    def __call__(self) -> str:
        self.i += 1
        return "%s_%03d" % (self.prefix, self.i)
