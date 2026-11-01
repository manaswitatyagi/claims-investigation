"""E1 metrics. PRD §12.2.

Every metric is reported separately. **There is no composite score**, by
design: a single number would hide exactly the failures that matter — a system
with excellent recall and broken asserter attribution would score well and be
unusable.

Two metrics in the PRD table are human-rated (specificity, open-question
usefulness). They are emitted as `requires_human_rating` rather than
approximated, because approximating them would let a vacuous output pass.
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.evaluation.matching import match_differences, match_facts

#: Nothing in this project may score materiality (D-033). The guard below is
#: not decoration: the whole reason E1 is allowed to run ahead of the §12 human
#: study is that it scores none of the materiality-dependent outputs. If a model
#: reproduces materiality labels we authored ourselves, we have measured our own
#: consistency and called it performance — and that failure is invisible from
#: inside the technical work.
FORBIDDEN_METRIC_SUBSTRINGS = ("material", "importance", "severity", "suspicion", "credibility")


class MaterialityScoringAttempt(RuntimeError):
    pass


def guard_metric_name(name: str) -> None:
    low = name.lower()
    for bad in FORBIDDEN_METRIC_SUBSTRINGS:
        if bad in low:
            raise MaterialityScoringAttempt(
                "refusing to compute metric %r. E1 must not score materiality or any "
                "proxy for it (D-033). `materiality_intent` in a gold answer is "
                "metadata for the §12 human study only." % name)


def evaluate(result: Dict[str, Any], gold: Dict[str, Any],
             dropped_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    out_facts = result["facts"]
    gold_facts = gold["expected_facts"]

    fm = match_facts(gold_facts, out_facts)
    matches = fm["matches"]
    co = fm["co_extractions"]

    n_gold = len(gold_facts)
    n_out = len(out_facts)

    # A gold fact is recalled, and an output fact is correct, under EITHER a
    # one-to-one match or a granularity relation (D-034). Counting distinct ids
    # on each side keeps a five-way split from inflating either number.
    gold_hit = ({m["gold"]["match_key"] for m in matches}
                | {c["gold"]["match_key"] for c in co})
    out_hit = ({m["output"]["fact_id"] for m in matches}
               | {c["output"]["fact_id"] for c in co})
    n_matched = len(gold_hit)

    # --- hallucination -----------------------------------------------------
    # Two distinct populations, deliberately not merged: facts that name a
    # must-not-appear item, and facts whose citation did not resolve. The
    # second are already dropped, but they are counted here so the drop rule
    # cannot silently flatter the model.
    forbidden_hits = _forbidden_hits(gold.get("facts_must_not_appear", []), out_facts)
    unresolved_drops = [d for d in dropped_facts if d.get("reason") == "unresolved_citation"]
    fabricated_spans = [d for d in unresolved_drops
                        if "text_absent_from_passage" in (d.get("notes") or [])]

    # --- differences -------------------------------------------------------
    dm = match_differences(gold.get("planted_differences", []),
                           result["differences"], matches, co)

    is_control = bool(gold.get("is_zero_conflict_control"))
    false_on_control = len(result["differences"]) if is_control else None

    # --- timeline ----------------------------------------------------------
    timeline = _timeline_metrics(result["timeline"], gold.get("expected_timeline", []))
    invented = _invented_precision(result, gold)

    # --- open questions ----------------------------------------------------
    oq = _open_question_metrics(result["open_questions"],
                                gold.get("expected_open_questions", []))

    extracted_matches = [m for m in matches if m["gold"]["provenance"] == "extracted"]
    # Span exactness is scored on one-to-one matches only: a sub-assertion has a
    # deliberately narrower span, so asking whether it equals the gold span would
    # score it 0 for being correct. Asserter accuracy DOES include them, because
    # attribution is checkable at any granularity.
    asserter_scored = extracted_matches + [c for c in co
                                           if c["gold"]["provenance"] == "extracted"]

    return {
        "claim_id": result["claim_id"],
        "synthesis_id": result["synthesis_id"],
        "model_id": result["model_id"],
        "prompt_version": result["prompt_version"],
        "is_zero_conflict_control": is_control,

        "fact_recall": _ratio(len(gold_hit), n_gold),
        "fact_precision": _ratio(len(out_hit), n_out),
        "span_exactness": _ratio(sum(1 for m in extracted_matches if m["span_exact"]),
                                 len(extracted_matches)),
        "asserter_accuracy": _ratio(sum(1 for m in asserter_scored if m["asserter_correct"]),
                                    len(asserter_scored)),
        "hallucination_rate": _ratio(len(forbidden_hits) + len(fabricated_spans), max(n_out, 1)),
        "omission_rate": _ratio(len(fm["unmatched_gold"]), n_gold),

        "timeline_ordering_accuracy": timeline["ordering_accuracy"],
        "invented_precision_count": invented["count"],
        "invented_precision_items": invented["items"],

        "difference_recall": _ratio(len(dm["matched"]), len(gold.get("planted_differences", []))),
        "difference_precision": _ratio(len(dm["matched"]), len(result["differences"])),
        "false_differences_on_zero_conflict_control": false_on_control,

        "open_question_recall": oq["recall"],
        "open_question_spurious": oq["spurious"],

        "specificity": "requires_human_rating",
        "open_question_usefulness": "requires_human_rating",

        "counts": {
            "gold_facts": n_gold,
            "output_facts": n_out,
            "matched_facts": n_matched,
            "matched_one_to_one": len(matches),
            "co_extractions": len(co),
            "span_exactness_denominator": len(extracted_matches),
            "unmatched_gold": len(fm["unmatched_gold"]),
            "unmatched_output": len(fm["unmatched_output"]),
            "facts_dropped_by_span_rule": len(dropped_facts),
            "dropped_as_fabricated_span": len(fabricated_spans),
            "dropped_as_offset_drift": sum(
                1 for d in unresolved_drops if "offset_drift" in (d.get("notes") or [])),
            "forbidden_facts_emitted": len(forbidden_hits),
            "differences_output": len(result["differences"]),
            "differences_planted": len(gold.get("planted_differences", [])),
            "differences_spurious": len(dm["spurious"]),
        },
        "detail": {
            "missed_gold_facts": [g["match_key"] for g in fm["unmatched_gold"]],
            "co_extraction_pairs": [
                {"gold": c["gold"]["match_key"], "output": c["output"]["fact_id"],
                 "relation": c["relation"]} for c in co],
            "unmatched_output_facts": [f["fact_id"] for f in fm["unmatched_output"]],
            "forbidden_hits": forbidden_hits,
            "missed_differences": [g["difference_id"] for g in dm["missed"]],
            "spurious_differences": [d["difference_id"] for d in dm["spurious"]],
        },
    }


def _ratio(num: int, den: int):
    if den == 0:
        return None                      # undefined, not 1.0 and not 0.0
    return round(num / den, 4)


#: Removed before comparison. Without this, "the vehicle was PARKED at the time
#: of the impact" and "the vehicle was MOVING at the time of the impact" score
#: as near-identical — the single discriminating word is drowned by shared
#: scaffolding, and the detector fires on the correct answer.
_STOPWORDS = {
    "that", "this", "with", "were", "was", "the", "and", "for", "from", "have",
    "has", "had", "been", "into", "onto", "their", "there", "which", "when",
    "what", "would", "could", "should", "about", "over", "than", "then",
    "they", "them", "some", "such", "only", "also", "each", "any", "all",
}

#: Jaccard, not containment. Containment asks "does the output contain the
#: forbidden assertion's words", which fires on any long fact that happens to
#: mention them — a fact reciting what a document does NOT establish shares most
#: of its vocabulary with the forbidden claim that it DOES. Jaccard asks the
#: question we actually mean: are these two the SAME assertion? A fact that says
#: much more than the forbidden one is not that forbidden one.
FORBIDDEN_JACCARD_THRESHOLD = 0.65


def _forbidden_hits(forbidden: List[Dict[str, Any]],
                    out_facts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Lexical match against the authored must-not-appear assertions.

    A deliberately simple heuristic, with limitations worth stating rather than
    hiding. It will MISS a hallucination paraphrased away from the authored
    wording — which is why `detail.unmatched_output_facts` is also reported, so
    a human can scan what the system produced that gold does not account for.
    And it compares content words only, symmetrically: shared scaffolding must
    not outvote the one word that carries the meaning, in either direction.
    """
    hits = []
    for f in forbidden:
        want = _content_tokens(f["assertion"])
        if not want:
            continue
        for o in out_facts:
            got = _content_tokens(o["assertion"])
            union = want | got
            if not union:
                continue
            if len(want & got) / len(union) >= FORBIDDEN_JACCARD_THRESHOLD:
                hits.append({"forbidden": f["match_key"], "fact_id": o["fact_id"],
                             "assertion": o["assertion"]})
    return hits


