# E1 run 1 — claim_001

model `google/gemini-3.8-flash` · prompts `e1-v2` · synthesis `syn_20c001fb9935`

## Metrics

| metric | value |
| --- | --- |
| fact_recall | 0.5385 |
| fact_precision | 1.0 |
| span_exactness | 0.5 |
| asserter_accuracy | 1.0 |
| hallucination_rate | 0.0 |
| omission_rate | 0.4615 |
| timeline_ordering_accuracy | 1.0 |
| difference_recall | 0.0 |
| difference_precision | None |
| open_question_recall | 1.0 |
| false_differences_on_zero_conflict_control | None |
| invented_precision_count | 0 |

## D-034 credit split

| path | recall | precision |
| --- | --- | --- |
| one-to-one | 0.5192 | 1.0 |
| containment | 0.0192 | 0.0 |
| **total** | **0.5385** | **1.0** |

## Extracted facts

- `ex_001` **vehicle_travel_direction** (claimant) — Their vehicle was traveling northbound on Karlov Avenue at night.
  - span `fnol.description_of_accident` [26:90] 'their vehicle was traveling northbound on Karlov Avenue at night'
- `ex_002` **road_conditions** (claimant) — The road was wet.
  - span `fnol.description_of_accident` [110:126] 'the road was wet'

## Proposed differences

_none_

## Failures by stage

### extraction — 24
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
### grounding — 7
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
### attribution — 0
### normalization — 0
### difference_proposal — 1
- **missed_planted_difference** (confirmed) — A planted difference was not reported.

## Stage counts

```
{
  "passages": 2,
  "facts_deterministic": 25,
  "facts_extracted": 8,
  "facts_dropped": 6,
  "facts_final": 27,
  "differences_deterministic": 0,
  "differences_extracted": 0,
  "open_questions": 2
}
```
