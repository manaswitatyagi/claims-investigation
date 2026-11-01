"""E1b extraction — model supplies the quote, code computes the span.

NOT part of the E1 freeze. `src/extraction/llm_extract.py` is untouched.

Diff against E1, in full:

  E1   Citation.locator = text_span(passage_id, model.char_start, model.char_end)
  E1b  Citation.locator = text_span(passage_id, located.char_start, located.char_end)
       where `located` comes from the deterministic quote locator, and
       Citation.quoted_text is the CANONICAL passage text at those offsets —
       not the string the model typed.

That last point matters. Echoing back the passage's own text means a Citation
can never disagree with its source: the span and the quote are read from the
same place. `resolve_and_drop` still verifies it afterwards, unchanged.

Everything else — the asserter enum, the vague-time handling, the malformed-item
guard, the fact id scheme — is identical to E1.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.claim_model import Asserter, Citation, Claim, Fact, Passage, text_span
from src.extraction.llm_extract import VALID_ASSERTER_KINDS, _speaker_note
from src.extraction.quote_locator import RESOLVED, locate
from src.llm.client import LLMClient
from src.llm.prompts_e1b import EXTRACT_SCHEMA, EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE
from src.normalization.dates import normalise_date


def extract_from_passages(claim: Claim, passages: List[Passage],
                          llm: LLMClient) -> Tuple[List[Fact], List[Dict[str, Any]]]:
    """Returns (facts, unlocatable) — the second list is the locator's audit trail.

    E1's extractor returned facts only, because a bad span survived until
    `resolve_and_drop` caught it. Here a quote that cannot be located never
    becomes a Fact at all, so the reason has to be carried out separately or it
    would be lost.
    """
    from src.ingestion.passages import assert_llm_readable

    facts: List[Fact] = []
    unlocatable: List[Dict[str, Any]] = []
    counter = 0

    for passage in passages:
        doc = claim.document(passage.document_id)
        if doc is not None:
            assert_llm_readable(doc)
        payload = llm.complete_json(
            system=EXTRACT_SYSTEM,
            user=EXTRACT_USER_TEMPLATE.format(
                passage_id=passage.passage_id,
                document_type=doc.type if doc else "unknown",
                document_id=passage.document_id,
                label=passage.label,
                speaker_note=_speaker_note(passage),
                text=passage.text,
            ),
            schema=EXTRACT_SCHEMA,
            tag="extract__%s" % passage.passage_id,
        )

        # Reading-order cursor, used only to break ties between identical quotes.
        cursor = 0
        for item in payload.get("facts", []) or []:
            counter += 1
            fact, note = _to_fact(item, passage, "ex_%03d" % counter, cursor)
            if fact is not None:
                facts.append(fact)
                cursor = fact.citations[0].locator["TextSpan"]["char_end"]
            elif note is not None:
                unlocatable.append(note)

    return facts, unlocatable


def _to_fact(item: Dict[str, Any], passage: Passage, fact_id: str, cursor: int):
    kind = item.get("asserter_kind")
    if kind not in VALID_ASSERTER_KINDS:
        return None, {"fact_id": fact_id, "reason": "invalid_asserter_kind",
                      "assertion": item.get("assertion"), "value": kind}
    if not item.get("assertion") or not item.get("quoted_text"):
        return None, {"fact_id": fact_id, "reason": "missing_assertion_or_quote",
                      "assertion": item.get("assertion")}

    located = locate(passage.text, item["quoted_text"], search_from=cursor)
    if located.status != RESOLVED:
        return None, {
            "fact_id": fact_id,
            "assertion": item.get("assertion"),
            "reason": "quote_not_located",
            "notes": [located.status],
            "passage_id": passage.passage_id,
            "model_quote": item["quoted_text"],
            "occurrences": located.occurrences,
        }

    normalised = None
    raw_time = item.get("raw_time_expression")
    if raw_time:
        normalised = normalise_date(raw_time)

    return Fact(
        fact_id=fact_id,
        assertion=item["assertion"],
        asserter=Asserter(kind=kind, name=item.get("asserter_name")),
        provenance="extracted",
        subject=item.get("subject"),
        normalised_value=normalised,
        citations=[Citation(
            document_id=passage.document_id,
            document_version=passage.document_version,
            locator=text_span(passage.passage_id, located.char_start, located.char_end),
            # The passage's own text, not the model's transcription of it.
            quoted_text=located.canonical_text,
            resolution_note="located_by:%s" % located.method,
        )],
    ), None
