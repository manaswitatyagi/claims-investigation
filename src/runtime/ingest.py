"""Live ingestion of one uploaded document.

Reuses the E1b/E2 pipeline components exactly. There is no second ingestion
architecture for the UI — the same extractor, the same deterministic quote
locator, the same ontology normalisation, the same classifier.

    uploaded text
        -> Document + Passage
        -> LLM extraction (prompts_e2)
        -> deterministic quote locator          [E1b]
        -> citation verified, or DROPPED        [D-020 P2, unweakened]
        -> ontology normalisation               [E2, lookup tables]
        -> admitted to claim state
        -> affected neighbourhoods recomputed   [only the affected keys]
        -> relationship deltas emitted

GROUNDING IS NOT RELAXED FOR THE DEMO. An assertion whose quote cannot be located
is dropped and counted, exactly as in E1b. An assertion that verifies but cannot
be placed in the ontology is KEPT and marked unresolved — never forced into a
nearly-right neighbourhood.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.claim_model import Passage
from src.extraction.quote_locator import RESOLVED, locate
from src.ingestion.loader import load_claim
from src.llm.prompts_e2 import EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE, extract_schema
from src.ontology.claim_mapping import EVENT_ID, build_roster
from src.ontology.vocabulary import PREDICATES, is_event_scoped, normalise_value
from src.presentation.view_model import SOURCE_LABELS, _label, _value_display
from src.runtime import events as ev
from src.runtime.claim_state import SEED, ClaimState

VALID_ASSERTER_KINDS = {"claimant", "insured", "witness", "police_officer",
                        "adjuster", "provider", "system_record", "attorney"}
MAX_BYTES = 200_000
ALLOWED_EXT = {".md", ".txt"}


class UnsupportedDocument(ValueError):
    pass


def store_document(claim_id: str, filename: str, raw: bytes) -> Dict[str, Any]:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise UnsupportedDocument("only .md and .txt are supported in this milestone "
                                  "(got %r)" % (ext or "no extension"))
    if len(raw) > MAX_BYTES:
        raise UnsupportedDocument("file is larger than %d bytes" % MAX_BYTES)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedDocument("file is not valid UTF-8 text: %s" % exc)
    if not text.strip():
        raise UnsupportedDocument("file is empty")

    state = ClaimState.load(claim_id)
    doc_id = "doc_%s" % uuid.uuid4().hex[:8]
    dest = os.path.join(state.dir, "documents", "%s%s" % (doc_id, ext))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(text)
    return {"document_id": doc_id, "filename": filename, "path": dest, "text": text}


def to_passages(doc_id: str, text: str) -> List[Passage]:
    """One passage per document for this milestone.

    Markdown headings and the synthetic banner are stripped so the model is not
    asked to extract from fixture scaffolding, mirroring the Claim 001 builder.
    """
    kept = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.lower().startswith(("**synthetic", "**evaluation note")):
            continue
        kept.append(line.replace("**", "").rstrip())
    body = "\n".join(kept).strip()
    while "\n\n\n" in body:
        body = body.replace("\n\n\n", "\n\n")
    return [Passage(passage_id="%s.body" % doc_id, document_id=doc_id,
                    document_version="v1", label="Uploaded document body", text=body)]


def process_document(claim_id: str, stored: Dict[str, Any], llm,
                     session_id: Optional[str] = None) -> Dict[str, Any]:
    session_id = session_id or uuid.uuid4().hex[:8]
    bus = ev.bus_for(claim_id)
    emit = lambda kind, payload: bus.publish(ev.make_event(kind, session_id, payload))

    doc_id = stored["document_id"]
    state = ClaimState.load(claim_id)
    summary = {"session_id": session_id, "document_id": doc_id,
               "extracted": 0, "verified": 0, "dropped": 0,
               "mapped": 0, "unresolved": 0,
               "neighborhoods_updated": [], "relationship_changes": []}

    source = {"source_id": doc_id, "name": stored["filename"], "type": "uploaded_document",
              "verified_assertion_count": 0, "dropped_assertion_count": 0,
              "processing": "extracted, quote located in code, citation verified",
              "verification_status": "uploaded", "passage_ids": [],
              "added_in_session": session_id}
    state.add_source(source)
    state.save()
    emit(ev.DOCUMENT_RECEIVED, {"document_id": doc_id, "name": stored["filename"],
                                "status": "uploaded"})

    try:
        passages = to_passages(doc_id, stored["text"])
        source["passage_ids"] = [p.passage_id for p in passages]
        state.update_source(doc_id, passage_ids=source["passage_ids"],
                            verification_status="processing")
        state.save()
        emit(ev.PASSAGES_CREATED, {"document_id": doc_id,
                                   "passages": [{"passage_id": p.passage_id,
                                                 "length": len(p.text)} for p in passages]})

        claim = load_claim(os.path.join(SEED[claim_id]["fixture_dir"], "claim.json"))
        roster = build_roster(claim)
        entity_ids = [e["entity_id"] for e in roster]
        predicate_names = sorted(PREDICATES)
        roster_block = "\n".join("  %-12s (%s) — %s" % (e["entity_id"], e["type"],
                                                        e["description"]) for e in roster)
        predicate_block = "\n".join(
            "  %-24s subject=%-10s %s" % (p, PREDICATES[p]["subject_type"],
                                          PREDICATES[p].get("note", ""))
            for p in predicate_names)

        affected: Dict[Tuple, bool] = {}

        for passage in passages:
            emit(ev.EXTRACTION_STARTED, {"document_id": doc_id,
                                         "passage_id": passage.passage_id})
            payload = llm.complete_json(
                system=EXTRACT_SYSTEM,
                user=EXTRACT_USER_TEMPLATE.format(
                    passage_id=passage.passage_id, document_type="uploaded_document",
                    document_id=doc_id, label=passage.label, speaker_note="",
                    roster=roster_block, predicates=predicate_block, text=passage.text),
                schema=extract_schema(entity_ids, predicate_names),
                tag="ingest__%s" % passage.passage_id)

            cursor = 0
            for item in payload.get("facts", []) or []:
                summary["extracted"] += 1
                aid = state.next_assertion_id("up")
                emit(ev.ASSERTION_EXTRACTED,
                     {"assertion_id": aid, "document_id": doc_id,
                      "text": item.get("assertion"),
                      "asserter_kind": item.get("asserter_kind")})

                if item.get("asserter_kind") not in VALID_ASSERTER_KINDS \
                        or not item.get("assertion") or not item.get("quoted_text"):
                    summary["dropped"] += 1
                    emit(ev.ASSERTION_DROPPED,
                         {"assertion_id": aid, "document_id": doc_id,
                          "reason": "malformed_item",
                          "text": item.get("assertion")})
                    continue

                located = locate(passage.text, item["quoted_text"], search_from=cursor)
                if located.status != RESOLVED:
                    summary["dropped"] += 1
                    emit(ev.ASSERTION_DROPPED,
                         {"assertion_id": aid, "document_id": doc_id,
                          "reason": located.status, "text": item.get("assertion"),
                          "model_quote": item["quoted_text"],
                          "occurrences": located.occurrences})
                    continue
                cursor = located.char_end
                summary["verified"] += 1

                predicate = item.get("predicate")
                if predicate not in PREDICATES:
                    predicate = None
                value = normalise_value(predicate, item.get("value_raw")) if predicate else None
                entity_id = item.get("subject_entity_id")
                event_id = EVENT_ID if (predicate and is_event_scoped(predicate)) else None

                assertion = {
                    "assertion_id": aid, "entity_id": entity_id, "event_id": event_id,
                    "predicate": predicate, "predicate_label": _label(predicate),
                    "value": _value_display(value), "value_normalised": value,
                    "text": item["assertion"],
                    "asserter_kind": item["asserter_kind"],
                    "asserter_name": item.get("asserter_name"),
                    "provenance": "extracted", "source_id": doc_id,
                    "source_name": stored["filename"],
                    "added_in_session": session_id,
                    "evidence": {
                        "quote": located.canonical_text, "verified": True,
                        "resolution_note": "located_by:%s" % located.method,
                        "document_id": doc_id, "document_version": "v1",
                        "locator_kind": "TextSpan", "passage_id": passage.passage_id,
                        "char_start": located.char_start, "char_end": located.char_end,
                        "passage_label": passage.label, "passage_text": passage.text,
                        "field_record": None, "field_path": None,
                    },
                }
                state.add_assertion(assertion)
                emit(ev.CITATION_VERIFIED,
                     {"assertion_id": aid, "document_id": doc_id,
                      "passage_id": passage.passage_id,
                      "char_start": located.char_start, "char_end": located.char_end,
                      "quote": located.canonical_text,
                      "located_by": located.method,
                      "note": "Evidence verified: traced to exact source text. "
                              "This does not establish that the assertion is true."})

                if entity_id and predicate:
                    summary["mapped"] += 1
                    affected[(entity_id, event_id, predicate)] = True
                    emit(ev.ASSERTION_NORMALIZED,
                         {"assertion_id": aid, "entity_id": entity_id,
                          "event_id": event_id, "predicate": predicate,
                          "predicate_label": _label(predicate),
                          "value": _value_display(value),
                          "value_resolved": value is not None})
                else:
                    summary["unresolved"] += 1
                    reason = ("no predicate in this claim's vocabulary" if entity_id
                              else "no entity in this claim's roster")
                    state.add_unresolved(aid, item["assertion"], reason)
                    emit(ev.ASSERTION_NORMALIZED,
                         {"assertion_id": aid, "entity_id": entity_id,
                          "event_id": event_id, "predicate": predicate,
                          "predicate_label": _label(predicate), "value": None,
                          "value_resolved": False, "unresolved_reason": reason})

        for (entity_id, event_id, predicate) in affected:
            delta = state.recompute(entity_id, event_id, predicate, llm)
            summary["neighborhoods_updated"].append(delta["neighborhood_id"])
            emit(ev.NEIGHBORHOOD_UPDATED,
                 {k: delta[k] for k in ("neighborhood_id", "entity_id", "event_id",
                                        "predicate", "predicate_label", "after",
                                        "method", "rationale", "is_new",
                                        "after_assertion_count")})
            if delta["changed"]:
                summary["relationship_changes"].append(
                    {"neighborhood_id": delta["neighborhood_id"],
                     "predicate": predicate, "from": delta["before"],
                     "to": delta["after"]})
                emit(ev.RELATIONSHIP_CHANGED,
                     {"neighborhood_id": delta["neighborhood_id"],
                      "entity_id": entity_id, "event_id": event_id,
                      "predicate": predicate,
                      "predicate_label": delta["predicate_label"],
                      "from": delta["before"], "to": delta["after"],
                      "rationale": delta["rationale"],
                      # Stated so no reader infers the new source disproved the old.
                      "note": "Describes the relationship among assertions only. "
                              "It does not mean any source is right or wrong."})

        status = ("processed_with_dropped_assertions" if summary["dropped"]
                  else "processed")
        state.update_source(doc_id, verification_status=status,
                            dropped_assertion_count=summary["dropped"])
        state.refresh_source_counts()
        state.save()
        emit(ev.PROCESSING_COMPLETE, dict(summary, status=status))
        return summary

    except Exception as exc:                       # noqa: BLE001 - surfaced, not swallowed
        state = ClaimState.load(claim_id)
        state.update_source(doc_id, verification_status="failed",
                            error="%s: %s" % (type(exc).__name__, exc))
        state.save()
        emit(ev.PROCESSING_FAILED,
             {"document_id": doc_id, "stage": "extraction",
              "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])})
        raise
