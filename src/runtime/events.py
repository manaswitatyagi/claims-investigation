"""Processing event contract and a per-claim in-memory bus.

WHAT AN EVENT MAY CONTAIN
------------------------
Structured product state only. No chain-of-thought, no model reasoning traces,
no raw completions. An event says *what is now true of the claim*, never *how the
model got there*. `rationale` on a relationship is the one-sentence neutral
explanation the domain layer already produces for the static view; it is not
reasoning exhaust.

NOT AN EVENT-SOURCING PLATFORM. There is no log to replay, no projection
rebuild, and no durable event store. Events narrate an in-flight ingestion to
whoever is watching; the authoritative state is `ClaimState`, saved as JSON.
"""
from __future__ import annotations

import json
import queue
import threading
import time
from typing import Any, Dict, Iterator, List, Optional

DOCUMENT_RECEIVED = "document_received"
PASSAGES_CREATED = "passages_created"
EXTRACTION_STARTED = "extraction_started"
ASSERTION_EXTRACTED = "assertion_extracted"
CITATION_VERIFIED = "citation_verified"
ASSERTION_DROPPED = "assertion_dropped"
ASSERTION_NORMALIZED = "assertion_normalized"
NEIGHBORHOOD_UPDATED = "neighborhood_updated"
RELATIONSHIP_CHANGED = "relationship_changed"
PROCESSING_COMPLETE = "processing_complete"
PROCESSING_FAILED = "processing_failed"

EVENT_TYPES = [
    DOCUMENT_RECEIVED, PASSAGES_CREATED, EXTRACTION_STARTED, ASSERTION_EXTRACTED,
    CITATION_VERIFIED, ASSERTION_DROPPED, ASSERTION_NORMALIZED,
    NEIGHBORHOOD_UPDATED, RELATIONSHIP_CHANGED, PROCESSING_COMPLETE,
    PROCESSING_FAILED,
]

#: Anything matching these must never appear in a payload key.
FORBIDDEN_KEYS = ("reasoning", "thinking", "chain_of_thought", "completion",
                  "raw_response", "prompt", "materiality", "credibility",
                  "liability", "fraud", "suspicion")


class EventContractViolation(RuntimeError):
    pass


def make_event(kind: str, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if kind not in EVENT_TYPES:
        raise EventContractViolation("unknown event type %r" % kind)
    _assert_clean(payload)
    return {"type": kind, "session_id": session_id,
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "payload": payload}


def _assert_clean(node: Any, path: str = "payload") -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            low = str(k).lower()
            for bad in FORBIDDEN_KEYS:
                if bad in low:
                    raise EventContractViolation(
                        "%s.%s would leak %r into the event stream" % (path, k, bad))
            _assert_clean(v, path + "." + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _assert_clean(v, "%s[%d]" % (path, i))


class EventBus:
    """Fan-out to every open SSE connection for one claim.

    Bounded queues: a stalled browser tab must not grow memory without limit,
    and dropping an event for a dead listener is better than blocking ingestion.
    """

    def __init__(self, history: int = 200) -> None:
        self._lock = threading.Lock()
        self._subscribers: List["queue.Queue[Dict[str, Any]]"] = []
        self._history: List[Dict[str, Any]] = []
        self._history_limit = history

    def publish(self, event: Dict[str, Any]) -> None:
        with self._lock:
            self._history.append(event)
            del self._history[:-self._history_limit]
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass

    def subscribe(self) -> "queue.Queue[Dict[str, Any]]":
        q: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=1000)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q) -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._history[-limit:])


_BUSES: Dict[str, EventBus] = {}
_BUS_LOCK = threading.Lock()


def bus_for(claim_id: str) -> EventBus:
    with _BUS_LOCK:
        if claim_id not in _BUSES:
            _BUSES[claim_id] = EventBus()
        return _BUSES[claim_id]


def sse_frame(event: Dict[str, Any]) -> bytes:
    return ("event: %s\ndata: %s\n\n"
            % (event["type"], json.dumps(event))).encode("utf-8")
