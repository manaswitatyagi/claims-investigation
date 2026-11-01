"""Full-fidelity per-run capture, failure classification, and artifact writing.

NOT part of the frozen set. This module observes the frozen pipeline; it never
alters it. Every frozen digest is unchanged by anything here.

Three jobs:

1. **Capture.** `CapturingClient` wraps any `LLMClient` and records both sides of
   every exchange, so the raw model response survives even after the drop rule
   has removed facts from the result. Without it, a fabricated span is visible
   only as an absence.

2. **Classify.** Every failure is assigned to one pipeline stage — extraction,
   grounding, attribution, normalization, difference proposal — and carries the
   evidence that justifies the assignment. A bare category label is not
   reviewable; a label plus the offending span, the passage text at those
   offsets, and the expected value is.

3. **Account for D-034 credit.** Recall and precision are reported split by the
   path that earned them: exact one-to-one matching versus span containment.
   The containment relaxation is a deliberate loosening, so the share of credit
   flowing through it is always on the face of the report.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from src.claim_model import Claim
from src.evaluation.matching import match_differences, match_facts
from src.llm.client import LLMClient

#: Confidence in a classification.
#:   confirmed — mechanically certain from the frozen artefacts.
#:   suspected — heuristic; the evidence is attached so a human can settle it.
CONFIRMED, SUSPECTED = "confirmed", "suspected"

#: Pipeline stages a failure can be attributed to.
#:
#: `runtime_completion` was added after E1: run 1 hit the 16,000-token cap and
#: returned unterminated JSON, and every fact that call would have produced was
#: counted as an extraction omission. That mislabels a budget failure as a model
#: capability failure — the model was not asked and did not decline, it was cut
#: off. Truncation and unparseable output belong to the runtime, not to
#: extraction.
STAGES = ["extraction", "grounding", "attribution", "normalization",
          "difference_proposal", "runtime_completion"]


class CapturingClient(LLMClient):
    """Wraps a client and records request AND response for every call."""

    def __init__(self, inner: LLMClient) -> None:
        self._inner = inner
        self.exchanges: List[Dict[str, Any]] = []

    @property
    def model_id(self):            # type: ignore[override]
        return self._inner.model_id

    @property
    def prompt_version(self):      # type: ignore[override]
        return self._inner.prompt_version

    def complete_json(self, system: str, user: str, schema: Dict[str, Any],
                      tag: str = "") -> Dict[str, Any]:
        response = self._inner.complete_json(system, user, schema, tag=tag)
        self.exchanges.append({
            "tag": tag,
            "request": {"system": system, "user": user, "schema": schema},
            "response": response,
        })
        return response


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------

def classify(claim: Claim, result: Dict[str, Any], gold: Dict[str, Any],
             dropped: List[Dict[str, Any]], metrics: Dict[str, Any],
             runtime: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """One record per failure, each carrying its own evidence.

    `runtime` carries adapter-level diagnostics — parse failures, truncation,
    transport retries. Without it, a completion that was cut off mid-JSON shows
    up as a silent absence of facts.
    """
    failures: List[Dict[str, Any]] = []

    # -- runtime: the call did not complete cleanly ------------------------
    for pf in (runtime or {}).get("parse_failures", []) or []:
        raw = pf.get("raw_text") or ""
        truncated = "Unterminated" in (pf.get("error") or "") or not raw.rstrip().endswith("}")
        failures.append({
            "stage": "runtime_completion",
            "kind": "unparseable_completion_truncated" if truncated
                    else "unparseable_completion",
            "confidence": CONFIRMED,
            "why": ("The model's output was not valid JSON under a strict schema. Facts this "
                    "call would have produced are missing for a RUNTIME reason, not because "
                    "the model failed to extract them. Counting them as extraction omissions "
                    "would blame capability for a budget or transport failure."),
            "evidence": {"tag": pf.get("tag"), "error": pf.get("error"),
                         "raw_length": len(raw), "raw_tail": raw[-240:],
                         "looks_truncated": truncated},
        })
    for meta in (runtime or {}).get("provider_meta", []) or []:
        if (meta or {}).get("finish_reason") in ("length", "MAX_TOKENS"):
            failures.append({
                "stage": "runtime_completion", "kind": "hit_max_tokens",
                "confidence": CONFIRMED,
                "why": "The completion stopped at the token cap rather than at a natural end.",
                "evidence": meta,
            })
    fm = match_facts(gold["expected_facts"], result["facts"])
    by_id = {f["fact_id"]: f for f in result["facts"]}
    passages = {p.passage_id: p.text
                for d in claim.documents for p in d.passages}

    # -- grounding: a citation that did not resolve ------------------------
    for d in dropped:
        note = (d.get("notes") or [None])[0]
        failures.append({
            "stage": "grounding",
            "kind": d.get("reason"),
            "e1b_model_quote": d.get("model_quote"),
            "detail": note,
            "confidence": CONFIRMED,
            "why": _grounding_why(note),
            "evidence": {
                "fact_id": d.get("fact_id"),
                "assertion": d.get("assertion"),
                "all_notes": d.get("notes"),
                "outcome": "dropped before assembly; absent from the result",
            },
        })

    # -- grounding: resolved, but not the span gold names -------------------
    for m in fm["matches"]:
        if m["gold"]["provenance"] != "extracted" or m["span_exact"]:
            continue
        out = m["output"]
        ts = _text_span(out)
        gold_span = m["gold"].get("span") or {}
        failures.append({
            "stage": "grounding",
            "kind": "span_offsets_differ_from_gold",
            "confidence": CONFIRMED,
            "why": ("The citation resolved, so the fact is verifiable, but it does not "
                    "quote the region gold names. A correct fact on the wrong span still "
                    "reads as verified."),
            "evidence": {
                "fact_id": out["fact_id"], "assertion": out["assertion"],
                "gold_match_key": m["gold"]["match_key"],
                "gold_span": gold_span, "output_span": ts,
                "passage_text_at_output_span": _slice(passages, ts),
            },
        })

    # -- attribution --------------------------------------------------------
    for m in fm["matches"] + fm["co_extractions"]:
        if m["gold"]["provenance"] != "extracted" or m.get("asserter_correct"):
            continue
        out = m["output"]
        ts = _text_span(out)
        failures.append({
            "stage": "attribution",
            "kind": "wrong_asserter",
            "confidence": CONFIRMED,
            "why": ("Who asserted a fact often matters more than what was asserted. "
                    "The span resolves, so nothing else in the pipeline catches this."),
            "evidence": {
                "fact_id": out["fact_id"], "assertion": out["assertion"],
                "expected_asserter": m["gold"]["asserter_kind"],
                "actual_asserter": (out.get("asserter") or {}).get("kind"),
                "gold_match_key": m["gold"]["match_key"],
                "output_span": ts,
                "passage_text_at_output_span": _slice(passages, ts),
                "match_path": "one_to_one" if m in fm["matches"] else "containment",
            },
        })

    # -- normalization ------------------------------------------------------
    for item in metrics.get("invented_precision_items", []):
        target = by_id.get(item.get("fact_id"), {})
        failures.append({
            "stage": "normalization",
            "kind": item.get("reason"),
            "confidence": CONFIRMED,
            "why": ("A vague expression was given a specific value or an orderable "
                    "position. Inventing precision on a timeline is a chronology error, "
                    "not a normalisation."),
            "evidence": {
                "fact_id": item.get("fact_id"), "event_id": item.get("event_id"),
                "assertion": target.get("assertion"),
                "normalised_value": target.get("normalised_value"),
            },
        })

    for m in fm["matches"] + fm["co_extractions"]:
        gv = ((m["gold"].get("normalised_value") or {}).get("Date") or {})
        ov = ((m["output"].get("normalised_value") or {}).get("Date") or {})
        if not gv or gv.get("precision") != "vague":
            continue
        if ov.get("precision") == "vague" and ov.get("value") is None:
            continue
        failures.append({
            "stage": "normalization",
            "kind": "must_remain_vague_violated",
            "confidence": CONFIRMED,
            "why": "Gold marks this expression unanchored; the run resolved it.",
            "evidence": {
                "fact_id": m["output"]["fact_id"],
                "gold_match_key": m["gold"]["match_key"],
                "raw_expression": gv.get("raw_expression"),
                "expected": {"precision": "vague", "value": None},
                "actual": ov or m["output"].get("normalised_value"),
            },
        })

    # -- extraction: content that must not appear ---------------------------
    forbidden_by_key = {f["match_key"]: f for f in gold.get("facts_must_not_appear", [])}
    for hit in metrics.get("detail", {}).get("forbidden_hits", []):
        entry = forbidden_by_key.get(hit["forbidden"], {})
        out = by_id.get(hit["fact_id"], {})
        failures.append({
            "stage": "extraction",
            "kind": "forbidden_fact_emitted",
            "confidence": CONFIRMED,
            "why": entry.get("why_absent"),
            "evidence": {
                "fact_id": hit["fact_id"], "assertion": hit["assertion"],
                "forbidden_key": hit["forbidden"],
                "forbidden_assertion": entry.get("assertion"),
                "output_span": _text_span(out),
                "passage_text_at_output_span": _slice(passages, _text_span(out)),
            },
        })

    # -- extraction: unsupported by gold ------------------------------------
    for out in fm["unmatched_output"]:
        if out.get("provenance") != "extracted":
            continue
        ts = _text_span(out)
        failures.append({
            "stage": "extraction",
            "kind": "unmatched_output_fact",
            "confidence": SUSPECTED,
            "why": ("No gold fact matches this and its span lies outside every gold span. "
                    "It is either a genuine false positive or a correct fact gold does not "
                    "account for — the span and passage text are attached so a human can "
                    "decide (D-034)."),
            "evidence": {
                "fact_id": out["fact_id"], "assertion": out["assertion"],
                "subject": out.get("subject"),
                "asserter": (out.get("asserter") or {}).get("kind"),
                "output_span": ts,
                "passage_text_at_output_span": _slice(passages, ts),
            },
        })

    # -- extraction: omission -----------------------------------------------
    # An omission is not always an extraction failure. If the model DID produce
    # the fact and the drop rule removed it for an unresolvable citation, the
    # root cause is grounding and the omission is its consequence. Counting them
    # as two independent failures would double-charge one error and point the
    # reader at the wrong stage.
    for g in fm["unmatched_gold"]:
        upstream = _dropped_counterpart(g, dropped)
        if upstream is not None:
            failures.append({
                "stage": "extraction",
                "kind": "omitted_gold_fact_caused_upstream",
                "confidence": CONFIRMED,
                "why": ("Gold fact absent from the result, but the model produced it and the "
                        "drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see "
                        "the linked grounding failure. The system behaved correctly here: an "
                        "uncitable fact is dropped, never hedged."),
                "evidence": {
                    "gold_match_key": g["match_key"], "assertion": g["assertion"],
                    "provenance": g["provenance"],
                    "root_cause_stage": "grounding",
                    "dropped_fact_id": upstream.get("fact_id"),
                    "dropped_reason": upstream.get("reason"),
                    "dropped_notes": upstream.get("notes"),
                },
            })
            continue
        failures.append({
            "stage": "extraction",
            "kind": "omitted_gold_fact",
            "confidence": CONFIRMED if g["provenance"] == "deterministic" else SUSPECTED,
            "why": ("A gold fact has no counterpart at any granularity, and nothing was "
                    "dropped that carried it."
                    if g["provenance"] == "extracted"
                    else "A deterministic fact is missing; this indicates a code or "
                         "fixture problem, not a model problem."),
            "evidence": {
                "gold_match_key": g["match_key"], "assertion": g["assertion"],
                "provenance": g["provenance"], "expected_asserter": g.get("asserter_kind"),
                "gold_span": g.get("span"),
                "gold_span_text": (g.get("span") or {}).get("quoted_text"),
            },
        })

    # -- difference proposal -------------------------------------------------
    dm = match_differences(gold.get("planted_differences", []), result["differences"],
                           fm["matches"], fm["co_extractions"])
    diffs_by_id = {d["difference_id"]: d for d in result["differences"]}

    for g in dm["missed"]:
        failures.append({
            "stage": "difference_proposal",
            "kind": "missed_planted_difference",
            "confidence": CONFIRMED,
            "why": "A planted difference was not reported.",
            "evidence": {"gold_difference_id": g["difference_id"], "subject": g["subject"],
                         "expected_position_match_keys": g["position_match_keys"],
                         "conflict_pair": g.get("conflict_pair")},
        })

    must_not = gold.get("differences_must_not_be_reported", [])
    for d in dm["spurious"]:
        forbidden = _matching_must_not(d, must_not)
        failures.append({
            "stage": "difference_proposal",
            "kind": ("forbidden_difference_reported" if forbidden
                     else "spurious_difference_reported"),
            "confidence": SUSPECTED,
            "why": (forbidden["why_not"] if forbidden else
                    "Reported a difference gold does not plant. Either a false positive or "
                    "a real difference gold does not account for."),
            "evidence": {
                "difference_id": d["difference_id"], "subject": d["subject"],
                "detection_method": d.get("detection_method"),
                "matched_must_not_subject": (forbidden or {}).get("subject"),
                "positions": [
                    {"fact_id": p["fact_id"], "stance": p["stance"],
                     "asserter": (by_id.get(p["fact_id"], {}).get("asserter") or {}).get("kind"),
                     "span": _text_span(by_id.get(p["fact_id"], {}))}
                    for p in d["positions"]],
            },
        })

    if gold.get("is_zero_conflict_control") and result["differences"]:
        failures.append({
            "stage": "difference_proposal",
            "kind": "false_difference_on_zero_conflict_control",
            "confidence": CONFIRMED,
            "why": ("The control plants no difference. PRD §12.2 decision rule 1: if this "
                    "fires, nothing downstream is trustworthy."),
            "evidence": {"reported": list(diffs_by_id)},
        })

    return failures


def _dropped_counterpart(gold_fact: Dict[str, Any], dropped: List[Dict[str, Any]]):
    """A dropped fact that carried this gold fact's content.

    Matched on the quoted span text, which is what survives in a dropped record.
    """
    quote = (gold_fact.get("span") or {}).get("quoted_text")
    want = {w for w in (quote or "").lower().split() if len(w) > 3}
    if not want:
        return None
    for d in dropped:
        got = {w for w in (d.get("assertion") or "").lower().split() if len(w) > 3}
        if got and len(want & got) / len(want | got) >= 0.5:
            return d
    return None


def _grounding_why(note: Optional[str]) -> str:
    return {
        "text_absent_from_passage":
            "The quoted text does not occur in the passage. The model fabricated the "
            "evidence, not merely the offsets.",
        "quote_ambiguous":
            "The quote occurs more than once and reading order did not leave a single "
            "candidate. Picking one would risk citing the wrong occurrence — identical "
            "text in a question and in an answer have different asserters.",
        "quote_empty": "The model returned an empty quote.",
        "offset_drift":
            "The quoted text is present but the offsets point elsewhere. The model can "
            "nearly cite — a different problem from inventing.",
        "offsets_out_of_range": "Offsets fall outside the passage.",
        "passage_not_found": "The citation names a passage that does not exist.",
        "field_value_mismatch": "The cited field does not hold the quoted value.",
        "field_not_found": "The citation names a field that does not exist.",
        "record_not_found": "The citation names a record that does not exist.",
    }.get(note or "", "The citation did not resolve; the fact was dropped.")


def _matching_must_not(diff: Dict[str, Any], must_not: List[Dict[str, Any]]):
    subject = _norm(diff.get("subject", ""))
    for entry in must_not:
        target = _norm(entry["subject"])
        if subject == target or subject in target or target in subject:
            return entry
    return None


def _norm(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def _text_span(fact: Dict[str, Any]):
    for c in fact.get("citations", []) or []:
        loc = c.get("locator", {})
        if "TextSpan" in loc:
            ts = dict(loc["TextSpan"])
            ts["quoted_text"] = c.get("quoted_text")
            return ts
    return None


def _slice(passages: Dict[str, str], ts) -> Optional[str]:
    """What the passage ACTUALLY holds at the cited offsets.

    This is the single most useful piece of evidence for a grounding failure: it
    shows the reviewer the gap between what was claimed and what is there.
    """
    if not ts:
        return None
    text = passages.get(ts.get("passage_id"))
    if text is None:
        return None
    start, end = ts.get("char_start", 0), ts.get("char_end", 0)
    return text[max(0, start):min(len(text), end)]


# ---------------------------------------------------------------------------
# D-034 credit accounting
# ---------------------------------------------------------------------------

def credit_split(gold: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """How much recall and precision came through containment rather than 1:1.

    The containment relaxation is a deliberate loosening. Reporting the totals
    without this split would hide how much of the score depends on it.
    """
    fm = match_facts(gold["expected_facts"], result["facts"])
    n_gold, n_out = len(gold["expected_facts"]), len(result["facts"])

    gold_1to1 = {m["gold"]["match_key"] for m in fm["matches"]}
    gold_co = {c["gold"]["match_key"] for c in fm["co_extractions"]} - gold_1to1
    out_1to1 = {m["output"]["fact_id"] for m in fm["matches"]}
    out_co = {c["output"]["fact_id"] for c in fm["co_extractions"]} - out_1to1

    def frac(n, d):
        return round(n / d, 4) if d else None

    return {
        "gold_total": n_gold, "output_total": n_out,
        "recall_total": frac(len(gold_1to1 | gold_co), n_gold),
        "recall_via_one_to_one": frac(len(gold_1to1), n_gold),
        "recall_via_containment": frac(len(gold_co), n_gold),
        "precision_total": frac(len(out_1to1 | out_co), n_out),
        "precision_via_one_to_one": frac(len(out_1to1), n_out),
        "precision_via_containment": frac(len(out_co), n_out),
        "co_extraction_pairs": [
            {"gold": c["gold"]["match_key"], "output": c["output"]["fact_id"],
             "relation": c["relation"], "asserter_correct": c["asserter_correct"],
             "gold_span": c["gold"].get("span"),
             "output_span": _text_span(c["output"])}
            for c in fm["co_extractions"]],
        "note": ("Containment credit (D-034) treats a sub-assertion or a covering "
                 "assertion as a match. It is a deliberate loosening: a spurious fact "
                 "whose span happens to fall inside a gold span is credited by it."),
    }


def match_detail(gold: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Every match structure, as full objects rather than id lists."""
    fm = match_facts(gold["expected_facts"], result["facts"])
    dm = match_differences(gold.get("planted_differences", []), result["differences"],
                           fm["matches"], fm["co_extractions"])
    return {
        "one_to_one_matches": [
            {"gold": m["gold"], "output": m["output"], "score": m["score"],
             "span_exact": m["span_exact"], "asserter_correct": m["asserter_correct"]}
            for m in fm["matches"]],
        "co_extractions": fm["co_extractions"],
        "unmatched_gold": fm["unmatched_gold"],
        "unmatched_output": fm["unmatched_output"],
        "differences_matched": dm["matched"],
        "differences_missed": dm["missed"],
        "differences_spurious": dm["spurious"],
    }


