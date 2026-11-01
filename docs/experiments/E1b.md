# E1b — Deterministic quote location

**Status:** run. 3 live runs, `google/gemini-3.8-flash` via OpenRouter, 2026-09-07.
**Freeze:** `data/generated/E1B_FREEZE_openrouter.json`
**Compares against:** E1, `data/generated/E1_FREEZE_openrouter.json` — untouched.

## Hypothesis

> E1b tests whether deterministic quote location removes the grounding bottleneck observed in E1.

E1 dropped 33 of ~40 extracted facts. **Every drop was `offset_drift`;
`text_absent_from_passage` was zero across all three runs.** The model quoted the
source correctly every time and miscounted character positions, with error
accumulating through the passage (0, −4, −4, −4, −9, −8, −13). D-020 P2 was
discarding correct extractions for a clerical failure.

## The isolated change

```
E1   model returns quote AND char_start/char_end  ->  Citation
E1b  model returns quote  ->  deterministic locator  ->  Citation
```

Two edits, nothing else:

1. Extraction prompt **rule 1 only** — "SPAN REQUIRED" → "VERBATIM QUOTE REQUIRED".
   Rules 2–9 byte-identical; a test asserts exactly one line differs.
2. Extraction schema — `char_start` / `char_end` removed. No other field changed.

Held constant: the difference system prompt, user template, and schema are the
**same Python objects**; fixture, gold, normalization, deterministic facts,
timeline, assembly, and the D-020 P2 drop rule are untouched. `resolve_and_drop`
still verifies every citation, including the ones code just computed — a locator
bug must not be invisible.

`Citation.quoted_text` now holds **the passage's own text** at the located
offsets, not the model's transcription, so a citation cannot disagree with its
source.

## Quote locator

`src/extraction/quote_locator.py`. No fuzzy matching, no edit distance, no
stemming, no semantic similarity.

| Case | Behaviour |
| --- | --- |
| Occurs exactly once | Resolve; offsets computed in code |
| Occurs more than once | Reading-order tie-break **only if it leaves one candidate**; else `quote_ambiguous` → dropped |
| Does not occur | `text_absent_from_passage` → dropped |
| Whitespace differs | Matched in whitespace-normalised space, mapped back to **exact canonical offsets** |
| Case or characters differ | Absent. Case is content, not presentation. |

Ambiguity is dropped rather than guessed because identical text can occur inside
an interviewer's question and inside the answer. Picking wrong yields a citation
that resolves perfectly while pointing at the wrong speaker — D-020 P3's
misattribution failure arriving through the back door.

## Result

| Metric | E1 (model offsets) | E1b (code offsets) |
| --- | --- | --- |
| fact recall | 0.538 / 0.692 / 0.519 | **1.000 / 1.000 / 1.000** |
| omission rate | 0.462 / 0.308 / 0.481 | **0.000 / 0.000 / 0.000** |
| facts dropped | 6 / 11 / 16 | **0 / 0 / 0** |
| extracted facts surviving | 2 / 6 / 1 | **17 / 18 / 17** |
| difference recall (re-scored) | 0 / 1 / 0 | **1 / 1 / 1** |
| fact precision | 1.000 ×3 | 1.000 ×3 |
| asserter accuracy | 1.000 ×3 | 1.000 ×3 |
| hallucination rate | 0.000 ×3 | 0.000 ×3 |
| parse failures | 1 (truncation) | 0 |
| cost | $0.223 | $0.085 |

Grounding stopped being the bottleneck. The planted difference went from found
once in three runs to found in all three, with three positions each — anchor,
FNOL, statement — and no adjudication between them.

## Two measurement notes

**`span_exactness` fell (0.50/0.60/0.00 → 0.31/0.56/0.13) and this is not a
regression.** In E1b every citation resolves by construction, so the metric no
longer measures grounding; it measures whether the model chose the same quote
*boundaries* as the gold author. Example: model quoted "…northbound on Karlov
Avenue at night", gold authored "…northbound on Karlov Avenue". Both are correct
citations. This is a D-034-class granularity artifact and `span_exactness` should
be read as a boundary-agreement statistic under the E1b contract, not a
correctness one.

**Difference recall was under-reported by the scorer.** All three E1b runs
proposed the same three-position direction difference, but run 2 scored 0.0
because one extracted fact — "driving the Mercedes-Benz G-Class **southbound**" —
covers two gold facts, and the frozen matcher maps each output fact to exactly
one. Corrected in `report.rescore_differences` (D-037) and re-scored from
captured output; no request was re-issued. Both as-run and re-scored figures are
reported.

## `runtime_completion`

Added as a sixth failure stage. E1 run 1 hit the 16,000-token cap and returned
unterminated JSON; every fact that call would have produced was counted as an
extraction omission, blaming capability for a budget failure. E1b: zero.
