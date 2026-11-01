# Claims Handoff Copilot

> "Inherit a claim without inheriting the guesswork."

An adjuster inheriting a contested, long-lived personal auto claim should be able
to reach a defensible account of it without re-reading the file from scratch.
This repository holds the research, the domain model, three technical
experiments, and a small demo UI that reads their output.

**This is not a product, and the decision to build one has not been made.**
D-014's gate is closed: no application code ships until the practitioner study in
`research/claims-synthesis-research.md` §12 has run. The demo exists to make the
experiment output inspectable by a human, not to be used on a real claim.

Product definition is `product/v1-prd.md`. Output contract and domain model are
`data/schema.md`. Decisions and their reasoning are `docs/decision_log.md`. Those
documents are the source of truth; this code implements them and does not extend
them.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Python 3.9+. Three dependencies: `jsonschema`, `pytest`, `anthropic`. The
OpenRouter adapter used for the live runs is stdlib `urllib` and adds nothing.

## Run the experiments

```bash
./.venv/bin/python -m pytest tests/ -q                                    # 211 tests, no network

# the deterministic path alone — seven of the nine stages, no model
./.venv/bin/python -m src.evaluation.runner --fixture claim_000_smoke --client null

# full path against hand-authored recordings — exercises the plumbing
./.venv/bin/python -m src.evaluation.runner --all --client recorded

# live. needs OPENROUTER_API_KEY in .env (see .env.example)
./.venv/bin/python tools/run_e1_live.py --client openrouter --runs 3
./.venv/bin/python tools/run_e2_ab.py   --client openrouter --runs 3
```

## The demo

Two hosted versions, because they can do different things.

| | GitHub Pages | Streamlit |
| --- | --- | --- |
| Read the claim, graph, timeline, spans | yes | yes |
| **Add a document and watch it reconcile** | no | **yes** |
| Needs an API key | no | yes |
| Cost per visit | zero | a model call per ingest |

**Hosted, read-only:** https://manaswitatyagi.github.io/claims-investigation/

Same app, built with `VITE_STATIC=1` so it reads a baked snapshot of the
`claim-view/1` DTO instead of calling the Python API — every panel is a
projection of that one contract, so a file serves them as well as a process
does. The `/api` path is dead-code-eliminated, and CI fails the build if it
survives. Adding a document is disabled there: ingestion runs the real
extraction and quote-location pipeline, and mocking it would mean showing
assertions whose spans were never resolved.

**Hosted, with live ingestion — Streamlit.** `streamlit_app.py` is a Python view
over the same `src/runtime/ingest.process_document` the local server calls, so a
visitor can drop a `.md` or `.txt` file and watch the real pipeline run:
extraction, quote location in code, ontology normalisation, neighbourhood
recompute. Assertions whose quote cannot be found in the uploaded text are
really dropped.

```bash
./.venv/bin/streamlit run streamlit_app.py           # http://localhost:8501
```

