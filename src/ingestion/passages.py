"""Stage 2 — ENUMERATE.

Turn available documents into the narrative passages an LLM may read.

`structure_class` routes the pipeline. `data/schema.md` §2.2 states that a
`structured` document reaching an LLM is "a bug the data can expose" — this
module makes that an exception rather than an aspiration.
"""
from __future__ import annotations

from typing import List

from src.claim_model import Claim, Document, Passage
from src.ingestion.loader import documents_available_at


class StructureClassViolation(RuntimeError):
    pass


#: Classes whose text an LLM is permitted to read.
LLM_READABLE = {"structured_with_narrative", "unstructured"}


def enumerate_passages(claim: Claim) -> List[Passage]:
    """Return exactly the passages the extractor may see.

    An FNOL carries ~100 structured fields around one or two free-text boxes.
    Only the boxes become passages; the fields are read deterministically. This
    is the deterministic-first principle made enforceable.
    """
    passages: List[Passage] = []
    for doc in documents_available_at(claim):
        if doc.structure_class == "non_text":
            # Presence is noted; content is not read (PRD §8.1).
            continue
        if doc.structure_class == "structured":
            if doc.passages:
                raise StructureClassViolation(
                    "document %s is structure_class='structured' but carries %d "
                    "passage(s). A structured document must be read by code, "
                    "never by a model." % (doc.document_id, len(doc.passages))
                )
            continue
        if doc.structure_class not in LLM_READABLE:
            raise StructureClassViolation(
                "unknown structure_class %r on %s" % (doc.structure_class, doc.document_id)
            )
        passages.extend(doc.passages)
    return passages


def assert_llm_readable(doc: Document) -> None:
    if doc.structure_class not in LLM_READABLE:
        raise StructureClassViolation(
            "refusing to send %s (structure_class=%s) to an LLM"
            % (doc.document_id, doc.structure_class)
        )
