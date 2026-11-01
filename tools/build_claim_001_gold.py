"""Author the Claim 001 gold answer and a clean mock recording.

Spans are computed from the built fixture, never typed by hand, so gold cannot
drift from passage text. `tests/test_fixtures.py` re-verifies every span.

Run AFTER tools/build_claim_001_fixture.py.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.ingestion.loader import load_claim          # noqa: E402
from src.pipeline import run_pipeline                # noqa: E402

FIXTURE = os.path.join(ROOT, "data", "fixtures", "claim_001")
GOLD = os.path.join(ROOT, "data", "gold", "claim_001.gold.json")
REC = os.path.join(ROOT, "src", "llm", "recordings", "claim_001")

DISCLAIMER = (
    "These labels record WHAT WE PLANTED. They are not evidence of real-world performance "
    "(D-003). Narrative documents are synthetic; the structured anchor holds fields "
    "transcribed from a real crash record and is treated as a SOURCE THAT ASSERTS THINGS, "
    "not as ground truth about the loss. The `expected_facts` list for extracted facts is an "
    "AUTHORED judgement about what a correct extraction contains — reasonable people would "
    "draw the boundary differently, particularly on the two enumerating sentences noted below, "
    "so fact recall and precision are indicative rather than absolute (D-034). "
    "`materiality_intent` is null throughout: E1 does not assess materiality and the runner "
    "cannot score it (D-033). Two anchor entries (A006 HIT_AND_RUN_I, A007 "
    "PRIM_CONTRIBUTORY_CAUSE) are deliberately excluded from this fixture's fact set and are "
    "recorded under provenance.anchor.excluded_entries."
)

claim = load_claim(os.path.join(FIXTURE, "claim.json"))
P = {p.passage_id: p.text for p in
     [claim.passage(i) for i in ("fnol.description_of_accident", "statement.body")]}


def span(passage_id, quote):
    text = P[passage_id]
    i = text.index(quote)
    return {"char_start": i, "char_end": i + len(quote), "quoted_text": quote}


def ext(key, assertion, subject, passage_id, quote, doc, raw_time=None,
        asserter_kind="claimant"):
    normalised = None
    if raw_time:
        normalised = {"Date": {"value": None, "precision": "vague",
                               "raw_expression": raw_time}}
    return {"match_key": key, "assertion": assertion, "subject": subject,
            "asserter_kind": asserter_kind, "asserter_name": None,
            "provenance": "extracted", "document_id": doc,
            "passage_id": passage_id, "span": span(passage_id, quote),
            "field_path": None, "normalised_value": normalised,
            "materiality_intent": None,
            "_raw_time": raw_time}


# --- deterministic facts: taken from the pipeline's own null-client output ---
# Authoring these by hand would duplicate the implementation and drift from it.
# They are regression coverage, not aindependent restatement of the arithmetic.
det_run = run_pipeline(claim)
deterministic = []
for f in det_run.result.facts:
    loc = f.citations[0].locator
    field_path = loc.get("Field", {}).get("field_path")
    deterministic.append({
        "match_key": "det.%s" % f.subject,
        "assertion": f.assertion,
        "subject": f.subject,
        "asserter_kind": f.asserter.kind,
        "asserter_name": f.asserter.name,
        "provenance": "deterministic",
        "document_id": f.citations[0].document_id,
        "passage_id": None,
        "span": None,
        "field_path": field_path,
        "normalised_value": f.normalised_value,
        "materiality_intent": None,
    })

# --- extracted facts: authored -------------------------------------------
F = "fnol.description_of_accident"
S = "statement.body"

extracted = [
    # FNOL narrative
    ext("fnol.direction", "The claimant reports the vehicle was travelling northbound on Karlov Avenue.",
        "direction_of_travel", F, "their vehicle was traveling northbound on Karlov Avenue", "doc_fnol"),
    ext("fnol.night", "The claimant reports the loss occurred at night.",
        "time_of_day", F, "at night", "doc_fnol", raw_time="at night"),
    ext("fnol.road_wet", "The claimant says the road was wet.",
        "road_surface", F, "the road was wet", "doc_fnol"),
    ext("fnol.visibility", "The claimant says visibility was limited by darkness although the roadway was illuminated.",
        "visibility", F, "visibility was limited by darkness, although the roadway was illuminated", "doc_fnol"),
    ext("fnol.maneuver", "The claimant reports the vehicle was turning right at the time of contact.",
        "vehicle_maneuver", F, "the vehicle was turning right", "doc_fnol"),
    ext("fnol.contact_object", "The claimant reports the vehicle came into contact with a parked vehicle.",
        "contact_object", F, "came into contact with a parked vehicle", "doc_fnol"),
    ext("fnol.awareness", "The claimant says they did not initially realise how significant the contact was.",
        "claimant_awareness_of_severity", F,
        "they did not initially realize how significant the contact was", "doc_fnol"),
    ext("fnol.actions", "The claimant states they stopped briefly, looked at the vehicles, and then left.",
        "post_collision_actions", F,
        "they stopped briefly, looked at the vehicles, and then left", "doc_fnol"),
    ext("fnol.reason_left", "The claimant states they left because they were concerned about being stranded late at night.",
        "reason_for_leaving", F,
        "because they were concerned about being stranded late at night", "doc_fnol"),
    ext("fnol.no_one_seen", "The claimant says they did not see anyone inside the parked vehicle.",
        "occupancy_observation", F,
        "they did not see anyone inside the parked vehicle", "doc_fnol"),
    ext("fnol.injury_belief", "The claimant says they did not believe anyone was injured.",
        "injury_belief", F, "did not believe anyone was injured", "doc_fnol"),

    # Recorded statement
    ext("stmt.direction", "The claimant says they were driving southbound.",
        "direction_of_travel", S, "southbound", "doc_statement"),
    ext("stmt.vehicle", "The claimant says they were driving the Mercedes-Benz G-Class.",
        "vehicle_identity", S, "driving the Mercedes-Benz G-Class", "doc_statement"),
    ext("stmt.maneuver", "The claimant says they were making a right turn.",
        "vehicle_maneuver", S, "making a right turn", "doc_statement"),
    ext("stmt.time", "The claimant says the loss occurred at approximately 9:40 PM.",
        "time_of_loss", S, "at approximately 9:40 PM", "doc_statement",
        raw_time="approximately 9:40 PM"),
    ext("stmt.rain", "The claimant recalls that it had been raining earlier.",
        "weather_before_loss", S, "it had been raining earlier", "doc_statement"),
    ext("stmt.pavement_wet", "The claimant recalls that the pavement was wet.",
        "road_surface", S, "the pavement was wet", "doc_statement"),
    ext("stmt.speed", "The claimant says they were driving around 25 to 30 mph before beginning the turn.",
        "speed_before_turn", S,
        "they were driving \"around 25 to 30 mph\" before beginning the turn", "doc_statement"),
    ext("stmt.slid", "The claimant says the turn was normal until the vehicle suddenly slid.",
        "vehicle_slid", S, "the turn was normal until the vehicle suddenly slid", "doc_statement"),
    ext("stmt.correction", "The claimant says they tried to correct the vehicle.",
        "correction_attempt", S, "they tried to correct the vehicle", "doc_statement"),
    ext("stmt.contact", "The claimant says the front of the Mercedes contacted a parked SUV.",
        "contact_configuration", S,
        "the front of the Mercedes contacted a parked SUV", "doc_statement"),
    ext("stmt.no_one_seen", "The claimant says they did not see anyone inside the parked SUV.",
        "occupancy_observation", S,
        "they did not see anyone inside the parked SUV", "doc_statement"),
    ext("stmt.injury_belief", "The claimant says they did not believe anyone was injured.",
        "injury_belief", S, "did not believe anyone was injured", "doc_statement"),
    ext("stmt.actions", "The claimant says they stopped after the collision, looked at the vehicles, and then left.",
        "post_collision_actions", S,
        "they stopped after the collision, looked at the vehicles, and then left", "doc_statement"),
    ext("stmt.reason_left", "The claimant says they left because they were concerned about being stranded late at night.",
        "reason_for_leaving", S,
        "because they were concerned about being stranded late at night", "doc_statement"),
    ext("stmt.intent_to_report", "The claimant says they intended to report the incident.",
        "reporting_intention", S, "they intended to report the incident", "doc_statement"),
    ext("stmt.non_recall", "The claimant says they do not recall the exact distance travelled, whether traction control activated, whether another vehicle was nearby, whether there was a witness, or the exact impact location.",
        "claimant_non_recall", S,
        "The claimant does not recall the exact distance traveled, whether traction control activated, whether another vehicle was nearby, whether there was a witness, or the exact impact location",
        "doc_statement"),
]

gold = {
    "claim_id": "claim_001",
    "checkpoint": "C3",
    "disclaimer": DISCLAIMER,
    "is_zero_conflict_control": False,
    "expected_facts": deterministic + [{k: v for k, v in f.items() if k != "_raw_time"}
                                       for f in extracted],
    "facts_must_not_appear": [
        {"match_key": "must_not.vehicle_was_empty",
         "assertion": "The parked vehicle was unoccupied.",
         "why_absent": "STRENGTHENING. Both documents say only that the claimant did not SEE "
                       "anyone inside. A failure to observe is not an absence."},
        {"match_key": "must_not.nobody_injured",
         "assertion": "The claimant asserted that nobody was injured.",
         "why_absent": "STRENGTHENING. The claimant states a belief — 'did not believe anyone "
                       "was injured'. A belief is not a fact. (The anchor record separately "
                       "codes no indication of injury; that is a different asserter.)"},
        {"match_key": "must_not.did_report",
         "assertion": "The claimant reported the incident as they had intended.",
         "why_absent": "STRENGTHENING. The statement records an intention, not an act."},
        {"match_key": "must_not.fnol_says_slid",
         "assertion": "The FNOL reports that the vehicle slid during the turn.",
         "why_absent": "The FNOL narrative does not mention a slide at all. Only the recorded "
                       "statement asserts one. Attributing it to the FNOL would manufacture "
                       "agreement where the FNOL is simply silent."},
        {"match_key": "must_not.no_other_vehicle",
         "assertion": "No other vehicle was nearby at the time of the collision.",
         "why_absent": "The claimant does not RECALL whether another vehicle was nearby. "
                       "Non-recall is not negation."},
        {"match_key": "must_not.speeding",
         "assertion": "The claimant was driving too fast for the conditions.",
         "why_absent": "INFERENCE. No source in this fixture asserts it. The contributory-cause "
                       "coding was deliberately excluded from the anchor, so nothing licenses "
                       "even a restatement."},
        {"match_key": "must_not.fled",
         "assertion": "The claimant left the scene in order to avoid responsibility.",
         "why_absent": "MOTIVE. The stated reason is concern about being stranded. Substituting "
                       "a different motive is exactly the inference forbidden throughout."},
        {"match_key": "must_not.inconsistent",
         "assertion": "The claimant's account is inconsistent with the official crash record.",
         "why_absent": "CONCLUSION, not a fact, and it adjudicates between sources. Differences "
                       "are surfaced as positions; no stage decides which source is correct."},
        {"match_key": "must_not.fnol_southbound",
         "assertion": "The FNOL records the vehicle as travelling southbound.",
         "why_absent": "CROSS-CONTAMINATION. The FNOL says northbound; the statement says "
                       "southbound. Attributing one document's content to the other destroys the "
                       "only planted difference in this fixture."},
    ],
    "expected_timeline": [
        {"axis": "occurred", "label": "reported date of loss", "order": 1,
         "when": "2026-08-11", "must_remain_vague": False,
         "source_match_keys": ["det.loss_date"]},
        {"axis": "occurred", "label": "crash record CRASH_DATE", "order": 1,
         "when": "2026-08-11", "must_remain_vague": False,
         "source_match_keys": ["det.anchor:CRASH_DATE"]},
        {"axis": "occurred", "label": "at night (FNOL)", "order": 99, "when": None,
         "must_remain_vague": True, "source_match_keys": ["fnol.night"]},
        {"axis": "occurred", "label": "approximately 9:40 PM (statement)", "order": 99,
         "when": None, "must_remain_vague": True, "source_match_keys": ["stmt.time"]},
        # The only became_known event: the statement's own stated date. No report
        # date and no FNOL arrival date exist in the file, and neither is invented.
        {"axis": "became_known", "label": "recorded statement received", "order": 1,
         "when": "2026-08-13", "must_remain_vague": False,
         "source_match_keys": ["det.document_received:doc_statement"]},
    ],
    "planted_differences": [
        {"difference_id": "gold_d_001",
         "subject": "direction_of_travel",
         "position_match_keys": ["fnol.direction", "stmt.direction"],
         "detection_method": "extracted",
         "conflict_pair": 1,
         "materiality_intent": None},
    ],
    "differences_must_not_be_reported": [
        {"subject": "time_of_loss",
         "why_not": "COMPATIBLE APPROXIMATION. The FNOL field records 9:43 PM; the statement "
                    "says 'approximately 9:40 PM'. One state of affairs satisfies both."},
        {"subject": "vehicle_slid",
         "why_not": "MISSING CORROBORATION, NOT CONTRADICTION. The statement asserts a slide; "
                    "the FNOL narrative simply does not mention one. Silence is not a position."},
        {"subject": "speed_before_turn_vs_posted_limit",
         "why_not": "DIFFERENT PROPERTIES. 'Around 25 to 30 mph' is an actual speed; the anchor's "
                    "POSTED_SPEED_LIMIT of 30 is a road attribute. They are not two accounts of "
                    "the same thing, and 25-30 does not exceed 30 in any case."},

        {"subject": "contact_point",
         "why_not": "DIFFERENT VEHICLES. The statement gives the contact point on the claimant's "
                    "vehicle (its front); the anchor gives UNIT_2_FIRST_CONTACT_POINT on the "
                    "parked vehicle (rear-right-corner). A front striking a rear corner is one "
                    "configuration, not two claims."},
        {"subject": "road_surface",
         "why_not": "AGREEMENT. FNOL, statement, and anchor all record a wet surface."},
        {"subject": "claimant_non_recall",
         "why_not": "NON-RECALL TAKES NO POSITION. A stated inability to recall cannot conflict "
                    "with a source that asserts something."},
        {"subject": "vehicle_maneuver",
         "why_not": "AGREEMENT. FNOL 'turning right', statement 'making a right turn', anchor "
                    "UNIT_1_MANEUVER 'TURNING RIGHT'. Three sources, one position."},
    ],
    "expected_open_questions": [
        {"match_key": "oq.independent_account", "kind": "expected_document_absent",
         "question": "The file does not contain an independent account of the loss.",
         "expected_source": "an independent account of the loss"},
        {"match_key": "oq.adjuster_notes", "kind": "expected_document_absent",
         "question": "The file does not contain adjuster notes.",
         "expected_source": "adjuster notes"},
    ],
}

with open(GOLD, "w", encoding="utf-8") as fh:
    json.dump(gold, fh, indent=2)

# --- clean mock recording -------------------------------------------------
# Hand-constructed "ideal" responses. Used only to exercise the plumbing and to
# show, in the preflight, the behaviour the prompts are asking for. NOT model
# output, and never an E1 result.
by_passage = {}
for f in extracted:
    by_passage.setdefault(f["passage_id"], []).append(f)

os.makedirs(REC, exist_ok=True)
order, idx, key_to_id = [F, S], 0, {}
for pid in order:
    items = []
    for f in by_passage.get(pid, []):
        idx += 1
        key_to_id[f["match_key"]] = "ex_%03d" % idx
        items.append({
            "assertion": f["assertion"],
            "asserter_kind": f["asserter_kind"],
            "asserter_name": f["asserter_name"],
            "subject": f["subject"],
            "quoted_text": f["span"]["quoted_text"],
            "char_start": f["span"]["char_start"],
            "char_end": f["span"]["char_end"],
            "raw_time_expression": f.get("_raw_time"),
            "revised": None,
            "superseded_text": None,
        })
    with open(os.path.join(REC, "extract__%s.json" % pid), "w", encoding="utf-8") as fh:
        json.dump({"facts": items}, fh, indent=2)

diffs = [{
    "subject": "direction_of_travel",
    "positions": [
        {"fact_id": key_to_id["fnol.direction"],
         "stance": "The FNOL records the vehicle as travelling northbound on Karlov Avenue."},
        {"fact_id": key_to_id["stmt.direction"],
         "stance": "The recorded statement has the claimant driving southbound."},
    ],
}]
with open(os.path.join(REC, "differences.json"), "w", encoding="utf-8") as fh:
    json.dump({"differences": diffs}, fh, indent=2)

print("gold: %d deterministic + %d extracted = %d expected facts"
      % (len(deterministic), len(extracted), len(gold["expected_facts"])))
print("recording: %d passages, %d difference(s)" % (len(order), len(diffs)))
