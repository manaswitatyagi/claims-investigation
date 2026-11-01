"""Mutable claim state for the live demo.

SEEDED FROM, NEVER WRITING TO, THE EXPERIMENT ARTIFACTS.
`data/generated/e2_ontology/` is read once to bootstrap and is then immutable as
far as this module is concerned. Runtime state lives in `data/runtime/<claim>/`,
a clearly separate directory, as plain JSON. No database, no queue, no cache
server — the milestone is a demo, and a file is the honest amount of machinery.

The state IS the `claim-view/1` payload plus an index. That is deliberate: the
DTO already carries every field a neighbourhood needs (`entity_id`, `event_id`,
`predicate`, `value_normalised`, `evidence`), so recomputation needs no shadow
model and the thing the browser reads is the thing the server owns.

RELATIONSHIP MEANING IS COMPUTED HERE, NOT IN REACT. `recompute` calls the same
`src.differences.neighborhoods.classify` the static E2 path used.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
from typing import Any, Dict, List, Optional, Tuple

from src.claim_model import Asserter, Citation, Fact, field_locator, text_span
from src.differences.neighborhoods import build_neighborhoods, classify
from src.presentation.view_model import ROOT, _entities, _label, build_claim_view

RUNTIME_DIR = os.path.join(ROOT, "data", "runtime")
SEED = {
    "claim_001": {
        "run_dir": os.path.join(ROOT, "data", "generated", "e2_ontology", "run_1"),
        "fixture_dir": os.path.join(ROOT, "data", "fixtures", "claim_001"),
    }
}

_LOCKS: Dict[str, threading.Lock] = {}


def _lock(claim_id: str) -> threading.Lock:
    return _LOCKS.setdefault(claim_id, threading.Lock())


class ClaimState:
    def __init__(self, claim_id: str, view: Dict[str, Any]) -> None:
        self.claim_id = claim_id
        self.view = view

    # -- persistence -------------------------------------------------------

    @property
    def dir(self) -> str:
        return os.path.join(RUNTIME_DIR, self.claim_id)

    @property
    def path(self) -> str:
        return os.path.join(self.dir, "state.json")

    @classmethod
    def load(cls, claim_id: str) -> "ClaimState":
        path = os.path.join(RUNTIME_DIR, claim_id, "state.json")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                return cls(claim_id, json.load(fh))
        return cls.seed(claim_id)

    @classmethod
    def seed(cls, claim_id: str) -> "ClaimState":
        cfg = SEED[claim_id]
        view = build_claim_view(cfg["run_dir"], cfg["fixture_dir"])
        view["seeded_from"] = os.path.relpath(cfg["run_dir"], ROOT)
        view["added_documents"] = []
        state = cls(claim_id, view)
        state.save()
        return state

    @classmethod
    def reset(cls, claim_id: str) -> "ClaimState":
        """Back to the E2 baseline. The demo's undo button."""
        d = os.path.join(RUNTIME_DIR, claim_id)
        if os.path.isdir(d):
            shutil.rmtree(d)
        return cls.seed(claim_id)

    def save(self) -> None:
        os.makedirs(os.path.join(self.dir, "documents"), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.view, fh, indent=2)
        os.replace(tmp, self.path)

    # -- lookups -----------------------------------------------------------

    def neighborhood_key(self, entity_id, event_id, predicate) -> Optional[Dict[str, Any]]:
        for n in self.view["neighborhoods"]:
            if (n["entity_id"], n["event_id"], n["predicate"]) == (entity_id, event_id, predicate):
                return n
        return None

    def _next_neighborhood_id(self) -> str:
        nums = [int(n["neighborhood_id"].split("_")[-1])
                for n in self.view["neighborhoods"]
                if n["neighborhood_id"].split("_")[-1].isdigit()]
        return "nb_%03d" % ((max(nums) if nums else 0) + 1)

    def next_assertion_id(self, prefix: str) -> str:
        n = 1
        while "%s_%03d" % (prefix, n) in self.view["assertions"]:
            n += 1
        return "%s_%03d" % (prefix, n)

    # -- mutation ----------------------------------------------------------

    def add_source(self, source: Dict[str, Any]) -> None:
        self.view["sources"] = [s for s in self.view["sources"]
                                if s["source_id"] != source["source_id"]] + [source]

    def update_source(self, source_id: str, **fields) -> Optional[Dict[str, Any]]:
        for s in self.view["sources"]:
            if s["source_id"] == source_id:
                s.update(fields)
                return s
        return None

    def add_assertion(self, assertion: Dict[str, Any]) -> None:
        self.view["assertions"][assertion["assertion_id"]] = assertion

    def add_unresolved(self, assertion_id: str, text: str, reason: str) -> None:
        """A verified assertion the ontology could not place.

        It is kept and shown, with its relationship state unresolved. It is NOT
        pushed into a nearly-right neighbourhood — a fake mapping would produce a
        confident relationship between things that are not comparable.
        """
        self.view["ungrouped"].append(
            {"assertion_id": assertion_id, "text": text,
             "provenance": "extracted", "reason": reason})

    def recompute(self, entity_id, event_id, predicate, llm) -> Dict[str, Any]:
        """Recompute ONE neighbourhood. Returns the before/after delta.

        Only the affected key is touched; the other 31 neighbourhoods are not
        reclassified and cost nothing.
        """
        members = [a for a in self.view["assertions"].values()
                   if (a["entity_id"], a["event_id"], a["predicate"])
                   == (entity_id, event_id, predicate)]
        existing = self.neighborhood_key(entity_id, event_id, predicate)
        before = existing["relationship"] if existing else None
        before_count = len(existing["assertion_ids"]) if existing else 0

        facts = [_as_fact(a) for a in members]
        groups, _ = build_neighborhoods(facts)
        group = groups[0] if groups else None
        if group is None:
            return {"changed": False, "neighborhood_id": existing["neighborhood_id"] if existing else None}

        rel = classify(group, llm)
        # If no comparison could be made but the member set is unchanged, the
        # previous relationship still describes these assertions — keep it rather
        # than degrading a known state to unresolved. If members DID change, a
        # stale relationship would be a lie, so it is cleared.
        if (rel["method"] == "not_compared" and existing
                and set(existing["assertion_ids"]) == {a["assertion_id"] for a in members}
                and existing["relationship"]):
            rel = {"relationship": existing["relationship"],
                   "method": existing["relationship_method"],
                   "rationale": existing["rationale"]}

        source_ids: List[str] = []
        for a in members:
            if a["source_id"] not in source_ids:
                source_ids.append(a["source_id"])

        record = {
            "neighborhood_id": existing["neighborhood_id"] if existing else self._next_neighborhood_id(),
            "entity_id": entity_id, "event_id": event_id, "predicate": predicate,
            "predicate_label": _label(predicate),
            "relationship": rel["relationship"], "relationship_method": rel["method"],
            "rationale": rel["rationale"], "singleton": group["singleton"],
            "assertion_ids": [a["assertion_id"] for a in members],
            "source_ids": source_ids,
            "distinct_value_count": len(group["distinct_values"]),
        }
        if existing:
            self.view["neighborhoods"][self.view["neighborhoods"].index(existing)] = record
        else:
            self.view["neighborhoods"].append(record)

        self.view["entities"] = _entities(self.view["neighborhoods"])
        return {
            "changed": rel["relationship"] != before,
            "is_new": existing is None,
            "before": before, "after": rel["relationship"],
            "before_assertion_count": before_count,
            "after_assertion_count": len(members),
            "neighborhood_id": record["neighborhood_id"],
            "predicate": predicate, "predicate_label": record["predicate_label"],
            "entity_id": entity_id, "event_id": event_id,
            "rationale": rel["rationale"], "method": rel["method"],
        }

    def refresh_source_counts(self) -> None:
        counts: Dict[str, int] = {}
        for a in self.view["assertions"].values():
            counts[a["source_id"]] = counts.get(a["source_id"], 0) + 1
        for s in self.view["sources"]:
            s["verified_assertion_count"] = counts.get(s["source_id"], 0)


def _as_fact(a: Dict[str, Any]) -> Fact:
    """Adapter: view assertion -> domain Fact, so the SAME classifier runs.

    Reimplementing comparison over DTOs would create a second definition of what
    "contradictory" means, and the two would drift.
    """
    ev = a.get("evidence") or {}
    if ev.get("locator_kind") == "TextSpan":
        loc = text_span(ev["passage_id"], ev["char_start"], ev["char_end"])
    else:
        loc = field_locator(ev.get("field_record") or "record",
                            ev.get("field_path") or "field")
    return Fact(
        fact_id=a["assertion_id"], assertion=a["text"],
        asserter=Asserter(kind=a["asserter_kind"], name=a.get("asserter_name")),
        provenance=a.get("provenance", "extracted"),
        subject=a.get("predicate"),
        subject_entity_id=a.get("entity_id"), predicate=a.get("predicate"),
        value=a.get("value_normalised"), event_id=a.get("event_id"),
        citations=[Citation(document_id=ev.get("document_id") or a["source_id"],
                            document_version=ev.get("document_version") or "v1",
                            locator=loc, quoted_text=ev.get("quote") or "",
                            resolved=True)])
