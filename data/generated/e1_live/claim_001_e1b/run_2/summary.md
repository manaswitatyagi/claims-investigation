# E1 run 2 — claim_001

model `google/gemini-3.8-flash` · prompts `e1-v2` · synthesis `syn_20c001fb9935`

## Metrics

| metric | value |
| --- | --- |
| fact_recall | 1.0 |
| fact_precision | 1.0 |
| span_exactness | 0.5556 |
| asserter_accuracy | 1.0 |
| hallucination_rate | 0.0 |
| omission_rate | 0.0 |
| timeline_ordering_accuracy | 1.0 |
| difference_recall | 0.0 |
| difference_precision | 0.0 |
| open_question_recall | 1.0 |
| false_differences_on_zero_conflict_control | None |
| invented_precision_count | 0 |

## D-034 credit split

| path | recall | precision |
| --- | --- | --- |
| one-to-one | 0.8269 | 1.0 |
| containment | 0.1731 | 0.0 |
| **total** | **1.0** | **1.0** |

## Extracted facts

- `ex_001` **direction_of_travel** (claimant) — The claimant's vehicle was traveling northbound on Karlov Avenue at night.
  - span `fnol.description_of_accident` [26:90] 'their vehicle was traveling northbound on Karlov Avenue at night'
- `ex_002` **road_conditions** (claimant) — The road was wet.
  - span `fnol.description_of_accident` [110:126] 'the road was wet'
- `ex_003` **lighting_and_visibility** (claimant) — Visibility was limited by darkness, although the roadway was illuminated.
  - span `fnol.description_of_accident` [131:203] 'visibility was limited by darkness, although the roadway was illuminated'
- `ex_004` **accident_description** (claimant) — The vehicle was turning right when it came into contact with a parked vehicle.
  - span `fnol.description_of_accident` [232:309] 'the vehicle was turning right when it came into contact with a parked vehicle'
- `ex_005` **awareness_of_impact** (claimant) — The claimant did not initially realize how significant the contact was.
  - span `fnol.description_of_accident` [329:391] 'they did not initially realize how significant the contact was'
- `ex_006` **post_accident_actions** (claimant) — The claimant stopped briefly, looked at the vehicles, and then left because they were concerned about being stranded late at night.
  - span `fnol.description_of_accident` [419:541] 'they stopped briefly, looked at the vehicles, and then left because they were concerned about being stranded late at night'
- `ex_007` **occupants_of_other_vehicle** (claimant) — The claimant did not see anyone inside the parked vehicle.
  - span `fnol.description_of_accident` [561:610] 'they did not see anyone inside the parked vehicle'
- `ex_008` **injuries** (claimant) — The claimant did not believe anyone was injured.
  - span `fnol.description_of_accident` [615:649] 'did not believe anyone was injured'
- `ex_009` **vehicle_movement** (claimant) — The claimant was driving the Mercedes-Benz G-Class southbound and making a right turn at approximately 9:40 PM.
  - span `statement.body` [18:121] 'they were driving the Mercedes-Benz G-Class southbound and making a right turn at approximately 9:40 PM'
- `ex_010` **weather_and_road_conditions** (claimant) — The claimant recalls that it had been raining earlier and that the pavement was wet.
  - span `statement.body` [150:207] 'it had been raining earlier and that the pavement was wet'
- `ex_011` **vehicle_speed** (claimant) — The claimant was driving "around 25 to 30 mph" before beginning the turn.
  - span `statement.body` [218:283] 'they were driving "around 25 to 30 mph" before beginning the turn'
- `ex_012` **vehicle_movement** (claimant) — The turn was normal until the vehicle suddenly slid.
  - span `statement.body` [313:364] 'the turn was normal until the vehicle suddenly slid'
- `ex_013` **collision_description** (claimant) — The claimant tried to correct the vehicle but the front of the Mercedes contacted a parked SUV.
  - span `statement.body` [384:470] 'they tried to correct the vehicle but the front of the Mercedes contacted a parked SUV'
- `ex_014` **other_vehicle_occupancy** (claimant) — The claimant did not see anyone inside the parked SUV.
  - span `statement.body` [491:536] 'they did not see anyone inside the parked SUV'
- `ex_015` **injuries** (claimant) — The claimant did not believe anyone was injured.
  - span `statement.body` [541:575] 'did not believe anyone was injured'
- `ex_016` **post_collision_actions** (claimant) — The claimant stopped after the collision, looked at the vehicles, and then left because they were concerned about being stranded late at night.
  - span `statement.body` [596:730] 'they stopped after the collision, looked at the vehicles, and then left because they were concerned about being stranded late at night'
- `ex_017` **reporting_intention** (claimant) — The claimant intended to report the incident.
  - span `statement.body` [741:777] 'they intended to report the incident'
- `ex_018` **claimant_recollection** (claimant) — The claimant does not recall the exact distance traveled, whether traction control activated, whether another vehicle was nearby, whether there was a witness, or the exact impact location.
  - span `statement.body` [780:968] 'The claimant does not recall the exact distance traveled, whether traction control activated, whether another vehicle was nearby, whether there was a witness, or the exact impact location.'

## Proposed differences

- `d_001` **direction_of_travel** (extracted), materiality=None
  - `an_008` — Unit 1 was traveling north.
  - `ex_001` — The claimant's vehicle was traveling northbound on Karlov Avenue.
  - `ex_009` — The claimant was driving southbound.

## Failures by stage

### extraction — 0
### grounding — 8
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
- **span_offsets_differ_from_gold** (confirmed) — The citation resolved, so the fact is verifiable, but it does not quote the region gold names. A correct fact on the wrong span still reads as verified.
### attribution — 0
### normalization — 0
### difference_proposal — 2
- **missed_planted_difference** (confirmed) — A planted difference was not reported.
- **spurious_difference_reported** (suspected) — Reported a difference gold does not plant. Either a false positive or a real difference gold does not account for.
### runtime_completion — 0

## Stage counts

```
{
  "passages": 2,
  "facts_deterministic": 25,
  "facts_extracted": 18,
  "facts_unlocatable": 0,
  "facts_dropped": 0,
  "facts_final": 43,
  "differences_deterministic": 0,
  "differences_extracted": 1,
  "open_questions": 2
}
```