# ---------------------------------------------------------------------------
# Corrected difference matching (D-034, second form)
# ---------------------------------------------------------------------------
# `match_differences` in the frozen matcher maps each output fact to ONE gold
# fact. That is wrong whenever a single extracted fact legitimately satisfies
# several gold facts — the mirror of the case D-034 already fixed for recall.
#
# Observed in E1b run 2: the model returned one fact, "the claimant was driving
# the Mercedes-Benz G-Class southbound", whose span covers both `stmt.vehicle`
# and `stmt.direction`. The greedy pass assigned it to `stmt.vehicle`, so the
# planted direction difference — which the model DID report, identically to runs
# 1 and 3 — scored recall 0.0 and precision 0.0.
#
# This lives here rather than in `src/evaluation/matching.py` so both frozen
# manifests stay verifiable. Re-scoring uses captured model output only; no
# request is re-issued, and nothing about either run changes.

def _gold_keys_for_output(fm: Dict[str, Any]) -> Dict[str, set]:
    """One output fact -> EVERY gold fact it satisfies."""
    out: Dict[str, set] = {}
    for m in fm["matches"]:
        out.setdefault(m["output"]["fact_id"], set()).add(m["gold"]["match_key"])
    for c in fm["co_extractions"]:
        out.setdefault(c["output"]["fact_id"], set()).add(c["gold"]["match_key"])
    return out


def rescore_differences(gold: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    fm = match_facts(gold["expected_facts"], result["facts"])
    o2g = _gold_keys_for_output(fm)

    remaining = list(result["differences"])
    matched, missed = [], []
    for g in gold.get("planted_differences", []):
        want = set(g["position_match_keys"])
        found = None
        for o in remaining:
            got: set = set()
            for p in o["positions"]:
                got |= o2g.get(p["fact_id"], set())
            if want.issubset(got):
                found = o
                break
        if found is not None:
            remaining.remove(found)
            matched.append({"gold": g["difference_id"], "output": found["difference_id"]})
        else:
            missed.append(g["difference_id"])

    n_gold = len(gold.get("planted_differences", []))
    n_out = len(result["differences"])
    return {
        "difference_recall": round(len(matched) / n_gold, 4) if n_gold else None,
        "difference_precision": round(len(matched) / n_out, 4) if n_out else None,
        "matched": matched, "missed": missed,
        "spurious": [d["difference_id"] for d in remaining],
    }
