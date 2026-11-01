# Claim 001 MVP — evidence view

Read-only visual layer over the artifacts E1b and E2 already produced. No upload,
no live ingestion, no auth, no database, no multi-claim workflow.

## Run it

```bash
cd web && npm install && npm run build      # once
./.venv/bin/python -m src.presentation.server
# http://127.0.0.1:8000
```

Frontend development, with the API proxied:

```bash
./.venv/bin/python -m src.presentation.server   # terminal 1
cd web && npm run dev                            # terminal 2
```

## What drives the page

`data/generated/e2_ontology/run_1/` — `neighborhoods.json`, `result.json`,
`ungrouped.json`, `run_meta.json` — plus `data/fixtures/claim_001/` for passage
text. Nothing is recomputed at request time.

## Architecture

```
E2 artifacts ─► src/presentation/view_model.py ─► claim-view/1 DTO
                                                        │
                          src/presentation/server.py ───┤  GET /api/claim/{id}/view
                                                        ▼
                                                   web/ (React + TS)
```

`view_model.py` is the only boundary the UI sees. React never imports `Fact`,
`Difference`, or anything from the evaluation layer, so the pipeline can be
reshaped without touching the screen.

**The UI never infers a relationship.** `relationship` and `rationale` arrive as
data, computed in the domain layer. There is no code path by which the frontend
could decide two assertions disagree — a test asserts every non-singleton
neighbourhood ships with a precomputed relationship.

## Screen

| Region | Contents |
| --- | --- |
| **Sources** | Each contributing source, its type, verification status, verified-assertion count, and how it was processed. Selecting one dims assertions from other sources across the whole map. |
| **Evidence map** | The primary experience. Entity → property, using E2's neighbourhoods. Each card names the property, shows every source's value side by side, and carries a relationship badge. Contradictions open expanded. |
| **Evidence inspector** | Entity, event, predicate, value, asserter, source, the exact quote highlighted in its surrounding passage, passage id, and character offsets. Opening a relationship shows all participating assertions side by side with their evidence and the reason they were compared. |
| **Timeline** | Secondary. Both axes kept distinct. Deterministic — no model orders it, and a vague expression is shown without a position rather than given a false one. |
| **Not assessed / Ungrouped** | What the system declined to judge, and the facts with no entity or property in this claim's vocabulary. |

## Language

The interface says **"Evidence verified"**, never "Fact verified".

> Verified means this assertion was traced to exact text in a source document and
> that citation was checked in code. It does **not** mean the assertion is true.

That sentence ships in the DTO and renders on the page, not in a tooltip.

## Accessibility

Relationship state is never colour alone: every badge carries a glyph (`=` `≈`
`≠` `·`) and a word. Cards are real buttons with `aria-expanded`; the source
filter uses `aria-pressed`; focus is visible throughout.

## Built for the streaming milestone, not implementing it

The DTO is normalised and id-addressable — assertions in one map, neighbourhoods
referencing them by id. Live ingestion becomes an added endpoint emitting patches
against the same `assertion_id` / `neighborhood_id` keys, so the screen updates in
place rather than being rewritten. `/api/health` already reports
`streaming: false` for a client to branch on.
