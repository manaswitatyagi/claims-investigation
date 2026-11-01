"""Canonical types for the E1 pipeline.

Mirrors `data/schema.md` Part 1 (output contract) and Part 2 (domain model).
Every design note that looks like an over-comment is load-bearing: it records a
decision from `docs/decision_log.md` that the code is enforcing.

Python 3.9 compatible.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------
# Locators and citations
# --------------------------------------------------------------------------

def text_span(passage_id: str, char_start: int, char_end: int) -> Dict[str, Any]:
    """P1: span-level, never document-level. "FNOL" is not a citation."""
    return {"TextSpan": {"passage_id": passage_id,
                         "char_start": char_start,
                         "char_end": char_end}}


def field_locator(record: str, field_path: str) -> Dict[str, Any]:
    """Structured facts cite too. A user should be able to check a deterministic
    fact as easily as an extracted one."""
    return {"Field": {"record": record, "field_path": field_path}}


def timestamp_locator(hhmmss: str) -> Dict[str, Any]:
    return {"Timestamp": {"hhmmss": hhmmss}}


@dataclass
class Citation:
    document_id: str
    document_version: str
    locator: Dict[str, Any]
    quoted_text: str
    resolved: bool = False
    resolution_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_version": self.document_version,
            "locator": self.locator,
            "quoted_text": self.quoted_text,
            "resolved": self.resolved,
            "resolution_note": self.resolution_note,
        }


# --------------------------------------------------------------------------
# Normalised values
# --------------------------------------------------------------------------

def date_value(value: Optional[str], precision: str, raw_expression: str) -> Dict[str, Any]:
    """`value` MUST be None when precision == 'vague'.

    Inventing a timestamp for "that evening" is a chronology error, not a
    normalisation. The raw expression is preserved so the fact is carried
    without being falsified.
    """
    if precision == "vague" and value is not None:
        raise ValueError(
            "invented precision: a vague date expression cannot carry a value "
            "(raw_expression=%r)" % raw_expression
        )
    return {"Date": {"value": value, "precision": precision,
                     "raw_expression": raw_expression}}


def quantity_value(value: float, unit: str) -> Dict[str, Any]:
    return {"Quantity": {"value": value, "unit": unit}}


def boolean_value(value: bool) -> Dict[str, Any]:
    return {"Boolean": {"value": value}}


def money_value(amount: float, currency: str = "USD") -> Dict[str, Any]:
    return {"Money": {"amount": amount, "currency": currency}}


# --------------------------------------------------------------------------
# Facts
# --------------------------------------------------------------------------

@dataclass
class Asserter:
    """Required, no default.

    In a claim file *who said this* often matters more than *what was said*.
    Misattribution is the error most likely to be invisible in evaluation and
    damaging in a deposition, so it gets its own metric (PRD §12.2).
    """
    kind: str
    name: Optional[str] = None
    party_id: Optional[str] = None   # set ONLY on human-confirmed entity resolution

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "name": self.name, "party_id": self.party_id}


@dataclass
class Fact:
    """An EVIDENCE-BACKED ASSERTION. Not guaranteed objective truth.

    A Fact records that *some source stated something*, with a verified citation
    proving the source stated it. It never records that the statement is correct.
    Three sources asserting different travel directions produce three Facts, all
    equally valid as Facts and at most one of them true about the world. No stage
    of this system decides which (D-036).

    ONTOLOGY FIELDS (optional, added for E2). Each exists because COMPARISON
    requires it, not because knowledge graphs usually carry it (D-036):

      subject_entity_id  Which thing this is about. Comparing assertions about
                         different vehicles is meaningless; without an entity id
                         "the vehicle" in the FNOL and "the Mercedes" in the
                         statement are unlinked strings.
      predicate          Which property, from a controlled vocabulary. The free
                         text `subject` proved unstable across runs — the same
                         property came back as direction_of_travel,
                         vehicle_direction_of_travel and vehicle_travel_direction
                         — so grouping on it is model-dependent.
      value              The normalised value, so `north` / `N` / `northbound`
                         collapse while `25 mph` and `moving quickly` do not.
      event_id           Temporal scope. Two assertions about the same property
                         at different times are not in conflict.

    They are OPTIONAL and omitted from `to_dict()` when unset, so a Fact produced
    by the E1/E1b path serialises byte-identically to before.
    """
    fact_id: str
    assertion: str
    asserter: Asserter
    provenance: str                      # deterministic | extracted
    citations: List[Citation]
    subject: Optional[str] = None
    normalised_value: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[float] = None
    review: Optional[Dict[str, Any]] = None
    subject_entity_id: Optional[str] = None
    predicate: Optional[str] = None
    value: Optional[Any] = None
    event_id: Optional[str] = None

    def neighborhood_key(self):
        """Deterministic grouping key, or None if this fact is not comparable.

        A fact missing an entity or a predicate cannot be placed. That is a
        finding to report, not a bucket to force it into.
        """
        if not self.subject_entity_id or not self.predicate:
            return None
        return (self.subject_entity_id, self.event_id, self.predicate)

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "fact_id": self.fact_id,
            "assertion": self.assertion,
            "asserter": self.asserter.to_dict(),
            "provenance": self.provenance,
            "citations": [c.to_dict() for c in self.citations],
            "subject": self.subject,
            "normalised_value": self.normalised_value,
            "review": self.review,
        }
        if self.provenance == "extracted":
            out["extraction_confidence"] = self.extraction_confidence
        # Omitted entirely when unset, so E1/E1b output is unchanged.
        for name in ("subject_entity_id", "predicate", "value", "event_id"):
            v = getattr(self, name)
            if v is not None:
                out[name] = v
        return out


# --------------------------------------------------------------------------
# Differences
# --------------------------------------------------------------------------

@dataclass
class Position:
    fact_id: str
    stance: str

    def to_dict(self) -> Dict[str, Any]:
        return {"fact_id": self.fact_id, "stance": self.stance}


@dataclass
class Difference:
    """`positions` is a set, not a pair.

    Three-way disagreement is real: the FNOL, the recorded statement, and the
    police narrative can each say something different about direction of
    travel. `fact_a`/`fact_b` would force a rewrite the first time that happens.

    `materiality` and `materiality_rationale` exist so the shape is visible and
    are NEVER populated by V1 (PROVISIONAL — GATED ON D-014). They are typed
    `None` here and `"type": "null"` in the schema, so writing a value fails.
    """
    difference_id: str
    subject: str
    positions: List[Position]
    detection_method: str                # deterministic | extracted
    already_noted_value: bool = False
    already_noted_fact_id: Optional[str] = None
    review: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "difference_id": self.difference_id,
            "subject": self.subject,
            "positions": [p.to_dict() for p in self.positions],
            "detection_method": self.detection_method,
            "already_noted": {"value": self.already_noted_value,
                              "fact_id": self.already_noted_fact_id},
            "review": self.review,
            "materiality": None,
            "materiality_rationale": None,
        }


# --------------------------------------------------------------------------
# Open questions
# --------------------------------------------------------------------------

@dataclass
class OpenQuestion:
    """`supporting_citations` is optional, unlike `Fact.citations`.

    An OpenQuestion about an *absent* document has nothing to cite. That is the
    one place drop-if-uncitable cannot apply, and precisely why OpenQuestion is
    not a Fact with a status (D-027).
    """
    question_id: str
    question: str
    kind: str
    provenance: str
    expected_source: Optional[str] = None
    supporting_citations: List[Citation] = field(default_factory=list)
    related_difference_id: Optional[str] = None
    review: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "kind": self.kind,
            "provenance": self.provenance,
            "expected_source": self.expected_source,
            "supporting_citations": [c.to_dict() for c in self.supporting_citations],
            "related_difference_id": self.related_difference_id,
            "review": self.review,
        }


# --------------------------------------------------------------------------
# Timeline
# --------------------------------------------------------------------------

@dataclass
class TimelineEvent:
    """Derived, never stored. Recomputed from Facts carrying a Date value."""
    event_id: str
    axis: str                            # occurred | became_known
    when: Dict[str, Any]
    label: str
    source_fact_ids: List[str]
    ordering_confidence: str             # exact | approximate | unorderable

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------
# Header and result
# --------------------------------------------------------------------------

@dataclass
class HeaderField:
    value: Optional[str]
    state: str                           # present | absent_from_file | not_assessed
    fact_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "state": self.state, "fact_ids": self.fact_ids}


@dataclass
class ClaimHeader:
    coverage: HeaderField
    loss_description: HeaderField
    jurisdiction: HeaderField
    damages: HeaderField
    status: HeaderField
    reserve: HeaderField

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.to_dict() for k, v in self.__dict__.items()}


@dataclass
class SynthesisResult:
    synthesis_id: str
    claim_id: str
    generated_at: str
    checkpoint: str
    document_set: List[Dict[str, str]]
    model_id: Optional[str]
    prompt_version: Optional[str]
    header: ClaimHeader
    timeline: List[TimelineEvent]
    facts: List[Fact]
    differences: List[Difference]
    open_questions: List[OpenQuestion]
    coverage: Dict[str, int]
    not_assessed: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "synthesis_id": self.synthesis_id,
            "claim_id": self.claim_id,
            "generated_at": self.generated_at,
            "checkpoint": self.checkpoint,
            "document_set": self.document_set,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "header": self.header.to_dict(),
            "timeline": [t.to_dict() for t in self.timeline],
            "facts": [f.to_dict() for f in self.facts],
            "differences": [d.to_dict() for d in self.differences],
            "open_questions": [q.to_dict() for q in self.open_questions],
            "coverage": self.coverage,
            "not_assessed": self.not_assessed,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# --------------------------------------------------------------------------
# Input side — thin wrappers over the validated claim bundle
# --------------------------------------------------------------------------

@dataclass
class Passage:
    passage_id: str
    document_id: str
    document_version: str
    label: str
    text: str
    speaker_turns: List[Dict[str, Any]] = field(default_factory=list)

    def speaker_at(self, char_start: int) -> Optional[Dict[str, Any]]:
        """Which speaker turn contains this offset.

        This is what makes asserter accuracy checkable in a transcript. Without
        it the leading-question failure — the adjuster asking "so you were
        stopped at the light?" and the model attributing it to the claimant —
        is unverifiable.
        """
        for turn in self.speaker_turns:
            if turn["char_start"] <= char_start < turn["char_end"]:
                return turn
        return None


@dataclass
class Document:
    document_id: str
    type: str
    version: str
    received_date: str
    checkpoint_available: str
    structure_class: str
    structured_fields: Dict[str, Any] = field(default_factory=dict)
    passages: List[Passage] = field(default_factory=list)


@dataclass
class Claim:
    claim_id: str
    checkpoint: str
    provenance: Dict[str, Any]
    claim_record: Dict[str, Any]
    documents: List[Document]
    policy_record: Optional[Dict[str, Any]] = None
    structured_records: Optional[Dict[str, Any]] = None
    prior_claims: List[Dict[str, Any]] = field(default_factory=list)
    reserve_history: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def document(self, document_id: str) -> Optional[Document]:
        for d in self.documents:
            if d.document_id == document_id:
                return d
        return None

    def passage(self, passage_id: str) -> Optional[Passage]:
        for d in self.documents:
            for p in d.passages:
                if p.passage_id == passage_id:
                    return p
        return None
