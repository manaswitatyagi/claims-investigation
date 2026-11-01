"""Stage 1 — INGEST.

Load a claim bundle from disk, validate it against `schemas/claim.schema.json`,
and refuse malformed input rather than degrading gracefully. A pipeline that
accepts a half-valid claim produces a half-valid synthesis and reports nothing
about it.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from src.claim_model import Claim, Document, Passage

SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "schemas",
)

CHECKPOINT_ORDER = {"C1": 1, "C2": 2, "C3": 3, "C4": 4, "C5": 5}


class ClaimValidationError(ValueError):
    pass


def _load_schema(name: str) -> Dict[str, Any]:
    with open(os.path.join(SCHEMA_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _registry() -> Registry:
    """Every local schema, keyed by its `$id`.

    Cross-file `$ref`s are written as absolute `$id` URLs rather than relative
    filenames. Relative refs resolve against whatever scope happens to be on
    the stack, which silently breaks once a ref is reached through another
    ref — absolute ids remove the ambiguity, and nothing is fetched over the
    network.
    """
    resources = []
    for fn in sorted(os.listdir(SCHEMA_DIR)):
        if not fn.endswith(".schema.json"):
            continue
        schema = _load_schema(fn)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load_schema(schema_name)
    return Draft202012Validator(schema, registry=_registry())


def validate_against(schema_name: str, instance: Dict[str, Any]) -> List[str]:
    """Return a list of human-readable validation errors. Empty means valid."""
    v = _validator(schema_name)
    errors = []
    for e in sorted(v.iter_errors(instance), key=lambda x: list(x.path)):
        path = "/".join(str(p) for p in e.path) or "<root>"
        errors.append("%s: %s" % (path, e.message))
    return errors


def load_claim(path: str) -> Claim:
    """Load and validate one claim bundle.

    The bundle may name its documents inline or by relative path under a
    `documents/` directory, so fixtures stay readable as separate files.
    """
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    base_dir = os.path.dirname(os.path.abspath(path))
    raw["documents"] = [_resolve_document(d, base_dir) for d in raw.get("documents", [])]

    # Order matters: a skeleton should report that it is a skeleton, not a type
    # error on the first placeholder the validator happens to reach.
    _check_todo_markers(raw, path)

    errors = validate_against("claim.schema.json", raw)
    if errors:
        raise ClaimValidationError(
            "claim bundle %s failed schema validation:\n  - %s" % (path, "\n  - ".join(errors))
        )

    documents = []
    for d in raw["documents"]:
        passages = [
            Passage(
                passage_id=p["passage_id"],
                document_id=d["document_id"],
                document_version=d["version"],
                label=p["label"],
                text=p["text"],
                speaker_turns=p.get("speaker_turns", []) or [],
            )
            for p in d.get("passages", []) or []
        ]
        documents.append(
            Document(
                document_id=d["document_id"],
                type=d["type"],
                version=d["version"],
                received_date=d["received_date"],
                checkpoint_available=d["checkpoint_available"],
                structure_class=d["structure_class"],
                structured_fields=d.get("structured_fields") or {},
                passages=passages,
            )
        )

    return Claim(
        claim_id=raw["claim_id"],
        checkpoint=raw["checkpoint"],
        provenance=raw["provenance"],
        claim_record=raw["claim_record"],
        documents=documents,
        policy_record=raw.get("policy_record"),
        structured_records=raw.get("structured_records"),
        prior_claims=raw.get("prior_claims", []) or [],
        reserve_history=raw.get("reserve_history", []) or [],
        raw=raw,
    )


def _resolve_document(entry: Any, base_dir: str) -> Dict[str, Any]:
    if isinstance(entry, str):
        with open(os.path.join(base_dir, entry), "r", encoding="utf-8") as fh:
            return json.load(fh)
    if isinstance(entry, dict) and "$file" in entry:
        with open(os.path.join(base_dir, entry["$file"]), "r", encoding="utf-8") as fh:
            return json.load(fh)
    return entry


class FixtureIncompleteError(ClaimValidationError):
    """A fixture still carrying TODO markers cannot be run or scored.

    Claim 001 ships as a skeleton until the real crash anchor is supplied.
    Raising here means a placeholder can never be silently evaluated and
    reported as a result.
    """


def _check_todo_markers(raw: Dict[str, Any], path: str) -> None:
    blob = json.dumps(raw)
    if "__TODO__" in blob:
        raise FixtureIncompleteError(
            "fixture %s still contains __TODO__ placeholders. It is a skeleton, "
            "not a runnable fixture. Supply the anchor data before running or "
            "scoring it." % path
        )


def documents_available_at(claim: Claim) -> List[Document]:
    """D-004 / D-015 — withhold documents that would not yet exist.

    Evaluating against a complete closed file is target leakage: every conflict
    becomes visible at once, which is not how real conflicts arrive.
    """
    limit = CHECKPOINT_ORDER[claim.checkpoint]
    return [d for d in claim.documents
            if CHECKPOINT_ORDER[d.checkpoint_available] <= limit]
