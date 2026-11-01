"""Stage 10 — ASSEMBLE.

Where the output object is built and where the invariants are enforced rather
than assumed. `assert_invariants` is called on every result before it leaves
this module; a violation raises. The alternative — logging a warning — produces
a result that looks fine and is not.

The header is built from a TEMPLATE, not a model. PRD §10.3 says to try the
template first, and D-025 cut the narrative summary precisely because a
structured, individually-cited header has no long generation for hallucinations
to cluster at the end of, and no room for the generic-vacuity failure.
"""
from __future__ import annotations

import datetime
import hashlib
from typing import Any, Dict, List, Optional

from src.claim_model import (Claim, ClaimHeader, Difference, Fact, HeaderField,
                             OpenQuestion, SynthesisResult, TimelineEvent)
from src.ingestion.loader import documents_available_at

#: Always present. An empty `differences` list is otherwise ambiguous between
#: "no differences found" and "differences not assessed" (D-020 P5).
BASELINE_NOT_ASSESSED = [
    "materiality — not assessed by design (PRD §7.4, gated on D-014). "
    "The system surfaces differences; a human decides which matter.",
    "credibility, fault, liability, coverage, and suspicion — out of scope for V1.",
    "photographs and scene diagrams — presence noted, content not read.",
]


class InvariantViolation(RuntimeError):
    pass


def assemble(claim: Claim, facts: List[Fact], timeline: List[TimelineEvent],
             differences: List[Difference], open_questions: List[OpenQuestion],
             model_id: Optional[str], prompt_version: Optional[str],
             dropped: List[Dict[str, Any]],
             passages_total: int, passages_processed: int,
             extra_not_assessed: Optional[List[str]] = None) -> SynthesisResult:

    available = documents_available_at(claim)
    withheld = len(claim.documents) - len(available)

    not_assessed = list(BASELINE_NOT_ASSESSED)
    if extra_not_assessed:
        not_assessed.extend(extra_not_assessed)
    if withheld:
        not_assessed.append(
            "%d document(s) withheld: not yet available at checkpoint %s (D-004)."
            % (withheld, claim.checkpoint))
    if not claim.claim_record.get("reported_date"):
        not_assessed.append(
            "reporting delay and report-date chronology — not computed: the claim record "
            "does not state a report date.")
    undated = [d.document_id for d in available if not d.received_date]
    if undated:
        not_assessed.append(
            "arrival date of %s — not recorded in the file, so %s contributes no "
            "'became known' timeline event."
            % (", ".join(undated), "it" if len(undated) == 1 else "they"))
    if model_id is None:
        not_assessed.append(
            "narrative extraction and difference proposal — no model was run "
            "(deterministic-only mode).")
    result = SynthesisResult(
        synthesis_id=_synthesis_id(claim, available),
        claim_id=claim.claim_id,
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        checkpoint=claim.checkpoint,
        document_set=[{"document_id": d.document_id, "version": d.version, "type": d.type}
                      for d in available],
        model_id=model_id,
        prompt_version=prompt_version,
        header=build_header(claim, facts),
        timeline=timeline,
        facts=facts,
        differences=differences,
        open_questions=open_questions,
        coverage={
            "documents_total": len(claim.documents),
            "documents_processed": len(available),
            "documents_withheld_by_checkpoint": withheld,
            "passages_total": passages_total,
            "passages_processed": passages_processed,
            "facts_dropped": len(dropped),
        },
        not_assessed=not_assessed,
    )
    assert_invariants(result)
    return result


