"""E2 pipeline — ontology-tagged assertions, with BOTH difference strategies.

Arm A (flat) and arm B (neighbourhoods) run over the SAME verified fact set from
the same extraction, so the comparison isolates the difference stage. Anything
else would confound the two changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.claim_model import Claim, SynthesisResult
from src.differences import deterministic as det_diff
from src.differences.llm_propose import propose_differences, render_facts
from src.differences.neighborhoods import (build_neighborhoods, classify,
                                           render_members, to_differences)
from src.extraction.llm_extract_e2 import extract_from_passages
from src.extraction.spans import resolve_and_drop
from src.extraction.structured import (became_known_facts, derive_facts,
                                       read_anchor_facts, read_structured_facts)
from src.ingestion.passages import enumerate_passages
from src.llm.client import LLMClient, NullClient
from src.llm.prompts import DIFFERENCE_SYSTEM, DIFFERENCE_USER_TEMPLATE
from src.llm.prompts_e2 import NEIGHBORHOOD_SYSTEM, NEIGHBORHOOD_USER_TEMPLATE
from src.ontology.claim_mapping import (annotate_anchor_facts, ungrouped_reason,
                                        unpack_composite_vehicle_facts)
from src.questions.checklist import build_open_questions
from src.synthesis_assembly import assemble
from src.timeline.build import build_timeline


@dataclass
class E2Run:
    result: SynthesisResult
    dropped_facts: List[Dict[str, Any]] = field(default_factory=list)
    stage_counts: Dict[str, int] = field(default_factory=dict)
    arm_a: Dict[str, Any] = field(default_factory=dict)
    arm_b: Dict[str, Any] = field(default_factory=dict)
    neighborhoods: List[Dict[str, Any]] = field(default_factory=list)
    ungrouped: List[Dict[str, Any]] = field(default_factory=list)


def run_pipeline(claim: Claim, llm: Optional[LLMClient] = None) -> E2Run:
    llm = llm or NullClient()

    passages = enumerate_passages(claim)

    facts = []
    facts.extend(read_structured_facts(claim))
    anchor = read_anchor_facts(claim)
    annotate_anchor_facts(anchor)
    facts.extend(anchor)
    facts.extend(unpack_composite_vehicle_facts(claim, anchor))
    facts.extend(derive_facts(claim))
    facts.extend(became_known_facts(claim))
    deterministic_count = len(facts)

    extracted, unlocatable = extract_from_passages(claim, passages, llm)
    facts.extend(extracted)

    det_facts, det_differences = det_diff.detect(claim)
    facts.extend(det_facts)

    facts, dropped = resolve_and_drop(facts, claim)
    dropped = list(unlocatable) + dropped
    surviving = {f.fact_id for f in facts}
    det_differences = [d for d in det_differences
                       if all(p.fact_id in surviving for p in d.positions)]

    # -- ARM A: flat. Every fact, one global call. Exactly E1b's stage. -----
    flat_payload = DIFFERENCE_SYSTEM + DIFFERENCE_USER_TEMPLATE.format(
        facts_block=render_facts(facts))
    a_diffs = propose_differences(facts, llm)
    a_diffs = [d for d in a_diffs if all(p.fact_id in surviving for p in d.positions)]

    # -- ARM B: deterministic grouping, then narrow comparison --------------
    neighborhoods, ungrouped_facts = build_neighborhoods(facts)
    relationships, b_calls, b_chars = [], 0, 0
    for nb in neighborhoods:
        rel = classify(nb, llm)
        if rel["method"] == "llm":
            b_calls += 1
            b_chars += len(NEIGHBORHOOD_SYSTEM) + len(
                NEIGHBORHOOD_USER_TEMPLATE.format(
                    entity_id=nb["entity_id"], event_id=nb["event_id"] or "n/a",
                    predicate=nb["predicate"], assertions=render_members(nb["members"])))
        relationships.append(rel)
    b_diffs = to_differences(neighborhoods, relationships)

    timeline = build_timeline(facts)
    open_questions = build_open_questions(claim)

    # The persisted SynthesisResult uses ARM B. Arm A is retained for comparison.
    result = assemble(
        claim=claim, facts=facts, timeline=timeline,
        differences=det_differences + b_diffs, open_questions=open_questions,
        model_id=llm.model_id, prompt_version=llm.prompt_version, dropped=dropped,
        passages_total=len(passages), passages_processed=len(passages))

    counts = {r["relationship"]: 0 for r in relationships if r["relationship"]}
    for r in relationships:
        if r["relationship"]:
            counts[r["relationship"]] = counts.get(r["relationship"], 0) + 1

    return E2Run(
        result=result, dropped_facts=dropped,
        stage_counts={"passages": len(passages),
                      "facts_deterministic": deterministic_count,
                      "facts_extracted": len(extracted),
                      "facts_unlocatable": len(unlocatable),
                      "facts_final": len(facts),
                      "neighborhoods": len(neighborhoods),
                      "neighborhoods_compared": sum(1 for n in neighborhoods
                                                    if not n["singleton"]),
                      "ungrouped_facts": len(ungrouped_facts),
                      "open_questions": len(open_questions)},
        arm_a={"strategy": "flat_all_facts_one_call",
               "facts_considered": len(facts), "model_calls": 1,
               "input_chars": len(flat_payload),
               "differences": [d.to_dict() for d in a_diffs]},
        arm_b={"strategy": "deterministic_neighborhoods",
               "facts_considered": len(facts),
               "neighborhoods_total": len(neighborhoods),
               "model_calls": b_calls, "input_chars": b_chars,
               "relationship_counts": counts,
               "differences": [d.to_dict() for d in b_diffs]},
        neighborhoods=[{"entity_id": n["entity_id"], "event_id": n["event_id"],
                        "predicate": n["predicate"], "singleton": n["singleton"],
                        "distinct_values": [repr(v) for v in n["distinct_values"]],
                        "members": [{"fact_id": m.fact_id, "value": repr(m.value),
                                     "asserter": m.asserter.kind,
                                     "document_id": m.citations[0].document_id,
                                     "assertion": m.assertion,
                                     "citation": m.citations[0].to_dict()}
                                    for m in n["members"]],
                        "relationship": rel["relationship"], "method": rel["method"],
                        "rationale": rel["rationale"]}
                       for n, rel in zip(neighborhoods, relationships)],
        ungrouped=[{"fact_id": f.fact_id, "subject": f.subject,
                    "assertion": f.assertion, "provenance": f.provenance,
                    "reason": ungrouped_reason(f)} for f in ungrouped_facts])