def _content_tokens(text: str) -> set:
    return {w for w in _tokens(text) if len(w) > 3 and w not in _STOPWORDS}


def _tokens(text: str) -> List[str]:
    return [w.strip(".,;:'\"()").lower() for w in text.split()]


def _timeline_metrics(timeline: List[Dict[str, Any]],
                      gold_timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ordering accuracy per axis, over events that carry a resolvable date.

    Gold entries sharing an `order` value are ties: either sequence is correct.
    """
    correct = total = 0
    for axis in ("occurred", "became_known"):
        gold_axis = [g for g in gold_timeline
                     if g["axis"] == axis and g.get("when")]
        out_axis = [e for e in timeline
                    if e["axis"] == axis and e["ordering_confidence"] != "unorderable"]
        gold_order = {}
        for g in gold_axis:
            gold_order.setdefault(g["when"], g["order"])
        prev = None
        for e in out_axis:
            when = (e["when"] or {}).get("Date", {}).get("value")
            rank = gold_order.get(when)
            if rank is None:
                continue
            total += 1
            if prev is None or rank >= prev:
                correct += 1
            prev = rank
    return {"ordering_accuracy": _ratio(correct, total)}


def _invented_precision(result: Dict[str, Any], gold: Dict[str, Any]) -> Dict[str, Any]:
    """Directly from DOCMAP §2.2. A vague expression resolved to a timestamp.

    Checked two ways: gold facts flagged must-remain-vague whose output carries
    a value, and any output Date whose precision is vague but whose value is
    non-null (which the model layer already refuses to construct, so a hit here
    means something bypassed it).
    """
    items = []
    vague_keys = {g["label"] for g in gold.get("expected_timeline", [])
                  if g.get("must_remain_vague")}
    for f in result["facts"]:
        nv = f.get("normalised_value") or {}
        d = nv.get("Date")
        if d and d.get("precision") == "vague" and d.get("value") is not None:
            items.append({"fact_id": f["fact_id"], "reason": "vague_with_value"})
    for ev in result["timeline"]:
        d = (ev.get("when") or {}).get("Date") or {}
        if d.get("precision") == "vague" and ev["ordering_confidence"] != "unorderable":
            items.append({"event_id": ev["event_id"], "reason": "vague_but_ordered"})
    return {"count": len(items), "items": items, "expected_vague_labels": sorted(vague_keys)}


def _open_question_metrics(out_questions: List[Dict[str, Any]],
                           gold_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    matched = 0
    for g in gold_questions:
        for o in out_questions:
            if o["kind"] == g["kind"] and _overlaps(g["question"], o["question"]):
                matched += 1
                break
    return {"recall": _ratio(matched, len(gold_questions)),
            "spurious": max(0, len(out_questions) - matched)}


def _overlaps(a: str, b: str) -> bool:
    ta = {w for w in _tokens(a) if len(w) > 3}
    tb = {w for w in _tokens(b) if len(w) > 3}
    if not ta:
        return False
    return len(ta & tb) / len(ta) >= 0.5
