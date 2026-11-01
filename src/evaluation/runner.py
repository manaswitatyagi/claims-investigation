"""E1 evaluation runner.

    python -m src.evaluation.runner --fixture claim_000_smoke --client null
    python -m src.evaluation.runner --fixture claim_000_smoke --client recorded --runs 3
    python -m src.evaluation.runner --all --client live --runs 3

PRD §12.2 requires each fixture to be run at least three times, because
"variance across runs is itself a finding — a capability that works one time in
three is not a capability". `--runs` reports per-metric spread, not just a mean.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from typing import Any, Dict, List, Optional

from src.evaluation.metrics import evaluate, guard_metric_name
from src.ingestion.loader import load_claim, validate_against
from src.llm.client import LLMClient, NullClient, RecordedClient
from src.pipeline import run_pipeline

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_DIR = os.path.join(ROOT, "data", "fixtures")
GOLD_DIR = os.path.join(ROOT, "data", "gold")
OUT_DIR = os.path.join(ROOT, "data", "generated")

#: Reported with spread across runs. Human-rated entries are excluded.
NUMERIC_METRICS = [
    "fact_recall", "fact_precision", "span_exactness", "asserter_accuracy",
    "hallucination_rate", "omission_rate", "timeline_ordering_accuracy",
    "difference_recall", "difference_precision", "open_question_recall",
]
for _m in NUMERIC_METRICS:
    guard_metric_name(_m)


def make_client(kind: str, fixture: str) -> LLMClient:
    if kind == "null":
        return NullClient()
    if kind == "recorded":
        return RecordedClient.from_dir(os.path.join(ROOT, "src", "llm", "recordings", fixture))
    if kind == "live":
        from src.llm.client import LiveClient
        return LiveClient()
    raise SystemExit("unknown client %r (null | recorded | live)" % kind)


def run_once(fixture: str, client_kind: str) -> Dict[str, Any]:
    claim = load_claim(os.path.join(FIXTURE_DIR, fixture, "claim.json"))
    gold_path = os.path.join(GOLD_DIR, fixture + ".gold.json")
    with open(gold_path, "r", encoding="utf-8") as fh:
        gold = json.load(fh)

    gold_errors = validate_against("gold_answer.schema.json", gold)
    if gold_errors:
        raise SystemExit("gold answer %s is invalid:\n  - %s"
                         % (gold_path, "\n  - ".join(gold_errors)))

    run = run_pipeline(claim, make_client(client_kind, fixture))
    result = run.result.to_dict()

    result_errors = validate_against("synthesis_result.schema.json", result)
    if result_errors:
        raise SystemExit("pipeline produced an invalid SynthesisResult:\n  - %s"
                         % "\n  - ".join(result_errors))

    scored = evaluate(result, gold, run.dropped_facts)
    scored["stage_counts"] = run.stage_counts
    scored["dropped_facts"] = run.dropped_facts
    scored["_result"] = result
    return scored


def summarise(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"runs": len(runs)}
    for metric in NUMERIC_METRICS:
        values = [r[metric] for r in runs if r.get(metric) is not None]
        if not values:
            summary[metric] = {"value": None, "note": "undefined (no denominator)"}
            continue
        summary[metric] = {
            "mean": round(statistics.fmean(values), 4),
            "min": min(values),
            "max": max(values),
            "stdev": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0,
        }
    controls = [r["false_differences_on_zero_conflict_control"] for r in runs
                if r["is_zero_conflict_control"]]
    summary["false_differences_on_zero_conflict_control"] = controls or None
    summary["invented_precision_count"] = [r["invented_precision_count"] for r in runs]
    summary["specificity"] = "requires_human_rating"
    summary["open_question_usefulness"] = "requires_human_rating"
    return summary


def decision_rules(summary: Dict[str, Any]) -> List[str]:
    """PRD §12.2, committed before any data was seen."""
    notes = []
    controls = summary.get("false_differences_on_zero_conflict_control")
    if controls and any(c and c > 0 for c in controls):
        notes.append(
            "STOP: false differences on the zero-conflict control > 0. The "
            "extraction-then-generate architecture is not sufficient on its own. "
            "Investigate before anything else — nothing downstream is trustworthy.")
    for key, label in (("span_exactness", "span exactness"),
                       ("asserter_accuracy", "asserter accuracy")):
        entry = summary.get(key) or {}
        if isinstance(entry, dict) and entry.get("mean") is not None and entry["mean"] < 0.8:
            notes.append(
                "STOP-AND-RETHINK: %s is %.2f. Grounding is not achievable at this "
                "level of effort; D-020 P2 would drop most output and the product "
                "does not work. This is not a tuning problem." % (label, entry["mean"]))
    recall = (summary.get("fact_recall") or {}).get("mean")
    precision = (summary.get("fact_precision") or {}).get("mean")
    if recall is not None and precision is not None and recall < 0.7 <= precision:
        notes.append(
            "ACCEPTABLE: fact recall is low but precision holds. D-020 explicitly "
            "accepts lower recall as the price of drop-if-uncitable.")
    if not notes:
        notes.append(
            "No decision rule triggered. Note that passing E1 changes nothing about "
            "D-014's gate: E1 asks whether the machine can do it, the §12 human "
            "study asks whether what it does is worth doing.")
    return notes


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="E1 evaluation runner")
    ap.add_argument("--fixture", help="fixture directory name under data/fixtures")
    ap.add_argument("--all", action="store_true", help="run every fixture")
    ap.add_argument("--client", default="null", choices=["null", "recorded", "live"])
    ap.add_argument("--runs", type=int, default=1,
                    help="PRD §12.2 requires >= 3 for a reportable result")
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args(argv)

    if args.all:
        fixtures = sorted(d for d in os.listdir(FIXTURE_DIR)
                          if os.path.isdir(os.path.join(FIXTURE_DIR, d)))
    elif args.fixture:
        fixtures = [args.fixture]
    else:
        ap.error("give --fixture NAME or --all")

    os.makedirs(args.out, exist_ok=True)
    exit_code = 0

    for fixture in fixtures:
        print("\n" + "=" * 72)
        print("FIXTURE: %s   client=%s   runs=%d" % (fixture, args.client, args.runs))
        print("=" * 72)
        try:
            runs = [run_once(fixture, args.client) for _ in range(args.runs)]
        except Exception as exc:                       # noqa: BLE001 - reported, not swallowed
            print("  SKIPPED: %s: %s" % (type(exc).__name__, exc))
            exit_code = 1
            continue

        summary = summarise(runs)
        last = runs[-1]

        print("\n  stage counts: %s" % json.dumps(last["stage_counts"]))
        print("\n  metrics (no composite score, by design):")
        for metric in NUMERIC_METRICS:
            entry = summary[metric]
            if entry.get("value", "missing") is None:
                print("    %-32s  undefined (no denominator)" % metric)
            else:
                print("    %-32s  mean=%.3f  min=%.3f  max=%.3f  sd=%.3f"
                      % (metric, entry["mean"], entry["min"], entry["max"], entry["stdev"]))
        print("    %-32s  %s" % ("false_diffs_on_zero_control",
                                 summary["false_differences_on_zero_conflict_control"]))
        print("    %-32s  %s" % ("invented_precision_count",
                                 summary["invented_precision_count"]))
        print("    %-32s  %s" % ("specificity", "requires human rating"))
        print("    %-32s  %s" % ("open_question_usefulness", "requires human rating"))

        if last["detail"]["missed_gold_facts"]:
            print("\n  missed gold facts: %s" % ", ".join(last["detail"]["missed_gold_facts"]))
        if last["detail"]["forbidden_hits"]:
            print("  !! FORBIDDEN FACTS EMITTED: %s" % last["detail"]["forbidden_hits"])
        if last["detail"]["spurious_differences"]:
            print("  !! SPURIOUS DIFFERENCES: %s" % last["detail"]["spurious_differences"])

        print("\n  decision rules:")
        for note in decision_rules(summary):
            print("    - %s" % note)

        payload = {"fixture": fixture, "client": args.client, "summary": summary,
                   "runs": [{k: v for k, v in r.items() if k != "_result"} for r in runs],
                   "last_result": last["_result"],
                   "disclaimer": "Scored against an authored synthetic gold answer. "
                                 "Measures what we planted, not real-world performance (D-003)."}
        path = os.path.join(args.out, "%s.eval.json" % fixture)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(path, ROOT))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