def build_header(claim: Claim, facts: List[Fact]) -> ClaimHeader:
    """Six fields, each individually cited and individually falsifiable.

    `state` has three values, not two: "absent from the file" and "we did not
    look" are different things and must be distinguishable.
    """
    by_subject: Dict[str, List[Fact]] = {}
    for f in facts:
        if f.subject:
            by_subject.setdefault(f.subject, []).append(f)

    def from_subjects(subjects, render) -> HeaderField:
        found = [f for s in subjects for f in by_subject.get(s, [])]
        if not found:
            return HeaderField(value=None, state="absent_from_file", fact_ids=[])
        return HeaderField(value=render(found), state="present",
                           fact_ids=[f.fact_id for f in found])

    coverage = from_subjects(
        ["policy_term", "policy_in_force_at_loss"],
        lambda fs: "; ".join(f.assertion for f in fs))

    loss_description = from_subjects(
        ["loss_date", "loss_location"],
        lambda fs: "; ".join(f.assertion for f in fs))

    jurisdiction_value = claim.claim_record.get("jurisdiction")
    if jurisdiction_value:
        jurisdiction = HeaderField(value=jurisdiction_value, state="present", fact_ids=[])
    else:
        jurisdiction = HeaderField(value=None, state="absent_from_file", fact_ids=[])

    # Damages needs a repair estimate or equivalent. At C3 there usually is
    # none, and saying so is the output.
    damages = from_subjects(["damages_total", "estimate_total"],
                            lambda fs: "; ".join(f.assertion for f in fs))

    status = HeaderField(value=claim.claim_record.get("status"), state="present", fact_ids=[]) \
        if claim.claim_record.get("status") else HeaderField(None, "absent_from_file", [])

    if claim.reserve_history:
        latest = claim.reserve_history[-1]
        reserve = HeaderField(
            value="%s as at %s" % (latest["amount"], latest["set_at"]),
            state="present",
            fact_ids=[f.fact_id for f in facts
                      if (f.subject or "").startswith("reserve_change:")])
    else:
        reserve = HeaderField(value=None, state="absent_from_file", fact_ids=[])

    return ClaimHeader(coverage=coverage, loss_description=loss_description,
                       jurisdiction=jurisdiction, damages=damages,
                       status=status, reserve=reserve)


def assert_invariants(result: SynthesisResult) -> None:
    """The safety properties, checked. Each maps to a decision."""
    d = result.to_dict()

    # D-020 P2 — nothing uncitable reaches the output.
    for f in d["facts"]:
        if not f["citations"]:
            raise InvariantViolation("fact %s has no citations" % f["fact_id"])
        for c in f["citations"]:
            if not c["resolved"]:
                raise InvariantViolation(
                    "fact %s carries an unresolved citation (%s). Unresolved facts "
                    "are DROPPED, never emitted." % (f["fact_id"], c["resolution_note"]))

    # PROVISIONAL — GATED ON D-014. V1 never asserts materiality.
    for diff in d["differences"]:
        if diff.get("materiality") is not None or diff.get("materiality_rationale") is not None:
            raise InvariantViolation(
                "difference %s carries a materiality value. V1 must never assert "
                "materiality (PRD §7.4)." % diff["difference_id"])
        if len(diff["positions"]) < 2:
            raise InvariantViolation(
                "difference %s has fewer than two positions" % diff["difference_id"])

    # D-020 P5 — absence stated, not implied.
    if not d["not_assessed"]:
        raise InvariantViolation(
            "not_assessed is empty. An empty differences list would then be "
            "ambiguous between 'none found' and 'not assessed'.")

    # D-020 P6 — the output records what the system actually saw.
    if not d["document_set"]:
        raise InvariantViolation("document_set is empty; the run is unauditable")

    # Every position must point at a fact that survived the drop rule.
    fact_ids = {f["fact_id"] for f in d["facts"]}
    for diff in d["differences"]:
        for p in diff["positions"]:
            if p["fact_id"] not in fact_ids:
                raise InvariantViolation(
                    "difference %s cites fact %s, which is not in the output. A "
                    "difference between dropped facts is unverifiable."
                    % (diff["difference_id"], p["fact_id"]))

    # Timeline events must trace to surviving facts.
    for ev in d["timeline"]:
        for fid in ev["source_fact_ids"]:
            if fid not in fact_ids:
                raise InvariantViolation(
                    "timeline event %s cites missing fact %s" % (ev["event_id"], fid))


def _synthesis_id(claim: Claim, documents) -> str:
    """Stable across identical document sets, so two runs over the same file
    are comparable and a changed file is visibly a different synthesis."""
    key = claim.claim_id + "|" + "|".join(
        sorted("%s@%s" % (d.document_id, d.version) for d in documents))
    return "syn_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
