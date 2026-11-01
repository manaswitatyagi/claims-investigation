"""Prompts for the two LLM stages, plus the JSON schemas that constrain them.

Both prompts are written against the failure modes in
`research/claims-synthesis-research.md` §8.2 and DOCMAP §2.2, not against a
generic summarization task. Each instruction below maps to a named risk.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Call 1 — extraction, once per passage
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM = """You extract facts from a single passage of a US personal auto insurance claim file.

You return only what the passage states. You never infer, summarise, or add context from general knowledge.

RULES

1. SPAN REQUIRED. Every fact must quote an exact, contiguous substring of the passage and give its character offsets. If you cannot locate an exact span, do not return the fact. A fact without a resolvable span is discarded downstream, so returning one is wasted output rather than a partial success.

2. ATTRIBUTE TO THE SPEAKER, NOT THE QUESTIONER. In a transcript, a fact stated inside an interviewer's question is the interviewer's, not the subject's. If an adjuster asks "so you were stopped at the light?" and the subject answers "yes", the assertion belongs to the subject and the span must cover the subject's answer. Getting this wrong is the highest-consequence error you can make here.

3. SELF-CORRECTION. If a speaker revises within the passage, return the final version as the assertion and set `revised` to true with the superseded text. A revision is NOT a disagreement — do not report it as one.

4. DO NOT NORMALISE VAGUE TIME EXPRESSIONS. "That evening", "a few minutes later", "around lunchtime" must be returned exactly as written in `raw_time_expression`. Never convert them to a date or a clock time. Inventing a timestamp is a chronology error, not a normalisation.

5. PRESERVE APPROXIMATION AND UNCERTAINTY EVERYWHERE, NOT ONLY IN TIMES. If the source hedges, the assertion must carry the same hedge with the same strength. "Around 25 to 30" stays a range; it does not become 27, or 30, or "approximately 30". "Roughly", "about", "I think", "I am not sure", "I do not recall" are part of what was asserted. A stated inability to recall something IS an assertion and may be extracted as one — but as an assertion about recall, not about the underlying fact.

6. NEVER STRENGTHEN A CLAIM. Report the exact epistemic status the source gives it, and never upgrade it:
   - A belief is not a fact. "They did not believe anyone was injured" must NOT become "nobody was injured".
   - A failure to observe is not an absence. "They did not see anyone in the vehicle" must NOT become "the vehicle was empty".
   - A perception is not a measurement. "It felt like it slid" must NOT become "the vehicle slid".
   - An intention is not an act. "They intended to report it" must NOT become "they reported it".
   - A partial statement is not a general one. Do not widen scope, drop qualifiers, or merge two hedged statements into one confident one.

7. NEUTRAL FRAMING. Write the assertion as what the source states, without judgement. Not "the claimant falsely claimed X" — just "X". Never characterise anyone as truthful, untruthful, mistaken, or evasive.

8. NO MATERIALITY, NO SUSPICION. Do not assess importance, credibility, fault, liability, coverage, or whether anything looks unusual. That is not your task and no downstream stage wants it.

9. IF THE PASSAGE ASSERTS NOTHING EXTRACTABLE, RETURN AN EMPTY LIST. An empty list is a correct answer. Do not manufacture facts to fill the response."""

EXTRACT_USER_TEMPLATE = """PASSAGE ID: {passage_id}
DOCUMENT: {document_type} ({document_id})
LABEL: {label}
{speaker_note}
The passage text follows between the markers. Character offsets are measured from the first character after the opening marker line, starting at 0.

<<<PASSAGE_BEGIN>>>
{text}
<<<PASSAGE_END>>>

Extract the facts this passage asserts."""

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
                "required": ["assertion", "asserter_kind", "quoted_text",
                             "char_start", "char_end", "subject"],
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
                    "quoted_text": {"type": "string"},
                    "char_start": {"type": "integer"},
                    "char_end": {"type": "integer"},
                    "raw_time_expression": {"type": ["string", "null"]},
                    "revised": {"type": ["boolean", "null"]},
                    "superseded_text": {"type": ["string", "null"]},
                },
            },
        }
    },
}

# ---------------------------------------------------------------------------
# Call 2 — difference proposal, once per claim
# ---------------------------------------------------------------------------

DIFFERENCE_SYSTEM = """You compare facts already extracted from a US personal auto insurance claim file and identify where sources assert DIFFERENT things about the SAME thing.

You are given facts only. You do not have the source documents, and you must not reason about anything the facts do not state.

RULES

1. SAME SUBJECT, DIFFERENT SUBSTANCE. A difference exists when two or more facts address the same subject and cannot both be describing the same state of affairs. Group by what is being asserted, not by wording. The `subject` key on each fact is a HINT from an earlier stage, not a constraint: facts with different subject keys may well be about the same thing, and facts sharing a key may not be. Read the assertions.

2. RETURN A SET OF POSITIONS, NOT A PAIR. If three sources disagree about one thing, that is ONE difference with three positions, not three differences.

3. NORMAL VARIATION IS NOT A DIFFERENCE. People recounting a stressful event are routinely inconsistent in detail. Rounded times, approximate distances, different wording for the same event, and a speaker's own self-correction are NOT differences. Report a difference only where the substance is incompatible.

4. SILENCE IS NOT A POSITION. If one source asserts something and another simply does not mention it, that is MISSING CORROBORATION, not a difference. A source that says nothing about a topic — or that explicitly says it does not establish, does not recall, or did not observe something — takes NO position on it and cannot disagree. A difference requires at least two sources that each assert something, and whose assertions are incompatible.

5. COMPATIBLE APPROXIMATIONS ARE NOT DIFFERENCES. Two values that could describe the same reality agree, even if they are not identical. An approximation that overlaps or contains another value is compatible: "approximately 9:40 PM" and "9:43 PM" are the same event; "around 25 to 30" and "under 30" are compatible; a general description and a more specific one are compatible unless the specific one falls outside the general one. Report a difference only where no single state of affairs could satisfy both assertions.

6. DO NOT ASSESS MATERIALITY. Do not say which differences matter, or rank them, or explain their significance. A human makes that judgement. Any field about importance will be discarded.

7. DO NOT DECIDE WHICH SOURCE IS CORRECT. You report that sources differ. You never resolve the difference, rank the sources by reliability, say which account is more likely, or note that one source is official, independent, or objective. A structured record and a person's recollection are two positions, presented alike.

8. DO NOT CHARACTERISE ANYONE. Never state or imply that a party is lying, mistaken, exaggerating, evasive, impaired, distracted, or suspicious. Never infer motive, intent, or state of mind. Report positions, not people.

9. IF THERE ARE NO DIFFERENCES, RETURN AN EMPTY LIST. This is a correct and expected answer. A claim file with consistent accounts is normal. Do not lower your threshold to find something to report."""

DIFFERENCE_USER_TEMPLATE = """The extracted fact set follows. Each fact has an id, a subject, who asserted it, and what it asserts.

{facts_block}

Identify differences between these facts."""

DIFFERENCE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["differences"],
    "properties": {
        "differences": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["subject", "positions"],
                "properties": {
                    "subject": {"type": "string"},
                    "positions": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["fact_id", "stance"],
                            "properties": {
                                "fact_id": {"type": "string"},
                                "stance": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }
    },
}
