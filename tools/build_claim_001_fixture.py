"""Derive `data/fixtures/claim_001/` from the supplied source material.

Source (left untouched, at repo root):
    documents/01_fnol.md
    documents/02_recorded_statement.md
    structured/objective_anchor.json
    structured/claim_record.json
    structured/policy_record.json

This script exists rather than hand-written JSON for one reason: **character
offsets**. Gold spans index into passage text, and a hand-maintained fixture
drifts silently the first time a passage is edited. Deriving both from one place
makes the derivation reviewable and repeatable, and `tests/test_fixtures.py`
verifies every gold span still resolves.

Run:  ./.venv/bin/python tools/build_claim_001_fixture.py
"""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DOCS = os.path.join(ROOT, "documents")
SRC_STRUCT = os.path.join(ROOT, "structured")
OUT = os.path.join(ROOT, "data", "fixtures", "claim_001")

# Lines that are fixture scaffolding rather than claim content. Excluded from
# every passage.
#
# The second pattern matters more than it looks. `02_recorded_statement.md` ends
# with "Evaluation note: Compare these statements with the structured anchor ...
# do not treat them as authoritative merely because they appear in a recorded
# statement." That is an instruction to whoever grades the experiment. Feeding it
# to the extraction model would contaminate the run with guidance about how to
# weigh evidence — the model would be reading the answer key.
SCAFFOLD_PATTERNS = (
    re.compile(r"^\s*\*\*SYNTHETIC DOCUMENT.*", re.IGNORECASE),
    re.compile(r"^\s*\*\*Evaluation note:\*\*.*", re.IGNORECASE),
)

_BOLD = re.compile(r"\*\*(.+?)\*\*")

