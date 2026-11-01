# Claims Handoff Copilot — E1 scaffold

> "Inherit a claim without inheriting the guesswork."

Experiment scaffolding for **E1**, the first technical experiment. **This is not
an application.** There is no UI, no server, no database, and no writeback to any
claim system — see `docs/experiments/E1.md` for what E1 tests and, more
importantly, what it does not.

Product definition is `product/v1-prd.md`. Output contract and domain model are
`data/schema.md`. Decisions are `docs/decision_log.md`. Those documents are the
source of truth; this code implements them and does not extend them.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Python 3.9+. Three dependencies: `jsonschema`, `pytest`, `anthropic`.

## Run

```bash
./.venv/bin/python -m pytest tests/ -q                                    # 100 tests, no network

# the deterministic path alone — seven of the nine stages, no model
./.venv/bin/python -m src.evaluation.runner --fixture claim_000_smoke --client null

# full path against hand-authored recordings — exercises the plumbing
./.venv/bin/python -m src.evaluation.runner --all --client recorded

# the actual experiment (requires ANTHROPIC_API_KEY or `ant auth login`)
./.venv/bin/python -m src.evaluation.runner --all --client live --runs 3
```

## Layout

```
schemas/          7 JSON Schemas: claim, fact, citation, difference,
                  open_question, synthesis_result, gold_answer
src/
  claim_model.py  canonical types
  pipeline.py     the nine stages, in order, once
  llm/            the ONLY non-deterministic code — client, prompts, recordings
  ingestion/ normalization/ extraction/ timeline/ differences/ questions/ evaluation/
data/
  raw/chicago/    anchor data for claim_001 — TODO, not yet supplied
  fixtures/       claim_000_smoke, claim_000_zero_conflict, claim_001 (skeleton)
  gold/           authored expected answers
  generated/      run outputs (gitignored)
tests/            9 files
docs/experiments/E1.md
```

## The four properties this code exists to enforce

Everything else is plumbing. These are the reasons the scaffold is shaped the way
it is, and each is a test, not a comment.

**1. The LLM's surface area is small, and bounded by code.** Four model calls per
run: one extraction per narrative passage, one difference proposal. Date
arithmetic, timeline ordering, counts, structured field reads, coverage checks,
and the completeness checklist are all code — `product/v1-prd.md` §10.4 lists
what a model must never do, and `ingestion/passages.py` raises rather than warns
when a structured document tries to reach one.

**2. Uncitable content is dropped, never hedged.** Every citation must verify
exactly against its source. Failures are removed and recorded in an audit trail;
`resolved: false` never reaches an output. Hedged-but-present content is worse
than absent content, because it looks verified.

**3. Generation never sees a raw document.** The difference stage takes
`List[Fact]` and has no parameter through which a document could reach it. A test
asserts no verbatim run from any passage appears in the outbound payload. This is
the structural defence against the multi-document hallucination rates in
`research/claims-synthesis-research.md` §8.2.

**4. Materiality is never asserted, and cannot be scored by accident.** The
schema types the field `null`, assembly raises if it is populated, and the
evaluation runner refuses any metric name containing `material`, `importance`,
`severity`, `suspicion`, or `credibility` (D-033). A model reproducing labels we
authored ourselves would measure our own consistency and read as performance.

## Standing caveats

**Every fixture is synthetic.** Per D-003, results record *what we planted* and
are not evidence of real-world performance. Each fixture and each evaluation
output states this in the artifact itself.

**No model has been run yet.** There is no E1 result. `--client recorded` uses
hand-authored responses and measures the plumbing.

**D-014's gate is still closed.** E1 asks whether the machine can do it. The §12
human study asks whether what it does is worth doing, and no technical result
substitutes for that.
