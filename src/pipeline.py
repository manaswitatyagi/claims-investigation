"""The E1 pipeline.

Nine stages, executed in order, once. No agent, no orchestration framework, no
retrieval, no branching (PRD §8.2 — "introducing non-determinism where a `for`
loop suffices is a regression against the deterministic-first principle, and it
makes evaluation harder by making runs non-reproducible").

Exactly two stages call a model. The other seven are code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.claim_model import Claim, SynthesisResult
from src.differences import deterministic as det_diff
from src.differences.llm_propose import propose_differences
from src.extraction.llm_extract import extract_from_passages
from src.extraction.spans import resolve_and_drop
from src.extraction.structured import (became_known_facts, derive_facts,
                                       read_anchor_facts, read_structured_facts)
from src.ingestion.passages import enumerate_passages
from src.llm.client import LLMClient, NullClient
from src.questions.checklist import build_open_questions
from src.synthesis_assembly import assemble
from src.timeline.build import build_timeline


@dataclass
class PipelineRun:
    """The result plus the audit trail the result deliberately excludes.

    Dropped facts do not appear in a SynthesisResult — that is the point of
    drop-if-uncitable. They appear here, so the drop is auditable and so the
    evaluation runner can report a hallucination rate rather than silently
    benefiting from the drop.
    """
    result: SynthesisResult
    dropped_facts: List[Dict[str, Any]] = field(default_factory=list)
    stage_counts: Dict[str, int] = field(default_factory=dict)


def run_pipeline(claim: Claim, llm: Optional[LLMClient] = None) -> PipelineRun:
    llm = llm or NullClient()

    # [1-2] INGEST is done by the loader. ENUMERATE passages by structure_class.
    passages = enumerate_passages(claim)

    # [3] READ + DERIVE — deterministic facts. No model involvement.
    facts = []
    facts.extend(read_structured_facts(claim))
    facts.extend(read_anchor_facts(claim))
    facts.extend(derive_facts(claim))
    facts.extend(became_known_facts(claim))
    deterministic_count = len(facts)

    # [4] EXTRACT — LLM call 1, once per passage.
    extracted = extract_from_passages(claim, passages, llm)
    extracted_count = len(extracted)
    facts.extend(extracted)

    # [8a] Deterministic differences carry their own supporting facts.
    det_facts, det_differences = det_diff.detect(claim)
    facts.extend(det_facts)

    # [5] RESOLVE — the gate. Anything uncitable is dropped, never hedged.
    facts, dropped = resolve_and_drop(facts, claim)
    surviving = {f.fact_id for f in facts}

    # A deterministic difference whose supporting facts were dropped cannot be
    # shown; a difference between facts nobody can check is not evidence.
    det_differences = [
        d for d in det_differences
        if all(p.fact_id in surviving for p in d.positions)
    ]

    # [6] NORMALIZE happened inside extraction and derivation, where the raw
    #     expression is still in hand. Vague stays vague.

    # [7] TIMELINE — arithmetic over normalised dates. No model sorts this.
    timeline = build_timeline(facts)

    # [8b] PROPOSE DIFFERENCES — LLM call 2, over FACTS ONLY (D-020 P4).
    llm_differences = propose_differences(facts, llm)
    llm_differences = [
        d for d in llm_differences
        if all(p.fact_id in surviving for p in d.positions)
    ]
    differences = det_differences + llm_differences

    # [9] OPEN QUESTIONS — deterministic completeness checklist.
    open_questions = build_open_questions(claim)

    # [10] ASSEMBLE — stamp the document set, enforce the invariants.
    result = assemble(
        claim=claim, facts=facts, timeline=timeline, differences=differences,
        open_questions=open_questions,
        model_id=llm.model_id, prompt_version=llm.prompt_version,
        dropped=dropped,
        passages_total=len(passages), passages_processed=len(passages),
    )

    return PipelineRun(
        result=result,
        dropped_facts=dropped,
        stage_counts={
            "passages": len(passages),
            "facts_deterministic": deterministic_count,
            "facts_extracted": extracted_count,
            "facts_dropped": len(dropped),
            "facts_final": len(facts),
            "differences_deterministic": len(det_differences),
            "differences_extracted": len(llm_differences),
            "open_questions": len(open_questions),
        },
    )
