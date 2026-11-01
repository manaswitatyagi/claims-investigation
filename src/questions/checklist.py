"""Stage 9 — IDENTIFY OPEN QUESTIONS.

Deterministic, and that is the point (D-026). This is the lowest-risk, cheapest
high-value output in the product, and the hedge if assumption A1 turns out to be
wrong — if adjusters lose more time chasing what they do not have than reading
what they do, this module is the product and the rest is supporting context.

Two kinds are computed here:
  expected_document_absent  — a checklist against the claim type
  requested_never_received  — DOCMAP pair 8: a request in correspondence with
                              no matching arrival

Note D-032 remains open: a checklist is trivially correct and may be trivially
useless, because an adjuster who has read the file already knows the police
report never arrived. Correctness is measurable here; usefulness needs a
practitioner, and PRD §12.2 scores it as a human-rated metric rather than
pretending this module can answer it.
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.claim_model import Citation, Claim, OpenQuestion, text_span
from src.ingestion.loader import CHECKPOINT_ORDER

#: Documents expected for a claim type, and the earliest checkpoint by which
#: their absence is worth remarking on.
EXPECTED_DOCUMENTS: Dict[str, List[Dict[str, str]]] = {
    "auto_collision": [
        {"type": "fnol", "from": "C1", "label": "an FNOL"},
        {"type": "policy_record", "from": "C2", "label": "a policy record"},
        {"type": "recorded_statement", "from": "C3", "label": "a recorded statement"},
        {"type": "independent_account", "from": "C3",
         "label": "an independent account of the loss",
         "alt": "police_report"},
        {"type": "adjuster_notes", "from": "C3", "label": "adjuster notes"},
        {"type": "repair_estimate", "from": "C4", "label": "a repair estimate"},
    ],
}


def build_open_questions(claim: Claim) -> List[OpenQuestion]:
    questions: List[OpenQuestion] = []
    n = _Counter("oq")
    questions.extend(_missing_documents(claim, n))
    questions.extend(_unanswered_requests(claim, n))
    return questions


def _missing_documents(claim: Claim, n) -> List[OpenQuestion]:
    expected = EXPECTED_DOCUMENTS.get(claim.claim_record.get("claim_type", ""), [])
    if not expected:
        return []
    limit = CHECKPOINT_ORDER[claim.checkpoint]
    present = {d.type for d in claim.documents}
    # The policy record may arrive as a structured record rather than a document.
    if claim.policy_record:
        present.add("policy_record")

    out = []
    for item in expected:
        if CHECKPOINT_ORDER[item["from"]] > limit:
            continue                      # not yet expected at this checkpoint
        if item["type"] in present:
            continue
        if item.get("alt") and item["alt"] in present:
            continue
        out.append(OpenQuestion(
            question_id=n(),
            question="The file does not contain %s. Has it been requested or received?"
                     % item["label"],
            kind="expected_document_absent",
            provenance="deterministic",
            expected_source=item["label"],
            # Nothing to cite: the document is absent. This is exactly why
            # OpenQuestion is not a Fact with a status (D-027).
            supporting_citations=[],
        ))
    return out


def _unanswered_requests(claim: Claim, n) -> List[OpenQuestion]:
    """DOCMAP pair 8. Date arithmetic over correspondence, not a model.

    A request is matched to an arrival by the item it names. An unmatched
    request becomes a question and cites the correspondence that made it — the
    one OpenQuestion kind that CAN be cited.
    """
    out = []
    received_types = {d.type for d in claim.documents}
    for doc in claim.documents:
        if doc.type != "correspondence":
            continue
        for req in (doc.structured_fields or {}).get("requests", []) or []:
            item_type = req.get("item_type")
            if item_type and item_type in received_types:
                continue
            citations = []
            span = req.get("span")
            if span and doc.passages:
                citations.append(Citation(
                    document_id=doc.document_id, document_version=doc.version,
                    locator=text_span(doc.passages[0].passage_id,
                                      span["char_start"], span["char_end"]),
                    quoted_text=span["quoted_text"]))
            out.append(OpenQuestion(
                question_id=n(),
                question="%s was requested on %s and no matching item has arrived."
                         % (req.get("item_label", item_type or "An item"),
                            req.get("requested_on", "an unrecorded date")),
                kind="requested_never_received",
                provenance="deterministic",
                expected_source=req.get("item_label") or item_type,
                supporting_citations=citations))
    return out


class _Counter:
    def __init__(self, prefix: str) -> None:
        self.prefix, self.i = prefix, 0

    def __call__(self) -> str:
        self.i += 1
        return "%s_%03d" % (self.prefix, self.i)
