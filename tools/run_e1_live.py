"""E1 live baseline driver.

    ./.venv/bin/python tools/run_e1_live.py --fixture claim_001 --runs 3
    ./.venv/bin/python tools/run_e1_live.py --fixture claim_001 --runs 3 --client recorded

Verifies the freeze, executes N independent runs against the frozen pipeline,
and persists EVERYTHING for every run — not just the last.

NOT part of the frozen set. This driver observes; it never alters the pipeline.
It deliberately does not use `src/evaluation/runner.py`'s `main()`, which
summarises runs 1..N-1 and keeps the full result only for the last.

Explicitly absent, per the experiment's terms: no retries for correctness, no
voting, no prompt selection, no per-run configuration change. Runs are
independent samples of one frozen setup.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.evaluation.freeze import prompt_digests, verify                  # noqa: E402
from src.evaluation.metrics import evaluate                               # noqa: E402
from src.evaluation.report import (CapturingClient, classify,             # noqa: E402
                                   credit_split, match_detail)
from src.evaluation.runner import NUMERIC_METRICS                          # noqa: E402
from src.evaluation.runner import make_client as _frozen_make_client       # noqa: E402
from src.ingestion.loader import load_claim, validate_against             # noqa: E402
from src.ingestion.passages import enumerate_passages                     # noqa: E402
from src.pipeline import run_pipeline                                     # noqa: E402

OUT_ROOT = os.path.join(ROOT, "data", "generated", "e1_live")

#: Selected with --openrouter-model. Kept out of the frozen runner so
#: `src/evaluation/runner.py` retains its digest.
OPENROUTER_MODEL = os.environ.get("E1_OPENROUTER_MODEL", "google/gemini-3.8-flash")


VARIANT = "e1"


def _pipeline_for(variant):
    if variant == "e1b":
        from src.pipeline_e1b import run_pipeline as p
        return p
    return run_pipeline


def make_client(kind, fixture):
    if kind != "openrouter":
        return _frozen_make_client(kind, fixture)
    from src.llm.openrouter_client import OpenRouterClient
    return OpenRouterClient(model=OPENROUTER_MODEL)
from src.evaluation.report import STAGES                                   # noqa: E402


def one_run(fixture: str, client_kind: str, run_no: int, out_dir: str) -> dict:
    claim = load_claim(os.path.join(ROOT, "data", "fixtures", fixture, "claim.json"))
    with open(os.path.join(ROOT, "data", "gold", fixture + ".gold.json"), encoding="utf-8") as fh:
        gold = json.load(fh)

    gold_errors = validate_against("gold_answer.schema.json", gold)
    if gold_errors:
        raise SystemExit("gold invalid:\n  - " + "\n  - ".join(gold_errors))

    client = CapturingClient(make_client(client_kind, fixture))
    started = datetime.datetime.now(datetime.timezone.utc)
    pipeline = _pipeline_for(VARIANT)
    run = pipeline(claim, client)
    finished = datetime.datetime.now(datetime.timezone.utc)

    result = run.result.to_dict()
    result_errors = validate_against("synthesis_result.schema.json", result)
    if result_errors:
        raise SystemExit("SynthesisResult invalid:\n  - " + "\n  - ".join(result_errors))

    metrics = evaluate(result, gold, run.dropped_facts)
    metrics.pop("_result", None)
    inner = getattr(client, "_inner", None)
    runtime = {"parse_failures": getattr(inner, "parse_failures", []),
               "provider_meta": [c.get("provider_meta")
                                 for c in getattr(inner, "calls", [])],
               "transport_retries": getattr(inner, "transport_retries", 0)}
    failures = classify(claim, result, gold, run.dropped_facts, metrics, runtime)
    credit = credit_split(gold, result)
    matches = match_detail(gold, result)

    run_dir = os.path.join(out_dir, "run_%d" % run_no)
    os.makedirs(run_dir, exist_ok=True)

    def write(name, payload):
        with open(os.path.join(run_dir, name), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    write("result.json", result)
    write("metrics.json", metrics)
    write("matches.json", matches)
    write("credit_split.json", credit)
    write("failures.json", {"by_stage": {s: [f for f in failures if f["stage"] == s]
                                         for s in STAGES},
                            "totals": {s: sum(1 for f in failures if f["stage"] == s)
                                       for s in STAGES},
                            "all": failures})
    write("dropped.json", run.dropped_facts)
    write("exchanges.json", client.exchanges)
    write("passages.json", [{"passage_id": p.passage_id, "document_id": p.document_id,
                             "label": p.label, "length": len(p.text), "text": p.text}
                            for p in enumerate_passages(claim)])
    write("stage_counts.json", run.stage_counts)
    write("run_meta.json", {
        "run": run_no, "fixture": fixture, "client": client_kind, "variant": VARIANT,
        "model_id": result["model_id"], "prompt_version": result["prompt_version"],
        "synthesis_id": result["synthesis_id"],
        "started_at": started.isoformat(), "finished_at": finished.isoformat(),
        "wall_seconds": round((finished - started).total_seconds(), 2),
        "model_calls": len(client.exchanges),
        "transport_retries": getattr(client._inner, "transport_retries", 0),
        "parse_failures": getattr(client._inner, "parse_failures", []),
        "provider_meta": [c.get("provider_meta")
                          for c in getattr(client._inner, "calls", [])],
        "usage": [c.get("usage") for c in getattr(client._inner, "calls", [])],
        "disclaimer": ("Scored against an authored synthetic gold answer. Measures what we "
                       "planted, not real-world performance (D-003)."),
    })
    _write_summary(run_dir, run_no, result, metrics, credit, failures, run.stage_counts)
    return {"run": run_no, "result": result, "metrics": metrics, "credit": credit,
            "matches": matches, "failures": failures, "dropped": run.dropped_facts,
            "exchanges": client.exchanges, "stage_counts": run.stage_counts}


def _write_summary(run_dir, run_no, result, metrics, credit, failures, counts):
    lines = ["# E1 run %d — %s" % (run_no, result["claim_id"]), "",
             "model `%s` · prompts `%s` · synthesis `%s`"
             % (result["model_id"], result["prompt_version"], result["synthesis_id"]), "",
             "## Metrics", "", "| metric | value |", "| --- | --- |"]
    for m in NUMERIC_METRICS:
        lines.append("| %s | %s |" % (m, metrics.get(m)))
    lines += ["| false_differences_on_zero_conflict_control | %s |"
              % metrics.get("false_differences_on_zero_conflict_control"),
              "| invented_precision_count | %s |" % metrics.get("invented_precision_count"),
              "", "## D-034 credit split", "",
              "| path | recall | precision |", "| --- | --- | --- |",
              "| one-to-one | %s | %s |" % (credit["recall_via_one_to_one"],
                                            credit["precision_via_one_to_one"]),
              "| containment | %s | %s |" % (credit["recall_via_containment"],
                                             credit["precision_via_containment"]),
              "| **total** | **%s** | **%s** |" % (credit["recall_total"],
                                                   credit["precision_total"]),
              "", "## Extracted facts", ""]
    for f in result["facts"]:
        if f["provenance"] != "extracted":
            continue
        c = f["citations"][0]
        ts = c["locator"].get("TextSpan", {})
        lines.append("- `%s` **%s** (%s) — %s" % (f["fact_id"], f.get("subject"),
                                                  f["asserter"]["kind"], f["assertion"]))
        lines.append("  - span `%s` [%s:%s] %r" % (ts.get("passage_id"),
                                                   ts.get("char_start"), ts.get("char_end"),
                                                   c["quoted_text"]))
    lines += ["", "## Proposed differences", ""]
    if not result["differences"]:
        lines.append("_none_")
    for d in result["differences"]:
        lines.append("- `%s` **%s** (%s), materiality=%s"
                     % (d["difference_id"], d["subject"], d["detection_method"],
                        d["materiality"]))
        for p in d["positions"]:
            lines.append("  - `%s` — %s" % (p["fact_id"], p["stance"]))
    lines += ["", "## Failures by stage", ""]
    for stage in STAGES:
        rows = [f for f in failures if f["stage"] == stage]
        lines.append("### %s — %d" % (stage, len(rows)))
        for f in rows:
            lines.append("- **%s** (%s) — %s" % (f["kind"], f["confidence"],
                                                 (f.get("why") or "")[:160]))
    lines += ["", "## Stage counts", "", "```", json.dumps(counts, indent=2), "```", ""]
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def variance(runs) -> dict:
    out = {}
    for m in NUMERIC_METRICS + ["invented_precision_count"]:
        vals = [r["metrics"].get(m) for r in runs]
        present = [v for v in vals if isinstance(v, (int, float))]
        out[m] = {"per_run": vals,
                  "mean": round(statistics.fmean(present), 4) if present else None,
                  "min": min(present) if present else None,
                  "max": max(present) if present else None,
                  "stdev": round(statistics.pstdev(present), 4) if len(present) > 1 else 0.0,
                  "identical_across_runs": len(set(present)) <= 1 if present else None}
    out["failures_by_stage_per_run"] = {
        s: [sum(1 for f in r["failures"] if f["stage"] == s) for r in runs] for s in STAGES}
    out["extracted_fact_count_per_run"] = [
        sum(1 for f in r["result"]["facts"] if f["provenance"] == "extracted") for r in runs]
    out["difference_count_per_run"] = [len(r["result"]["differences"]) for r in runs]
    out["dropped_count_per_run"] = [len(r["dropped"]) for r in runs]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="E1 live baseline driver")
    ap.add_argument("--fixture", default="claim_001")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--client", default="live",
                    choices=["live", "recorded", "null", "openrouter"])
    ap.add_argument("--variant", default="e1", choices=["e1", "e1b"],
                    help="e1 = model computes offsets; e1b = code computes offsets")
    ap.add_argument("--openrouter-model", default=None,
                    help="OpenRouter model slug; default %s" % OPENROUTER_MODEL)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    globals()["VARIANT"] = args.variant
    if args.openrouter_model:
        globals()["OPENROUTER_MODEL"] = args.openrouter_model

    freeze = verify()
    freeze["prompt_digests"] = prompt_digests()
    print("freeze verified: %d files, 0 drift | model=%s prompts=%s"
          % (freeze["files_checked"], freeze["model_id"], freeze["prompt_version"]))

    out_dir = args.out or os.path.join(OUT_ROOT, args.fixture)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "freeze_check.json"), "w", encoding="utf-8") as fh:
        json.dump(freeze, fh, indent=2)

    runs = []
    for i in range(1, args.runs + 1):
        print("  run %d/%d ..." % (i, args.runs), end="", flush=True)
        r = one_run(args.fixture, args.client, i, out_dir)
        runs.append(r)
        print(" %d facts, %d differences, %d dropped, %d failures"
              % (len(r["result"]["facts"]), len(r["result"]["differences"]),
                 len(r["dropped"]), len(r["failures"])))

    v = variance(runs)
    with open(os.path.join(out_dir, "variance.json"), "w", encoding="utf-8") as fh:
        json.dump(v, fh, indent=2)
    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"fixture": args.fixture, "client": args.client, "runs": args.runs,
                   "artifacts_per_run": sorted(os.listdir(os.path.join(out_dir, "run_1"))),
                   "cross_run": ["freeze_check.json", "variance.json", "index.json"]},
                  fh, indent=2)
    print("artifacts: %s" % os.path.relpath(out_dir, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
