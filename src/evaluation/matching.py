"""Matching output facts to gold facts.

**No LLM-as-judge.** A model judging a model makes the evaluation
non-reproducible and re-introduces exactly the non-determinism PRD §8.2
excludes. Matching is therefore deterministic string and span arithmetic.

The honest cost, stated here rather than buried: this UNDERCOUNTS semantically
correct extractions that are worded differently or span slightly different
text. Fact recall will read low for reasons that are not always the model's
fault. A brittle number we can defend beats a smooth number we cannot.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

#: Minimum character-range overlap (intersection / union) for an extracted fact
#: to count as the same fact as a gold fact. Lenient on boundaries, strict on
#: location — a fact quoting a different part of the passage is a different fact.
SPAN_OVERLAP_THRESHOLD = 0.30

#: Minimum containment (intersection / length of the SHORTER span) for one fact
#: to count as a sub-assertion of another. Resolves D-034.
#:
#: Granularity is a free choice. A sentence like "they do not recall A, B, C, D,
#: or E" can be extracted as one fact or as five, and both are correct. Under
#: strict one-to-one matching the disagreement is punished twice over: if gold
#: authors one and the model returns five, four count as false positives; if
#: gold authors five and the model returns one, four count as omissions. Neither
#: is an extraction error — it is the evaluator imposing a granularity the task
#: never specified.
#:
#: So containment in EITHER direction counts as a match. A fact whose span sits
#: inside a gold fact's span, in the same passage, is a sub-assertion of it; a
#: fact whose span covers several gold spans satisfies all of them. Asserter is
#: deliberately NOT required to agree — attribution is scored on its own metric,
#: and folding it in here would make asserter accuracy circular.
#:
#: The cost, stated plainly: a spurious fact that happens to sit inside a gold
#: span gets credited. `co_extractions` is reported separately so the share of
#: credit coming from this path is always visible.
SPAN_CONTAINMENT_THRESHOLD = 0.90


def span_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    union = max(a_end, b_end) - min(a_start, b_start)
    return (inter / union) if union > 0 else 0.0


def span_containment(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    """Intersection over the SHORTER span. 1.0 when one span sits inside the other."""
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    shorter = min(a_end - a_start, b_end - b_start)
    return (inter / shorter) if shorter > 0 else 0.0


def _text_span(fact: Dict[str, Any]) -> Optional[Tuple[str, int, int]]:
    for c in fact.get("citations", []):
        loc = c.get("locator", {})
        if "TextSpan" in loc:
            ts = loc["TextSpan"]
            return ts["passage_id"], ts["char_start"], ts["char_end"]
    return None


def _field_path(fact: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    for c in fact.get("citations", []):
        loc = c.get("locator", {})
        if "Field" in loc:
            return loc["Field"]["record"], loc["Field"]["field_path"]
    return None


def match_facts(gold_facts: List[Dict[str, Any]],
                output_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Greedy one-to-one matching. Returns matches plus both unmatched sides."""
    remaining = list(output_facts)
    matches: List[Dict[str, Any]] = []
    unmatched_gold: List[Dict[str, Any]] = []

    for g in gold_facts:
        best, best_score = None, 0.0
        for o in remaining:
            score = _score(g, o)
            if score > best_score:
                best, best_score = o, score
        if best is not None and best_score > 0:
            remaining.remove(best)
            matches.append({"gold": g, "output": best, "score": best_score,
                            "asserter_correct": _asserter_ok(g, best),
                            "span_exact": _span_exact(g, best)})
        else:
            unmatched_gold.append(g)

    # Second pass — granularity reconciliation (D-034).
    co_extractions = []
    still_unmatched_output = []
    for out in remaining:
        parent = _containing_partner(out, gold_facts)
        if parent is not None:
            co_extractions.append({"gold": parent, "output": out,
                                   "relation": "output_within_gold",
                                   "asserter_correct": _asserter_ok(parent, out)})
        else:
            still_unmatched_output.append(out)

    covered_gold_keys = {c["gold"]["match_key"] for c in co_extractions}
    still_unmatched_gold = []
    for g in unmatched_gold:
        if g["match_key"] in covered_gold_keys:
            continue
        child = _covering_partner(g, output_facts)
        if child is not None:
            co_extractions.append({"gold": g, "output": child,
                                   "relation": "gold_within_output",
                                   "asserter_correct": _asserter_ok(g, child)})
        else:
            still_unmatched_gold.append(g)

    return {"matches": matches,
            "co_extractions": co_extractions,
            "unmatched_gold": still_unmatched_gold,
            "unmatched_output": still_unmatched_output}


