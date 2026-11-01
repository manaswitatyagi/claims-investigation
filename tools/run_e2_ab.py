"""E2 — ontology grouping A/B. Both arms over the SAME verified fact set.

    ./.venv/bin/python tools/run_e2_ab.py --runs 3 --client openrouter

NOT in any freeze. E1 and E1b artifacts are never written to.
"""
from __future__ import annotations

import argparse, datetime, json, os, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.evaluation.metrics import evaluate                                # noqa: E402
from src.evaluation.report import CapturingClient, classify, rescore_differences  # noqa: E402
from src.ingestion.loader import load_claim, validate_against              # noqa: E402
from src.pipeline_e2 import run_pipeline                                   # noqa: E402

OUT = os.path.join(ROOT, "data", "generated", "e2_ontology")


def make_client(kind, model):
    if kind == "null":
        from src.llm.client import NullClient
        return NullClient()
    from src.llm.openrouter_client import OpenRouterClient
    return OpenRouterClient(model=model)


def one_run(fixture, kind, model, n, out_dir):
    claim = load_claim(os.path.join(ROOT, "data", "fixtures", fixture, "claim.json"))
    gold = json.load(open(os.path.join(ROOT, "data", "gold", fixture + ".gold.json")))

    client = CapturingClient(make_client(kind, model))
    t0 = datetime.datetime.now(datetime.timezone.utc)
    run = run_pipeline(claim, client)
    t1 = datetime.datetime.now(datetime.timezone.utc)

    result = run.result.to_dict()
    errs = validate_against("synthesis_result.schema.json", result)
    if errs:
        raise SystemExit("invalid SynthesisResult:\n  - " + "\n  - ".join(errs))

    metrics = evaluate(result, gold, run.dropped_facts)
    metrics.pop("_result", None)
    inner = getattr(client, "_inner", None)
    runtime = {"parse_failures": getattr(inner, "parse_failures", []),
               "provider_meta": [c.get("provider_meta") for c in getattr(inner, "calls", [])],
               "transport_retries": getattr(inner, "transport_retries", 0)}
    failures = classify(claim, result, gold, run.dropped_facts, metrics, runtime)

    # Score BOTH arms against the same gold, with the D-037 many-to-one matcher.
    a_res = dict(result); a_res["differences"] = run.arm_a["differences"]
    b_res = dict(result); b_res["differences"] = run.arm_b["differences"]
    run.arm_a["scored"] = rescore_differences(gold, a_res)
    run.arm_b["scored"] = rescore_differences(gold, b_res)

    d = os.path.join(out_dir, "run_%d" % n)
    os.makedirs(d, exist_ok=True)
    for name, payload in (("result.json", result), ("metrics.json", metrics),
                          ("failures.json", failures), ("dropped.json", run.dropped_facts),
                          ("neighborhoods.json", run.neighborhoods),
                          ("ungrouped.json", run.ungrouped),
                          ("arm_a_flat.json", run.arm_a), ("arm_b_graph.json", run.arm_b),
                          ("exchanges.json", client.exchanges),
                          ("stage_counts.json", run.stage_counts)):
        json.dump(payload, open(os.path.join(d, name), "w"), indent=2)
    usage = [c.get("usage") for c in getattr(inner, "calls", [])]
    json.dump({"run": n, "model": getattr(inner, "model_id", None),
               "wall_seconds": round((t1 - t0).total_seconds(), 2),
               "model_calls": len(client.exchanges), "usage": usage,
               "parse_failures": runtime["parse_failures"],
               "cost": sum(float((u or {}).get("cost", 0) or 0) for u in usage),
               "disclaimer": "Synthetic gold. Measures what we planted (D-003)."},
              open(os.path.join(d, "run_meta.json"), "w"), indent=2)
    return run


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", default="claim_001")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--client", default="openrouter", choices=["openrouter", "null"])
    ap.add_argument("--model", default="google/gemini-3.8-flash")
    a = ap.parse_args(argv)

    os.makedirs(OUT, exist_ok=True)
    runs = []
    for i in range(1, a.runs + 1):
        print("  run %d/%d ..." % (i, a.runs), end="", flush=True)
        r = one_run(a.fixture, a.client, a.model, i, OUT)
        runs.append(r)
        print(" %d facts | %d neighbourhoods (%d compared) | A: %d diffs / 1 call | "
              "B: %d diffs / %d calls"
              % (r.stage_counts["facts_final"], r.stage_counts["neighborhoods"],
                 r.stage_counts["neighborhoods_compared"],
                 len(r.arm_a["differences"]), len(r.arm_b["differences"]),
                 r.arm_b["model_calls"]))
    json.dump({"runs": a.runs, "model": a.model,
               "arm_a": [r.arm_a for r in runs], "arm_b": [r.arm_b for r in runs],
               "stage_counts": [r.stage_counts for r in runs]},
              open(os.path.join(OUT, "ab_summary.json"), "w"), indent=2)
    print("artifacts: %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
