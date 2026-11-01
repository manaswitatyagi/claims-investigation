# Live ingestion milestone

Add a `.md`/`.txt` document to Claim 001 and watch the evidence state reconcile.

## Run

```bash
cd "/Users/manaswitatyagi/Documents/Claim Fraud Signal Flagger"
cd web && npm install && npm run build && cd ..     # once
set -a && . ./.env && set +a                        # OPENROUTER_API_KEY
./.venv/bin/python -m src.presentation.server       # http://127.0.0.1:8000
```

Then drop `data/demo/04_witness_statement.md` onto **Add evidence**.
"Reset demo to baseline" restores the E2 state.

## Architecture

```
upload ─► store_document (.md/.txt only)
        ─► to_passages
        ─► LLM extraction        prompts_e2        [same as E2]
        ─► quote_locator                           [same as E1b]
        ─► citation verified, or DROPPED           [D-020 P2, unweakened]
        ─► ontology normalisation, lookup tables   [same as E2]
        ─► admitted to ClaimState
        ─► recompute ONLY affected (entity, event, predicate) keys
        ─► events ─► SSE ─► React
```

No second ingestion architecture. Every stage is the component the experiments used.

**SSE, not WebSockets.** Every message flows server → client; the browser sends
nothing back over the channel, so a duplex protocol would be unused complexity.

**Persistence** is `data/runtime/claim_001/state.json` plus uploaded files.
Seeded once from `data/generated/e2_ontology/run_1/`, which is never written to.
No database, queue, or object store.

## Event contract

`document_received · passages_created · extraction_started · assertion_extracted ·
citation_verified · assertion_dropped · assertion_normalized · neighborhood_updated ·
relationship_changed · processing_complete · processing_failed`

Structured product state only. `make_event` **raises** if a payload key contains
`reasoning`, `thinking`, `chain_of_thought`, `completion`, `raw_response`,
`prompt`, `materiality`, `credibility`, `liability`, `fraud`, or `suspicion`.

Every `relationship_changed` carries: *"Describes the relationship among
assertions only. It does not mean any source is right or wrong."*

## Behaviour that is deliberately not relaxed

| Case | Behaviour |
| --- | --- |
| Quote not found | Dropped. `assertion_dropped`, source becomes `processed_with_dropped_assertions`. |
| Quote ambiguous | Dropped. Guessing an occurrence would misattribute while resolving cleanly. |
| Predicate unmappable | Assertion **kept and shown**, relationship state unresolved. No fake ontology mapping. |
| Extraction throws | `processing_failed`, source marked `failed`, error surfaced on the panel. |

## Demo result (live, 2026-09-07)

5 extracted, 5 verified, 0 dropped, 5 mapped. 26 events.

| Neighbourhood | Before | After |
| --- | --- | --- |
| `travel_direction @ vehicle_1` | CONTRADICTORY (3) | CONTRADICTORY (**4**) — position added, no state change |
| `approximate_speed @ vehicle_1` | single-source (1) | **CONTRADICTORY (2)** — relationship changed |
| `occupant_observation @ vehicle_2` | CORROBORATING (2) | **COMPATIBLE (3)** — relationship changed |
| `road_surface @ roadway_1` | CORROBORATING (3) | CORROBORATING (**4**) — corroboration only |
| `maneuver @ vehicle_1` | CORROBORATING (3) | CORROBORATING (**4**) — corroboration only |

Two of five updated neighbourhoods changed state; three merely gained a source.
That distinction is the point of the milestone, and the UI shows it: only the two
changed neighbourhoods get the `⚠ relationship changed` flag.
