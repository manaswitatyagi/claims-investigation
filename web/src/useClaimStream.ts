import { useCallback, useEffect, useRef, useState } from "react";
import { STATIC_MODE } from "./api";
import type { ProcessingEvent, RelationshipDelta } from "./types";

export interface IngestionSession {
  sessionId: string | null;
  documentId: string | null;
  documentName: string | null;
  status: "idle" | "uploading" | "processing" | "complete" | "failed";
  extracted: number;
  verified: number;
  dropped: number;
  mapped: number;
  unresolved: number;
  error: string | null;
  /** Assertions produced in THIS session, so the map can mark what is new. */
  newAssertionIds: Set<string>;
  /** Neighbourhoods touched, and those whose relationship actually changed. */
  updatedNeighborhoodIds: Set<string>;
  relationshipChanges: RelationshipDelta[];
  log: ProcessingEvent[];
}

const EMPTY: IngestionSession = {
  sessionId: null, documentId: null, documentName: null, status: "idle",
  extracted: 0, verified: 0, dropped: 0, mapped: 0, unresolved: 0, error: null,
  newAssertionIds: new Set(), updatedNeighborhoodIds: new Set(),
  relationshipChanges: [], log: [],
};

/** Subscribes to the claim's SSE stream and folds events into session state.
 *  It never interprets relationship meaning — it only records what the backend
 *  said the relationship became. */
export function useClaimStream(claimId: string, onStateChanged: () => void) {
  const [session, setSession] = useState<IngestionSession>(EMPTY);
  const [connected, setConnected] = useState(false);
  const changedRef = useRef(onStateChanged);
  changedRef.current = onStateChanged;

  useEffect(() => {
    // No server, no stream. EventSource retries on failure by design, so
    // opening one against a static host would reconnect forever and report
    // "disconnected" about a backend that was never meant to be there.
    if (STATIC_MODE) return;

    const es = new EventSource(`/api/claim/${claimId}/stream`);
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);

    const handle = (raw: MessageEvent) => {
      const ev: ProcessingEvent = JSON.parse(raw.data);
      setSession((prev) => fold(prev, ev));
      if (ev.type === "processing_complete" || ev.type === "processing_failed") {
        changedRef.current();
      }
    };
    const types = [
      "document_received", "passages_created", "extraction_started",
      "assertion_extracted", "citation_verified", "assertion_dropped",
      "assertion_normalized", "neighborhood_updated", "relationship_changed",
      "processing_complete", "processing_failed",
    ];
    types.forEach((t) => es.addEventListener(t, handle as EventListener));
    return () => es.close();
  }, [claimId]);

  const reset = useCallback(() => setSession(EMPTY), []);
  const beginUpload = useCallback((name: string) => {
    setSession({ ...EMPTY, newAssertionIds: new Set(), updatedNeighborhoodIds: new Set(),
                 status: "uploading", documentName: name });
  }, []);

  return { session, connected, reset, beginUpload };
}

function fold(prev: IngestionSession, ev: ProcessingEvent): IngestionSession {
  const s: IngestionSession = {
    ...prev,
    log: [...prev.log, ev].slice(-200),
    newAssertionIds: new Set(prev.newAssertionIds),
    updatedNeighborhoodIds: new Set(prev.updatedNeighborhoodIds),
  };
  const p = ev.payload;
  switch (ev.type) {
    case "document_received":
      return { ...s, sessionId: ev.session_id, documentId: p.document_id,
               documentName: p.name ?? prev.documentName, status: "processing" };
    case "assertion_extracted":
      return { ...s, extracted: s.extracted + 1 };
    case "citation_verified":
      s.newAssertionIds.add(p.assertion_id);
      return { ...s, verified: s.verified + 1 };
    case "assertion_dropped":
      return { ...s, dropped: s.dropped + 1 };
    case "assertion_normalized":
      return p.predicate && p.entity_id
        ? { ...s, mapped: s.mapped + 1 }
        : { ...s, unresolved: s.unresolved + 1 };
    case "neighborhood_updated":
      s.updatedNeighborhoodIds.add(p.neighborhood_id);
      return s;
    case "relationship_changed":
      return { ...s, relationshipChanges: [...s.relationshipChanges, {
        neighborhood_id: p.neighborhood_id, predicate: p.predicate,
        predicate_label: p.predicate_label, from: p.from, to: p.to,
        rationale: p.rationale }] };
    case "processing_complete":
      return { ...s, status: "complete", extracted: p.extracted ?? s.extracted,
               verified: p.verified ?? s.verified, dropped: p.dropped ?? s.dropped,
               mapped: p.mapped ?? s.mapped, unresolved: p.unresolved ?? s.unresolved };
    case "processing_failed":
      return { ...s, status: "failed", error: p.error ?? "processing failed" };
    default:
      return s;
  }
}