#: Anchor entries kept in the source export for provenance but deliberately NOT
#: carried into the E1 fact set.
#:
#: The supplied objective_anchor.json permits "crash geometry, timing, roadway,
#: vehicle, and crash-status attributes". A contributory-cause coding is none of
#: those — it is a causal determination, and pairing it against a claimant's
#: account produces a liability-adjacent comparison this experiment does not
#: need. HIT_AND_RUN_I is withheld on the project owner's instruction as a
#: separate semantic question to be tested later.
ANCHOR_EXCLUSIONS = {
    "A006": "Crash-status coding with intent-adjacent semantics. Deferred to a later "
            "experiment on the project owner's instruction; not an E1 fact.",
    "A007": "Contributory-cause coding is a causal/liability determination, outside the "
            "geometry/timing/roadway/vehicle/status categories the supplied anchor permits "
            "for E1. Excluded to keep difference detection off liability ground.",
}


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sections(markdown: str):
    """Split on `## ` headings. Returns {heading: [paragraph, ...]}."""
    out, current, buf = {}, None, []
    for line in markdown.split("\n"):
        if line.startswith("## "):
            if current is not None:
                out[current] = buf
            current, buf = line[3:].strip(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out[current] = buf
    return out


def prose(lines) -> str:
    """Narrative paragraphs only.

    Drops scaffolding lines, bullet list items (those become structured fields,
    not narrative — DOCMAP §2.1: an FNOL is ~100 fields around one or two free
    text boxes), and markdown emphasis markers. Emphasis is presentation; keeping
    the asterisks would put them inside quoted spans and make exact-span
    resolution depend on markup.
    """
    kept = []
    for line in lines:
        if any(p.match(line) for p in SCAFFOLD_PATTERNS):
            continue
        if line.strip().startswith(("- ", "* ", "|")):
            continue
        kept.append(_BOLD.sub(r"\1", line).rstrip())
    text = "\n".join(kept).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def bullets(lines):
    out = {}
    for line in lines:
        m = re.match(r"^\s*[-*]\s+(.+?):\s+(.+)$", _BOLD.sub(r"\1", line))
        if m:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def main() -> None:
    fnol_md = read(os.path.join(SRC_DOCS, "01_fnol.md"))
    stmt_md = read(os.path.join(SRC_DOCS, "02_recorded_statement.md"))
    anchor = load(os.path.join(SRC_STRUCT, "objective_anchor.json"))
    claim_src = load(os.path.join(SRC_STRUCT, "claim_record.json"))
    policy_src = load(os.path.join(SRC_STRUCT, "policy_record.json"))

    fnol_sec = sections(fnol_md)
    stmt_sec = sections(stmt_md)

    fnol_narrative = prose(fnol_sec["First Notice of Loss"])

    # The recorded statement has no `##` headings — its body is everything after
    # the Date/Speaker block, minus scaffolding.
    stmt_body_lines = []
    for line in stmt_md.split("\n"):
        if line.startswith("# ") or line.startswith("**Date:**") or line.startswith("**Speaker:**"):
            continue
        stmt_body_lines.append(line)
    stmt_body = prose(stmt_body_lines)

    claim_bullets = bullets(fnol_sec["Claim"])
    vehicle_bullets = bullets(fnol_sec["Vehicle"])

    anchor_by_id = {f["fact_id"]: {"field": f["field"], "value": f["value"]}
                    for f in anchor["facts"] if f["fact_id"] not in ANCHOR_EXCLUSIONS}
    excluded = [{"fact_id": f["fact_id"], "field": f["field"],
                 "reason": ANCHOR_EXCLUSIONS[f["fact_id"]]}
                for f in anchor["facts"] if f["fact_id"] in ANCHOR_EXCLUSIONS]

    # --- policy: map the supplied shape onto the repo schema -----------------
    # `listed_drivers` is a list of names in the repo schema and a list of refs
    # in the supplied record. The claimant is unnamed in both documents, which
    # call them "the claimant" throughout, so that is the name used. No VIN is
    # supplied and none is invented; the vehicle-scheduled check simply does not
    # run.
    policy_record = {
        "policy_id": policy_src["policy_id"],
        "policy_number": policy_src["policy_id"],
        "inception_date": policy_src["effective_at"].split("T")[0],
        "expiry_date": policy_src["expires_at"].split("T")[0],
        "listed_drivers": ["Claimant"] if policy_src["listed_drivers"][0]["listed"] else [],
        "scheduled_vehicles": [{
            "vin": None,
            "year": v["year"], "make": v["make"], "model": v["model"],
        } for v in policy_src["scheduled_vehicles"]],
        "coverages": [{"code": "COLL", "limit": "not_specified_in_fixture", "deductible": None}],
        "garaging_address": None,
        "lapse_history": [],
    }

    loss_date = claim_src["loss"]["occurred_at"].split("T")[0]

    claim = {
        "claim_id": "claim_001",
        "checkpoint": claim_src["checkpoint"],
        "provenance": {
            "fixture_kind": "real_anchor_synthetic_documents",
            "documents_are_synthetic": True,
            "disclaimer": (
                "HYBRID PROVENANCE. The structured anchor record holds fields transcribed from "
                "real Chicago crash data supplied by the project owner. Every narrative document "
                "is SYNTHETIC and is not a statement by any real crash participant. No "
                "person-level demographic attribute is carried into this fixture. Results "
                "measured against it record WHAT WE PLANTED (D-003); the real anchor makes the "
                "scenario physically plausible, it does not make the evaluation real-world "
                "evidence."
            ),
            "anchor": {
                "source_name": anchor["source_kind"],
                "source_url": None,
                "licence": None,
                "retrieved_at": None,
                "record_identifiers": {"claim_id": anchor["claim_id"]},
                "excluded_entries": excluded,
                "todo": (
                    "Source URL, licence, and retrieval date are deliberately null. The supplied "
                    "objective_anchor.json asserts none, and CLAUDE.md forbids inventing them. "
                    "Fill these in only from a verified source. "
                    "USAGE CONSTRAINT (carried from the supplied file): use only crash geometry, "
                    "timing, roadway, vehicle, and crash-status attributes. Do not attach "
                    "synthetic narrative statements to real crash participants."
                ),
            },
        },
        "claim_record": {
            "claim_number": claim_src["claim_id"],
            "policy_id": policy_src["policy_id"],
            "loss_date": loss_date,
            # The supplied material carries no report date, so none is asserted.
            # Reporting delay and report-date chronology are consequently NOT
            # computed, and the output says so in `not_assessed` rather than
            # implying there was no delay.
            "reported_date": None,
            "loss_location": claim_src["loss"]["location"],
            "claim_type": "auto_collision",
            "status": "open_investigating",
            "jurisdiction": None,
            "handler_history": [{"handler": "Handler A", "from": "2026-08-11", "to": None}],
            "parties": [
                {"party_id": "p_001", "name_as_written": "Claimant", "role": "claimant"},
                {"party_id": "p_002", "name_as_written": "Claimant", "role": "driver"},
            ],
        },
        "policy_record": policy_record,
        "structured_records": {"anchor": anchor_by_id, "crash": None,
                               "vehicles": [], "people": []},
        "documents": ["documents/fnol.json", "documents/recorded_statement.json"],
        "prior_claims": [],
        "reserve_history": [],
    }

    fnol_doc = {
        "document_id": "doc_fnol",
        "type": "fnol",
        "version": "v1",
        # Unrecorded in the supplied material. The FNOL therefore contributes no
        # "became known" event; a date is not invented to fill the axis.
        "received_date": None,
        "checkpoint_available": "C1",
        "structure_class": "structured_with_narrative",
        "structured_fields": {
            "claim_id": claim_bullets.get("Claim ID"),
            "loss_date": claim_bullets.get("Loss date"),
            "loss_time_approximate": claim_bullets.get("Approximate loss time"),
            "loss_location": claim_bullets.get("Loss location"),
            "reported_damage_band": claim_bullets.get("Reported damage"),
            "injury_reported": claim_bullets.get("Injury reported"),
            "claimant_vehicle": vehicle_bullets.get("Claimant vehicle"),
            "vehicle_use": vehicle_bullets.get("Use"),
            "vehicle_maneuver": vehicle_bullets.get("Maneuver"),
            "driver_name": "Claimant",
        },
        # ONE passage. The document's "Not established" section is meta language
        # about the form itself, not the claimant's account, and E1 tests
        # extraction from claimant narrative.
        "passages": [
            {"passage_id": "fnol.description_of_accident",
             "label": "First Notice of Loss narrative",
             "text": fnol_narrative},
        ],
    }

    stmt_doc = {
        "document_id": "doc_statement",
        "type": "recorded_statement",
        "version": "v1",
        "received_date": "2026-08-13",
        "checkpoint_available": "C3",
        "structure_class": "unstructured",
        "structured_fields": {"statement_date": "2026-08-13",
                              "speaker": "Claimant (synthetic)"},
        "passages": [
            {"passage_id": "statement.body",
             "label": "Recorded statement of the claimant",
             "text": stmt_body},
        ],
    }

    os.makedirs(os.path.join(OUT, "documents"), exist_ok=True)
    with open(os.path.join(OUT, "claim.json"), "w", encoding="utf-8") as fh:
        json.dump(claim, fh, indent=2)
    for name, doc in (("fnol", fnol_doc), ("recorded_statement", stmt_doc)):
        with open(os.path.join(OUT, "documents", name + ".json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)

    print("wrote %s" % os.path.relpath(OUT, ROOT))
    for pid, text in (("fnol.description_of_accident", fnol_narrative),
                      ("statement.body", stmt_body)):
        print("  %-32s %4d chars" % (pid, len(text)))


if __name__ == "__main__":
    main()
