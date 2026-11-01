"""Stage 3 — READ + DERIVE. Deterministic facts.

No LLM touches anything in this module. Every fact produced here cites a
`Field` locator, so a user can check a deterministic fact as easily as an
extracted one — and a derived fact cites *both* operands, which makes the
arithmetic checkable without trusting the code that did it.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.claim_model import (
    Asserter, Citation, Claim, Fact, boolean_value, date_value,
    field_locator, quantity_value,
)
from src.normalization.dates import days_between, normalise_date

SYSTEM = Asserter(kind="system_record", name=None)


def _cite(claim: Claim, record: str, path: str, value: Any) -> Citation:
    doc_id, version = _record_document(claim, record)
    return Citation(document_id=doc_id, document_version=version,
                    locator=field_locator(record, path),
                    quoted_text=str(value))


def _record_document(claim: Claim, record: str):
    """Which document a structured record is attributed to.

    Structured records are still evidence and still need provenance: a fact
    read from the policy system must not be cited as if it came from the FNOL.
    """
    for doc in claim.documents:
        if doc.document_id == record:
            return doc.document_id, doc.version
    mapping = {
        "claim_record": "rec_claim",
        "policy_record": "rec_policy",
        "crash_record": "rec_crash",
        "vehicle_records": "rec_vehicles",
        "people_records": "rec_people",
        "anchor_record": "rec_anchor",
        "reserve_history": "rec_claim",
        "prior_claims": "rec_claim",
        "document_metadata": "rec_claim",
    }
    return mapping.get(record, record), "v1"


def read_structured_facts(claim: Claim) -> List[Fact]:
    """Facts read directly off structured records."""
    facts: List[Fact] = []
    n = _Counter("sf")
    cr = claim.claim_record

    facts.append(Fact(
        fact_id=n(), assertion="The reported date of loss is %s." % cr["loss_date"],
        asserter=SYSTEM, provenance="deterministic", subject="loss_date",
        normalised_value=normalise_date(cr["loss_date"]),
        citations=[_cite(claim, "claim_record", "loss_date", cr["loss_date"])]))

    if cr.get("reported_date"):
        facts.append(Fact(
            fact_id=n(),
            assertion="The loss was reported to the carrier on %s." % cr["reported_date"],
            asserter=SYSTEM, provenance="deterministic", subject="reported_date",
            normalised_value=normalise_date(cr["reported_date"]),
            citations=[_cite(claim, "claim_record", "reported_date", cr["reported_date"])]))

    if cr.get("loss_location"):
        facts.append(Fact(
            fact_id=n(), assertion="The loss location of record is %s." % cr["loss_location"],
            asserter=SYSTEM, provenance="deterministic", subject="loss_location",
            citations=[_cite(claim, "claim_record", "loss_location", cr["loss_location"])]))

    pol = claim.policy_record
    if pol:
        facts.append(Fact(
            fact_id=n(),
            assertion="The policy incepted on %s and expires on %s."
                      % (pol["inception_date"], pol["expiry_date"]),
            asserter=SYSTEM, provenance="deterministic", subject="policy_term",
            citations=[_cite(claim, "policy_record", "inception_date", pol["inception_date"]),
                       _cite(claim, "policy_record", "expiry_date", pol["expiry_date"])]))

    return facts


def read_anchor_facts(claim: Claim) -> List[Fact]:
    """Facts from structured source data supplied to anchor a synthetic scenario.

    Deterministic reads. No model ever sees this record.

    Three properties make this safe to surface next to a claimant's account:

    * Each fact is **attributed to the record**, exactly as a claimant's account
      is attributed to the claimant. The system asserts that the record codes a
      value; it does not assert the value is true. `data/schema.md` §1.5 —
      neutral framing, composed at the rendering layer.
    * Each fact **cites the supplier's own entry id**, so it traces back to the
      row it came from.
    * Nothing here is ranked above anything else. An anchor record and a
      recollection are two positions, and the difference stage is instructed
      not to adjudicate between them.
    """
    anchor = (claim.structured_records or {}).get("anchor") or {}
    facts: List[Fact] = []
    n = _Counter("an")
    for entry_id in sorted(anchor):
        entry = anchor[entry_id]
        field_name = entry.get("field")
        value = entry.get("value")
        if field_name is None or value is None:
            continue
        facts.append(Fact(
            fact_id=n(),
            assertion="The structured crash record codes %s as %s." % (field_name, value),
            asserter=SYSTEM, provenance="deterministic",
            subject="anchor:%s" % field_name,
            normalised_value=_anchor_normalised(field_name, value),
            citations=[Citation(document_id="rec_anchor", document_version="v1",
                                locator=field_locator("anchor_record", "%s.value" % entry_id),
                                quoted_text=str(value))]))
    return facts


def _anchor_normalised(field_name: str, value):
    """Only values whose type is unambiguous are normalised.

    A coded string is left as-is: guessing at its meaning is the model's job in
    no stage of this pipeline, and it is not code's job either.
    """
    if isinstance(value, str) and "T" in value and value[:4].isdigit():
        return normalise_date(value.split("T")[0])
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return quantity_value(value, field_name.lower())
    return None


def derive_facts(claim: Claim) -> List[Fact]:
    """Computed facts. Arithmetic is code, always (PRD §10.4)."""
    facts: List[Fact] = []
    n = _Counter("df")
    cr = claim.claim_record

    # Reporting delay — cites both operands.
    delay = None
    if cr.get("loss_date") and cr.get("reported_date"):
        try:
            delay = days_between(cr["loss_date"], cr["reported_date"])
        except ValueError:
            delay = None
    if delay is not None:
        facts.append(Fact(
            fact_id=n(),
            assertion="The loss was reported %d day%s after the reported date of loss."
                      % (delay, "" if delay == 1 else "s"),
            asserter=SYSTEM, provenance="deterministic", subject="reporting_delay_days",
            normalised_value=quantity_value(delay, "days"),
            citations=[_cite(claim, "claim_record", "loss_date", cr["loss_date"]),
                       _cite(claim, "claim_record", "reported_date", cr["reported_date"])]))

    pol = claim.policy_record
    if pol:
        try:
            age = days_between(pol["inception_date"], cr["loss_date"])
            facts.append(Fact(
                fact_id=n(),
                assertion="The policy had been in force %d days at the date of loss." % age,
                asserter=SYSTEM, provenance="deterministic", subject="policy_age_at_loss_days",
                normalised_value=quantity_value(age, "days"),
                citations=[_cite(claim, "policy_record", "inception_date", pol["inception_date"]),
                           _cite(claim, "claim_record", "loss_date", cr["loss_date"])]))
        except (ValueError, KeyError):
            pass

        in_force = _in_force(pol, cr["loss_date"])
        if in_force is not None:
            facts.append(Fact(
                fact_id=n(),
                assertion="The policy %s in force on the reported date of loss."
                          % ("was" if in_force else "was not"),
                asserter=SYSTEM, provenance="deterministic", subject="policy_in_force_at_loss",
                normalised_value=boolean_value(in_force),
                citations=[_cite(claim, "policy_record", "inception_date", pol["inception_date"]),
                           _cite(claim, "policy_record", "expiry_date", pol["expiry_date"]),
                           _cite(claim, "claim_record", "loss_date", cr["loss_date"])]))

    # Prior claim count.
    facts.append(Fact(
        fact_id=n(),
        assertion="The file records %d prior claim(s)." % len(claim.prior_claims),
        asserter=SYSTEM, provenance="deterministic", subject="prior_claim_count",
        normalised_value=quantity_value(len(claim.prior_claims), "claims"),
        citations=[_cite(claim, "claim_record", "claim_number", cr["claim_number"])]))

    # Handler count — the segment signal the product exists for (D-016).
    handlers = cr.get("handler_history", [])
    facts.append(Fact(
        fact_id=n(),
        assertion="The claim has been handled by %d handler(s)." % len(handlers),
        asserter=SYSTEM, provenance="deterministic", subject="handler_count",
        normalised_value=quantity_value(len(handlers), "handlers"),
        citations=[_cite(claim, "claim_record", "handler_history.0.handler",
                         handlers[0]["handler"] if handlers else "")]))

    return facts


def _in_force(policy: Dict[str, Any], loss_date: str) -> Optional[bool]:
    try:
        return (days_between(policy["inception_date"], loss_date) >= 0
                and days_between(loss_date, policy["expiry_date"]) >= 0)
    except (ValueError, KeyError):
        return None


def became_known_facts(claim: Claim) -> List[Fact]:
    """Facts about *when the file learned things* — the second timeline axis.

    This is what a chronology of the loss alone does not give a successor.
    Reserve changes in particular signal when the predecessor's view of
    severity shifted.
    """
    facts: List[Fact] = []
    n = _Counter("bk")
    for doc in claim.documents:
        if not doc.received_date:
            continue
        facts.append(Fact(
            fact_id=n(),
            assertion="%s was received into the file on %s."
                      % (_label(doc.type), doc.received_date),
            asserter=SYSTEM, provenance="deterministic",
            subject="document_received:%s" % doc.document_id,
            normalised_value=normalise_date(doc.received_date),
            citations=[Citation(document_id=doc.document_id,
                                document_version=doc.version,
                                locator=field_locator("document_metadata",
                                                      "%s.received_date" % doc.document_id),
                                quoted_text=doc.received_date)]))
    for i, r in enumerate(claim.reserve_history):
        facts.append(Fact(
            fact_id=n(),
            assertion="The reserve was set to %s on %s by %s."
                      % (r["amount"], r["set_at"], r["set_by"]),
            asserter=SYSTEM, provenance="deterministic",
            subject="reserve_change:%d" % i,
            normalised_value=normalise_date(r["set_at"]),
            citations=[_cite(claim, "reserve_history", "%d.amount" % i, r["amount"]),
                       _cite(claim, "reserve_history", "%d.set_at" % i, r["set_at"])]))
    return facts


def _label(doc_type: str) -> str:
    return {
        "fnol": "The FNOL",
        "recorded_statement": "The recorded statement",
        "independent_account": "The independent account",
        "police_report": "The police report",
        "repair_estimate": "The repair estimate",
        "adjuster_notes": "The adjuster notes",
        "correspondence": "Correspondence",
    }.get(doc_type, "Document %s" % doc_type)


class _Counter:
    def __init__(self, prefix: str) -> None:
        self.prefix, self.i = prefix, 0

    def __call__(self) -> str:
        self.i += 1
        return "%s_%03d" % (self.prefix, self.i)
