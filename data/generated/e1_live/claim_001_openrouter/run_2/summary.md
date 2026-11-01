# E1 run 2 — claim_001

model `google/gemini-3.8-flash` · prompts `e1-v2` · synthesis `syn_20c001fb9935`

## Metrics

| metric | value |
| --- | --- |
| fact_recall | 0.6923 |
| fact_precision | 1.0 |
| span_exactness | 0.6 |
| asserter_accuracy | 1.0 |
| hallucination_rate | 0.0 |
| omission_rate | 0.3077 |
| timeline_ordering_accuracy | 1.0 |
| difference_recall | 1.0 |
| difference_precision | 1.0 |
| open_question_recall | 1.0 |
| false_differences_on_zero_conflict_control | None |
| invented_precision_count | 0 |

## D-034 credit split

| path | recall | precision |
| --- | --- | --- |
| one-to-one | 0.5769 | 0.9677 |
| containment | 0.1154 | 0.0323 |
| **total** | **0.6923** | **1.0** |

## Extracted facts

- `ex_001` **direction_of_travel** (claimant) — Their vehicle was traveling northbound on Karlov Avenue at night
  - span `fnol.description_of_accident` [26:90] 'their vehicle was traveling northbound on Karlov Avenue at night'
- `ex_002` **road_conditions** (claimant) — The road was wet
  - span `fnol.description_of_accident` [110:126] 'the road was wet'
- `ex_003` **visibility_conditions** (claimant) — Visibility was limited by darkness, although the roadway was illuminated
  - span `fnol.description_of_accident` [131:203] 'visibility was limited by darkness, although the roadway was illuminated'
- `ex_004` **collision_description** (claimant) — The vehicle was turning right when it came into contact with a parked vehicle
  - span `fnol.description_of_accident` [232:309] 'the vehicle was turning right when it came into contact with a parked vehicle'
- `ex_005` **impact_perception** (claimant) — The claimant did not initially realize how significant the contact was
  - span `fnol.description_of_accident` [329:391] 'they did not initially realize how significant the contact was'
- `ex_009` **vehicle_operation** (claimant) — The claimant states they were driving the Mercedes-Benz G-Class southbound and making a right turn at approximately 9:40 PM.
  - span `statement.body` [0:122] 'The claimant says they were driving the Mercedes-Benz G-Class southbound and making a right turn at approximately 9:40 PM.'

## Proposed differences

- `d_001` **direction_of_travel** (extracted), materiality=None
  - `an_008` — The vehicle was traveling northbound.
  - `ex_001` — The vehicle was traveling northbound on Karlov Avenue.
  - `ex_009` — The vehicle was being driven southbound.

## Failures by stage

### extraction — 16
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
- **omitted_gold_fact** (suspected) — A gold fact has no counterpart at any granularity, and nothing was dropped that carried it.
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
### grounding — 13
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
### attribution — 0
### normalization — 0
### difference_proposal — 0

## Stage counts

```
{
  "passages": 2,
  "facts_deterministic": 25,
  "facts_extracted": 17,
  "facts_dropped": 11,
  "facts_final": 31,
  "differences_deterministic": 0,
  "differences_extracted": 1,
  "open_questions": 2
}
```
