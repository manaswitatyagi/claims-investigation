"""Stage 8b — PROPOSE DIFFERENCES. LLM call 2, once per claim.

D-020 P4 is enforced structurally: this function takes `List[Fact]` and has no
parameter through which a Document or Passage could reach it. The model cannot
fabricate from a source it cannot see.

`tests/test_llm_boundary.py` asserts that no passage text appears in the
outbound payload — the invariant is checked, not merely intended.
"""
from __future__ import annotations

from typing import List

from src.claim_model import Difference, Fact, Position
from src.llm.client import LLMClient
from src.llm.prompts import (DIFFERENCE_SCHEMA, DIFFERENCE_SYSTEM,
                             DIFFERENCE_USER_TEMPLATE)


def propose_differences(facts: List[Fact], llm: LLMClient) -> List[Difference]:
    if not facts:
        return []

    by_id = {f.fact_id: f for f in facts}
    payload = llm.complete_json(
        system=DIFFERENCE_SYSTEM,
        user=DIFFERENCE_USER_TEMPLATE.format(facts_block=render_facts(facts)),
        schema=DIFFERENCE_SCHEMA,
        tag="differences",
    )

    out: List[Difference] = []
    for i, item in enumerate(payload.get("differences", []) or [], start=1):
        positions = [
            Position(fact_id=p["fact_id"], stance=p["stance"])
            for p in item.get("positions", []) or []
            if p.get("fact_id") in by_id       # a position citing an unknown fact
        ]                                      # is dropped, not invented into being
        if len(positions) < 2:
            continue
        out.append(Difference(
            difference_id="d_%03d" % i,
            subject=item.get("subject") or "unspecified",
            positions=positions,
            detection_method="extracted",
        ))
    return out


def render_facts(facts: List[Fact]) -> str:
    """Serialise the fact set for the model.

    Deliberately renders assertion, asserter, and subject — and NOT
    `quoted_text`, which is source text. Keeping quotes out is what makes the
    no-raw-documents invariant testable rather than approximate.
    """
    lines = []
    for f in facts:
        who = f.asserter.kind
        if f.asserter.name:
            who = "%s (%s)" % (f.asserter.name, f.asserter.kind)
        lines.append("- id=%s | subject=%s | asserted_by=%s | %s"
                     % (f.fact_id, f.subject or "unspecified", who, f.assertion))
    return "\n".join(lines)
