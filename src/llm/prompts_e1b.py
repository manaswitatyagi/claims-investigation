"""E1b prompt contract — the model supplies the quote, code computes the offsets.

NOT part of the E1 freeze. `src/llm/prompts.py` is untouched so the E1 baseline
stays reproducible, and this file exists beside it so the two contracts can be
diffed.

CAUSAL ISOLATION
----------------
Exactly two things differ from E1, and both concern *who computes character
offsets*:

  1. `EXTRACT_SYSTEM` rule 1 — asks for a verbatim quote, not offsets.
  2. `EXTRACT_SCHEMA`   — `char_start` / `char_end` removed.

Everything else is imported unchanged: rules 2-9 of the extraction prompt are
byte-identical, the user template is the same object, and the entire difference
stage — system prompt, user template, and schema — is re-exported untouched. If
E1b scores differently, the offset contract is the only candidate cause.

WHY
---
E1 (google/gemini-3.8-flash, 3 runs) dropped 33 of ~40 extracted facts. Every
single drop was `offset_drift`; `text_absent_from_passage` was **zero** across
all three runs. The model quoted the source correctly every time and mis-counted
the character positions, with error accumulating through the passage (0, -4, -4,
-4, -9, -8, -13). Character counting is something code does perfectly and
language models do poorly, and D-020 P2 was dropping correct extractions for a
clerical failure.
"""
from __future__ import annotations

# Re-exported UNCHANGED from the E1 contract. Named imports rather than a
# wildcard so the shared surface is explicit and greppable.
from src.llm.prompts import (  # noqa: F401
    DIFFERENCE_SCHEMA,
    DIFFERENCE_SYSTEM,
    DIFFERENCE_USER_TEMPLATE,
    EXTRACT_USER_TEMPLATE,
)
from src.llm.prompts import EXTRACT_SYSTEM as _E1_EXTRACT_SYSTEM

_E1_RULE_1 = """1. SPAN REQUIRED. Every fact must quote an exact, contiguous substring of the passage and give its character offsets. If you cannot locate an exact span, do not return the fact. A fact without a resolvable span is discarded downstream, so returning one is wasted output rather than a partial success."""

_E1B_RULE_1 = """1. VERBATIM QUOTE REQUIRED. Every fact must quote an exact, contiguous substring of the passage — copied character for character, including punctuation and capitalisation exactly as they appear. Do not paraphrase, tidy, join across a gap, or normalise anything inside the quote. You do NOT need to count character positions: those are computed from your quote by code. What matters is that the quote is copied EXACTLY, and that it is long enough to occur only once in the passage. A quote that cannot be found verbatim is discarded downstream, so an approximate quote is wasted output rather than a partial success."""

assert _E1_RULE_1 in _E1_EXTRACT_SYSTEM, "E1 rule 1 moved; E1b's diff is no longer isolated"

#: Rules 2-9 are byte-identical to E1 by construction.
EXTRACT_SYSTEM = _E1_EXTRACT_SYSTEM.replace(_E1_RULE_1, _E1B_RULE_1, 1)

#: E1's schema minus `char_start` / `char_end`. Every other field, description,
#: and enum is identical.
EXTRACT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["facts"],
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["assertion", "asserter_kind", "quoted_text", "subject"],
                "properties": {
                    "assertion": {"type": "string"},
                    "asserter_kind": {
                        "enum": ["claimant", "insured", "witness", "police_officer",
                                 "adjuster", "provider", "system_record", "attorney"]
                    },
                    "asserter_name": {"type": ["string", "null"]},
                    "subject": {
                        "type": "string",
                        "description": "Short snake_case key for what this fact is about, "
                                       "e.g. vehicle_state_at_impact, direction_of_travel. "
                                       "Facts about the same thing must share a subject."
                    },
                    "quoted_text": {
                        "type": "string",
                        "description": "Verbatim substring of the passage, copied exactly. "
                                       "Character offsets are computed from this by code."
                    },
                    "raw_time_expression": {"type": ["string", "null"]},
                    "revised": {"type": ["boolean", "null"]},
                    "superseded_text": {"type": ["string", "null"]},
                },
            },
        }
    },
}
