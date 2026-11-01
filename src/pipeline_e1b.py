"""E1b pipeline — identical to `src/pipeline.py` except for the extraction stage.

NOT part of the E1 freeze. This is a deliberate near-copy rather than a
parameter on `run_pipeline`, because `src/pipeline.py` is frozen and adding a
hook would change its digest and break E1's reproducibility.

The divergence is stages [4] and [5] and nothing else. Diff the two files: every
other line is the same call in the same order, against the same frozen modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.claim_model import Claim, SynthesisResult
from src.differences import deterministic as det_diff
from src.differences.llm_propose import propose_differences
from src.extraction.llm_extract_e1b import extract_from_passages       # <-- the change
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
    result: SynthesisResult
    dropped_facts: List[Dict[str, Any]] = field(default_factory=list)
    stage_counts: Dict[str, int] = field(default_factory=dict)


def run_pipeline(claim: Claim, llm: Optional[LLMClient] = None) -> PipelineRun:
    llm = llm or NullClient()

    passages = enumerate_passages(claim)

    facts = []
    facts.extend(read_structured_facts(claim))
    facts.extend(read_anchor_facts(claim))
    facts.extend(derive_facts(claim))
    facts.extend(became_known_facts(claim))
    deterministic_count = len(facts)

    # [4] EXTRACT — LLM supplies quotes; code locates them.
    # [5a] LOCATE — an unlocatable quote never becomes a Fact. Its reason is
    #      carried out separately so the drop stays auditable, exactly as an
    #      unresolved citation is in E1.
    extracted, unlocatable = extract_from_passages(claim, passages, llm)
    extracted_count = len(extracted)
    facts.extend(extracted)

    det_facts, det_differences = det_diff.detect(claim)
    facts.extend(det_facts)

    # [5b] RESOLVE — unchanged. Verifies every citation, including the ones code
    #      just computed. Code checking its own arithmetic is cheap, and a
    #      locator bug would otherwise be invisible.
    facts, dropped = resolve_and_drop(facts, claim)
    dropped = list(unlocatable) + dropped
    surviving = {f.fact_id for f in facts}

    det_differences = [d for d in det_differences
                       if all(p.fact_id in surviving for p in d.positions)]

    timeline = build_timeline(facts)

    llm_differences = propose_differences(facts, llm)
    llm_differences = [d for d in llm_differences
                       if all(p.fact_id in surviving for p in d.positions)]
    differences = det_differences + llm_differences

    open_questions = build_open_questions(claim)

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
            "facts_unlocatable": len(unlocatable),
            "facts_dropped": len(dropped),
            "facts_final": len(facts),
            "differences_deterministic": len(det_differences),
            "differences_extracted": len(llm_differences),
            "open_questions": len(open_questions),
        },
    )
