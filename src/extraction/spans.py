"""Stage 5 — RESOLVE. The gate.

D-020 P2: **drop, never soften.** A fact whose span cannot be located is
discarded, not hedged. Hedged-but-present content is worse than absent content
because it looks verified.

`resolved: false` exists only so the drop is auditable. It never reaches a
`SynthesisResult`.

Resolution is *exact*. PRD §12.2: "anything that does not resolve exactly is
dropped". The `resolution_note` still distinguishes offset drift (the text is
present, the offsets are wrong) from absence (the text is not in the passage at
all) — the first is a model that can nearly cite, the second is a model that
fabricated. Both are dropped; only the diagnosis differs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.claim_model import Citation, Claim, Fact


def build_record_index(claim: Claim) -> Dict[str, Any]:
    """Addressable structured records, for `Field` locators."""
    index: Dict[str, Any] = {"claim_record": claim.claim_record}
    if claim.policy_record:
        index["policy_record"] = claim.policy_record
    sr = claim.structured_records or {}
    if sr.get("anchor"):
        index["anchor_record"] = sr["anchor"]
    if sr.get("crash"):
        index["crash_record"] = sr["crash"]
    if sr.get("vehicles"):
        index["vehicle_records"] = sr["vehicles"]
    if sr.get("people"):
        index["people_records"] = sr["people"]
    if claim.prior_claims:
        index["prior_claims"] = claim.prior_claims
    if claim.reserve_history:
        index["reserve_history"] = claim.reserve_history
    # Document metadata is citable too: "when did this arrive" is a fact about
    # the file, and the became_known timeline axis is built from it.
    index["document_metadata"] = {
        doc.document_id: {"type": doc.type, "version": doc.version,
                          "received_date": doc.received_date,
                          "checkpoint_available": doc.checkpoint_available}
        for doc in claim.documents
    }
    for doc in claim.documents:
        if doc.structured_fields:
            index[doc.document_id] = doc.structured_fields
    return index


def _walk(node: Any, path: str) -> Tuple[bool, Any]:
    cur = node
    for part in path.split("."):
        if isinstance(cur, list):
            if not part.isdigit() or int(part) >= len(cur):
                return False, None
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                return False, None
            cur = cur[part]
        else:
            return False, None
    return True, cur


def resolve_citation(citation: Citation, claim: Claim,
                     record_index: Dict[str, Any]) -> Citation:
    loc = citation.locator

    if "TextSpan" in loc:
        ts = loc["TextSpan"]
        passage = claim.passage(ts["passage_id"])
        if passage is None:
            citation.resolved = False
            citation.resolution_note = "passage_not_found"
            return citation
        start, end = ts["char_start"], ts["char_end"]
        if not (0 <= start <= end <= len(passage.text)):
            citation.resolved = False
            citation.resolution_note = "offsets_out_of_range"
            return citation
        if passage.text[start:end] == citation.quoted_text:
            citation.resolved = True
            citation.resolution_note = None
        elif citation.quoted_text and citation.quoted_text in passage.text:
            citation.resolved = False
            citation.resolution_note = "offset_drift"
        else:
            citation.resolved = False
            citation.resolution_note = "text_absent_from_passage"
        return citation

    if "Field" in loc:
        f = loc["Field"]
        record = record_index.get(f["record"])
        if record is None:
            citation.resolved = False
            citation.resolution_note = "record_not_found"
            return citation
        found, value = _walk(record, f["field_path"])
        if not found:
            citation.resolved = False
            citation.resolution_note = "field_not_found"
            return citation
        if str(value) == citation.quoted_text:
            citation.resolved = True
            citation.resolution_note = None
        else:
            citation.resolved = False
            citation.resolution_note = "field_value_mismatch"
        return citation

    citation.resolved = False
    citation.resolution_note = "unsupported_locator"
    return citation


def resolve_and_drop(facts: List[Fact], claim: Claim) -> Tuple[List[Fact], List[Dict[str, Any]]]:
    """Resolve every citation on every fact; drop facts that do not fully resolve.

    A fact must have *all* its citations resolve. A derived fact citing two
    operands is only checkable if both are checkable.
    """
    record_index = build_record_index(claim)
    kept: List[Fact] = []
    dropped: List[Dict[str, Any]] = []

    for fact in facts:
        if not fact.citations:
            dropped.append({"fact_id": fact.fact_id, "assertion": fact.assertion,
                            "reason": "no_citations"})
            continue
        for c in fact.citations:
            resolve_citation(c, claim, record_index)
        unresolved = [c for c in fact.citations if not c.resolved]
        if unresolved:
            dropped.append({
                "fact_id": fact.fact_id,
                "assertion": fact.assertion,
                "reason": "unresolved_citation",
                "notes": [c.resolution_note for c in unresolved],
            })
            continue
        kept.append(fact)

    return kept, dropped