To deploy on [share.streamlit.io](https://share.streamlit.io): point it at this
repo, main branch, `streamlit_app.py`, Python 3.9+, then **App settings →
Secrets**:

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
```

Without the secret the app still runs and only ingestion is disabled, with the
reason on screen. Two things worth knowing before sharing that link: anyone who
opens it can spend the key, so the app allows **one upload per session** and
caps files at **40 KB**; and each session gets its own claim id, hence its own
runtime directory, lock and event bus — Streamlit Cloud shares one filesystem
across viewers, so without that a stranger's upload would appear in your session.

**Locally, with ingestion and the React UI:**

```bash
cd web && npm install && npm run build && cd ..     # emits src/presentation/static
./.venv/bin/python -m src.presentation.server        # http://127.0.0.1:8000
```

Sources, an evidence map grouped by assertion neighbourhood, a **graph view**
(entity → property → source, deterministic layout), an inspector showing each
assertion against its exact source span, and a two-axis timeline. Dropping a
`.md` or `.txt` file in re-runs the affected neighbourhoods and streams the
updated view over SSE.

To refresh the hosted snapshot after an experiment re-run:

```bash
./.venv/bin/python tools/build_static_snapshot.py    # -> web/public/claim-view.json
```

It is committed rather than generated in CI, so the hosted numbers cannot move
without a commit saying so.

State lives in `data/runtime/` (gitignored). On first run it self-seeds from the
committed E2 run at `data/generated/e2_ontology/run_1`, so a fresh clone works
with no experiment re-run. Delete the directory to reset.

**"Evidence verified" is the strongest thing the UI says, and it means the quoted
text was found at that offset in that document — not that the assertion is true.**
A verified citation on a false statement by a claimant is a correct output.

## Layout

```
schemas/          7 JSON Schemas: claim, fact, citation, difference,
                  open_question, synthesis_result, gold_answer
src/
  claim_model.py  canonical types
  pipeline.py     the nine stages, in order, once
  llm/            the ONLY non-deterministic code — clients, prompts, recordings
  ontology/       26 controlled predicates, value normalisation (E2)
  runtime/        live ingestion, claim state, SSE event stream
  presentation/   the claim-view/1 DTO and the view server
  ingestion/ normalization/ extraction/ timeline/ differences/ questions/ evaluation/
web/              React + Vite UI; consumes the DTO and derives nothing from it
data/
  fixtures/       claim_000_smoke, claim_000_zero_conflict, claim_001
  gold/           authored expected answers
  generated/      run outputs and freeze manifests — COMMITTED, deliberately
tests/            16 files, 211 tests
docs/experiments/ E1.md, E1b.md, E2.md
```

`data/generated/` is committed because the freeze manifests are what make "E1b
changed exactly one thing" checkable, and the decision log cites run artifacts as
evidence. Ignoring them would leave every experiment claim unverifiable.

## What the experiments found

**E1 — grounding, with the model reporting character offsets.** Fact recall
0.52–0.69, and 33 of ~40 extracted facts discarded. Every single drop was
`offset_drift`; `text_absent_from_passage` was zero across all three runs. The
model was quoting faithfully and counting characters badly. The failure was
clerical, not cognitive.

**E1b — the model returns the quote, code computes the offsets.** One rule in one
prompt changed. Fact recall 0.52–0.69 → **1.000 ×3**, facts dropped 6/11/16 →
**0**, surviving facts 2/6/1 → **17/18/17**, planted-difference recall 1-of-3
runs → **3-of-3**, cost $0.223 → $0.085. Grounding stopped being the bottleneck.

**E2 — does an evidence graph earn its complexity? No.** A controlled
`(entity, event, predicate, value)` ontology was tested against a flat baseline.
The neighbourhood arm used 8–9 model calls against 1 and more total input, for
**identical** difference recall (1.00 ×3) and zero false positives in both arms.
Recommendation recorded: **do not build the graph layer.** What the ontology did
buy was stable grouping keys (32/32 across runs), corroboration becoming
expressible at all (0 → 7–9 per run), and three category errors prevented
structurally rather than by prompt instruction.

## The four properties this code exists to enforce

Everything else is plumbing. These are the reasons the scaffold is shaped the way
it is, and each is a test, not a comment.

**1. The LLM's surface area is small, and bounded by code.** Two call sites, and
seven of the nine pipeline stages never reach them. Date arithmetic, timeline
ordering, counts, structured field reads, coverage checks, and the completeness
checklist are all code — `product/v1-prd.md` §10.4 lists what a model must never
do, and `ingestion/passages.py` raises rather than warns when a structured
document tries to reach one.

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

**The live runs are not an Anthropic baseline.** They routed through OpenRouter to
`google/gemini-3.8-flash`. The original freeze pinned a different provider and
model, so these runs change two variables at once and are reported as a separate
experiment, never as that baseline.

**No claims professional has been consulted.** Zero. The primary user, the claim
segment, and the premise that experienced adjusters agree on what counts as a
material difference are all untested assumptions.

**The time-savings premise is unmeasured.** No public study measures how personal
auto adjusters allocate their time. The figure that dominates this space traces
to an unattributed vendor blog and is barred from this project (D-021).

**D-014's gate is still closed.** The experiments ask whether the machine can do
it. The §12 human study asks whether what it does is worth doing, and no
technical result substitutes for that.