def _containing_partner(out, gold_facts):
    """The gold fact this output fact is a sub-assertion of, if any."""
    ts = _text_span(out)
    if ts is None:
        return None
    passage_id, start, end = ts
    best, best_ratio = None, 0.0
    for g in gold_facts:
        if g["provenance"] != "extracted" or g.get("passage_id") != passage_id:
            continue
        gs = g.get("span")
        if not gs:
            continue
        ratio = span_containment(gs["char_start"], gs["char_end"], start, end)
        if ratio >= SPAN_CONTAINMENT_THRESHOLD and ratio > best_ratio:
            best, best_ratio = g, ratio
    return best


def _covering_partner(gold, output_facts):
    """An output fact whose span covers this gold fact, if any."""
    if gold["provenance"] != "extracted" or not gold.get("span"):
        return None
    gs = gold["span"]
    for out in output_facts:
        ts = _text_span(out)
        if ts is None:
            continue
        passage_id, start, end = ts
        if passage_id != gold.get("passage_id"):
            continue
        if span_containment(gs["char_start"], gs["char_end"], start, end) >= \
                SPAN_CONTAINMENT_THRESHOLD:
            return out
    return None


def _score(gold: Dict[str, Any], out: Dict[str, Any]) -> float:
    """0 means not the same fact. Higher is a better match.

    Subject agreement is necessary for extracted facts: two facts about
    different things are never the same fact, however similar the wording.
    """
    if gold["provenance"] != out.get("provenance"):
        return 0.0

    if gold["provenance"] == "deterministic":
        if gold.get("subject") != out.get("subject"):
            return 0.0
        fp = _field_path(out)
        if gold.get("field_path") and fp and fp[1] == gold["field_path"]:
            return 1.0
        return 0.6                      # right subject, different citation path

    ts = _text_span(out)
    if ts is None or gold.get("span") is None:
        return 0.0
    passage_id, start, end = ts
    if passage_id != gold.get("passage_id"):
        return 0.0
    overlap = span_overlap(gold["span"]["char_start"], gold["span"]["char_end"], start, end)
    if overlap < SPAN_OVERLAP_THRESHOLD:
        return 0.0
    # Subject agreement is a tie-breaker, not a gate: a correct fact given a
    # different subject key is still the same fact, and penalising it here
    # would double-count a labelling difference as an extraction failure.
    return overlap + (0.5 if gold.get("subject") == out.get("subject") else 0.0)


def _asserter_ok(gold: Dict[str, Any], out: Dict[str, Any]) -> bool:
    return gold.get("asserter_kind") == (out.get("asserter") or {}).get("kind")


def _span_exact(gold: Dict[str, Any], out: Dict[str, Any]) -> bool:
    """A correct fact with a wrong span is unverifiable, and looks verified."""
    if gold["provenance"] == "deterministic":
        return True
    ts = _text_span(out)
    if ts is None or gold.get("span") is None:
        return False
    _, start, end = ts
    return start == gold["span"]["char_start"] and end == gold["span"]["char_end"]


def match_differences(gold_differences: List[Dict[str, Any]],
                      output_differences: List[Dict[str, Any]],
                      fact_matches: List[Dict[str, Any]],
                      co_extractions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """A planted difference is found when the output reports a difference whose
    positions resolve to the gold facts that take those positions.

    Matching on *positions* rather than on the subject string matters: a model
    that names the subject differently but points at the right two facts has
    found the difference.
    """
    out_fact_to_gold = {m["output"]["fact_id"]: m["gold"]["match_key"] for m in fact_matches}
    for c in co_extractions or []:
        out_fact_to_gold.setdefault(c["output"]["fact_id"], c["gold"]["match_key"])

    remaining = list(output_differences)
    matched, missed = [], []
    for g in gold_differences:
        want = set(g["position_match_keys"])
        found = None
        for o in remaining:
            got = {out_fact_to_gold.get(p["fact_id"]) for p in o["positions"]}
            got.discard(None)
            if want.issubset(got):
                found = o
                break
        if found is not None:
            remaining.remove(found)
            matched.append({"gold": g, "output": found})
        else:
            missed.append(g)
    return {"matched": matched, "missed": missed, "spurious": remaining}
