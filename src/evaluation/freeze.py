"""Freeze verification.

`data/generated/E1_FREEZE.json` digests the 22 files that define the experiment.
Runs 1-3 must execute against that exact state; if a digest differs, the runs are
not comparable and the result is void. This module makes that a precondition
rather than a promise, so a live run cannot quietly proceed on a changed setup.

NOT part of the frozen set. Reporting code only.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "data", "generated", "E1_FREEZE.json")


class FreezeViolation(RuntimeError):
    pass


def digest(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def load_manifest(path: str = MANIFEST) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def verify(path: str = MANIFEST) -> Dict[str, Any]:
    """Return a verification record. Raises if anything drifted."""
    manifest = load_manifest(path)
    checked, drifted, missing = [], [], []
    for rel, expected in sorted(manifest["files"].items()):
        if not os.path.exists(os.path.join(ROOT, rel)):
            missing.append(rel)
            continue
        actual = digest(rel)
        checked.append({"file": rel, "expected": expected, "actual": actual,
                        "match": actual == expected})
        if actual != expected:
            drifted.append({"file": rel, "expected": expected, "actual": actual})

    record = {
        "manifest": os.path.relpath(path, ROOT),
        "frozen_at": manifest["frozen_at"],
        "model_id": manifest["model_id"],
        "prompt_version": manifest["prompt_version"],
        "files_checked": len(checked),
        "files_drifted": len(drifted),
        "files_missing": missing,
        "drifted": drifted,
        "verified": not drifted and not missing,
    }
    if not record["verified"]:
        raise FreezeViolation(
            "the frozen setup changed: %d file(s) drifted, %d missing. Runs against a "
            "changed setup are not comparable.\n%s"
            % (len(drifted), len(missing),
               json.dumps(drifted + [{"missing": m} for m in missing], indent=2)))
    return record


def prompt_digests() -> Dict[str, str]:
    from src.llm import prompts
    return {
        "extract_system_sha256_16":
            hashlib.sha256(prompts.EXTRACT_SYSTEM.encode()).hexdigest()[:16],
        "difference_system_sha256_16":
            hashlib.sha256(prompts.DIFFERENCE_SYSTEM.encode()).hexdigest()[:16],
    }
