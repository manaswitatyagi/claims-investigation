# E1 run 1 — claim_000_smoke

model `recorded` · prompts `e1-v2` · synthesis `syn_be174f29fca5`

## Metrics

| metric | value |
| --- | --- |
| fact_recall | 0.9655 |
| fact_precision | 1.0 |
| span_exactness | 1.0 |
| asserter_accuracy | 0.9167 |
| hallucination_rate | 0.0357 |
| omission_rate | 0.0345 |
| timeline_ordering_accuracy | 1.0 |
| difference_recall | 1.0 |
| difference_precision | 1.0 |
| open_question_recall | 1.0 |
| false_differences_on_zero_conflict_control | None |
| invented_precision_count | 0 |

## D-034 credit split

| path | recall | precision |
| --- | --- | --- |
| one-to-one | 0.9655 | 1.0 |
| containment | 0.0 | 0.0 |
| **total** | **0.9655** | **1.0** |

## Extracted facts

- `ex_001` **vehicle_state_at_impact** (claimant) — The vehicle was parked at the kerb and unoccupied.
  - span `fnol.description_of_accident` [213:263] 'My car was parked at the kerb and nobody was in it'
- `ex_002` **loss_location_narrative** (claimant) — The vehicle was parked outside the claimant's sister's house on Willow Street.
  - span `fnol.description_of_accident` [0:55] "I had parked outside my sister's house on Willow Street"
- `ex_003` **damage_location** (claimant) — The front nearside of the vehicle was pushed in.
  - span `fnol.description_of_accident` [111:153] 'the front nearside of my car was pushed in'
- `ex_004` **other_vehicle** (claimant) — A silver saloon was stopped further up the road.
  - span `fnol.description_of_accident` [158:211] 'there was a silver saloon stopped further up the road'
- `ex_005` **direction_of_travel** (claimant) — The claimant was heading north towards the junction.
  - span `statement.body` [162:208] 'I was heading north, back towards the junction'
- `ex_006` **speed_at_impact** (claimant) — The claimant was travelling at twenty to twenty-five.
  - span `statement.body` [295:314] 'Twenty, twenty-five'
- `ex_007` **vehicle_state_at_impact** (claimant) — The vehicle was still moving at the time of the impact.
  - span `statement.body` [488:510] 'No, I was still moving'
- `ex_008` **time_of_loss** (claimant) — The loss occurred that evening, after the claimant had eaten.
  - span `statement.body` [623:655] 'That evening, after I had my tea'
- `ex_009` **reporting_delay_reason** (claimant) — The claimant delayed reporting to see whether the other driver would resolve it.
  - span `statement.body` [792:847] 'I wanted to see if the other driver would sort it first'
- `ex_011` **witness_observation** (claimant) — The witness heard the collision from inside number 41.
  - span `independent.body` [0:57] 'I was in my front room at number 41 when I heard the bang'
- `ex_012` **post_impact_position** (witness) — A dark blue hatchback was across the middle of the road with front-end damage.
  - span `independent.body` [84:162] 'a dark blue hatchback across the middle of the road with its front end damaged'
- `ex_014` **witness_observation_limit** (witness) — The witness did not see the collision itself, only the aftermath.
  - span `independent.body` [271:337] 'I did not see the collision itself, only what was there afterwards'

## Proposed differences

- `ddiff_001` **driver_is_a_listed_driver** (deterministic), materiality=None
  - `dd_001` — The driver of record for this loss is Dana Whitfield.
  - `dd_002` — The policy lists Marcus Whitfield as driver(s).
- `d_001` **vehicle_state_at_impact** (extracted), materiality=None
  - `ex_001` — The vehicle was parked at the kerb and unoccupied.
  - `ex_007` — The vehicle was still moving at the time of the impact.

## Failures by stage

### extraction — 1
- **omitted_gold_fact_caused_upstream** (confirmed) — Gold fact absent from the result, but the model produced it and the drop rule removed it. ROOT CAUSE IS GROUNDING, not extraction — see the linked grounding fai
### grounding — 2
- **unresolved_citation** (confirmed) — The quoted text does not occur in the passage. The model fabricated the evidence, not merely the offsets.
- **unresolved_citation** (confirmed) — The quoted text is present but the offsets point elsewhere. The model can nearly cite — a different problem from inventing.
### attribution — 1
- **wrong_asserter** (confirmed) — Who asserted a fact often matters more than what was asserted. The span resolves, so nothing else in the pipeline catches this.
### normalization — 0
### difference_proposal — 0

## Stage counts

```
{
  "passages": 3,
  "facts_deterministic": 14,
  "facts_extracted": 14,
  "facts_dropped": 2,
  "facts_final": 28,
  "differences_deterministic": 1,
  "differences_extracted": 1,
  "open_questions": 1
}
```
