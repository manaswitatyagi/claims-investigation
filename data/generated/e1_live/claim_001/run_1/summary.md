# E1 run 1 — claim_001

model `recorded` · prompts `e1-v2` · synthesis `syn_20c001fb9935`

## Metrics

| metric | value |
| --- | --- |
| fact_recall | 1.0 |
| fact_precision | 1.0 |
| span_exactness | 1.0 |
| asserter_accuracy | 1.0 |
| hallucination_rate | 0.0 |
| omission_rate | 0.0 |
| timeline_ordering_accuracy | 1.0 |
| difference_recall | 1.0 |
| difference_precision | 1.0 |
| open_question_recall | 1.0 |
| false_differences_on_zero_conflict_control | None |
| invented_precision_count | 0 |

## D-034 credit split

| path | recall | precision |
| --- | --- | --- |
| one-to-one | 1.0 | 1.0 |
| containment | 0.0 | 0.0 |
| **total** | **1.0** | **1.0** |

## Extracted facts

- `ex_001` **direction_of_travel** (claimant) — The claimant reports the vehicle was travelling northbound on Karlov Avenue.
  - span `fnol.description_of_accident` [26:81] 'their vehicle was traveling northbound on Karlov Avenue'
- `ex_002` **time_of_day** (claimant) — The claimant reports the loss occurred at night.
  - span `fnol.description_of_accident` [82:90] 'at night'
- `ex_003` **road_surface** (claimant) — The claimant says the road was wet.
  - span `fnol.description_of_accident` [110:126] 'the road was wet'
- `ex_004` **visibility** (claimant) — The claimant says visibility was limited by darkness although the roadway was illuminated.
  - span `fnol.description_of_accident` [131:203] 'visibility was limited by darkness, although the roadway was illuminated'
- `ex_005` **vehicle_maneuver** (claimant) — The claimant reports the vehicle was turning right at the time of contact.
  - span `fnol.description_of_accident` [232:261] 'the vehicle was turning right'
- `ex_006` **contact_object** (claimant) — The claimant reports the vehicle came into contact with a parked vehicle.
  - span `fnol.description_of_accident` [270:309] 'came into contact with a parked vehicle'
- `ex_007` **claimant_awareness_of_severity** (claimant) — The claimant says they did not initially realise how significant the contact was.
  - span `fnol.description_of_accident` [329:391] 'they did not initially realize how significant the contact was'
- `ex_008` **post_collision_actions** (claimant) — The claimant states they stopped briefly, looked at the vehicles, and then left.
  - span `fnol.description_of_accident` [419:478] 'they stopped briefly, looked at the vehicles, and then left'
- `ex_009` **reason_for_leaving** (claimant) — The claimant states they left because they were concerned about being stranded late at night.
  - span `fnol.description_of_accident` [479:541] 'because they were concerned about being stranded late at night'
- `ex_010` **occupancy_observation** (claimant) — The claimant says they did not see anyone inside the parked vehicle.
  - span `fnol.description_of_accident` [561:610] 'they did not see anyone inside the parked vehicle'
- `ex_011` **injury_belief** (claimant) — The claimant says they did not believe anyone was injured.
  - span `fnol.description_of_accident` [615:649] 'did not believe anyone was injured'
- `ex_012` **direction_of_travel** (claimant) — The claimant says they were driving southbound.
  - span `statement.body` [62:72] 'southbound'
- `ex_013` **vehicle_identity** (claimant) — The claimant says they were driving the Mercedes-Benz G-Class.
  - span `statement.body` [28:61] 'driving the Mercedes-Benz G-Class'
- `ex_014` **vehicle_maneuver** (claimant) — The claimant says they were making a right turn.
  - span `statement.body` [77:96] 'making a right turn'
- `ex_015` **time_of_loss** (claimant) — The claimant says the loss occurred at approximately 9:40 PM.
  - span `statement.body` [97:121] 'at approximately 9:40 PM'
- `ex_016` **weather_before_loss** (claimant) — The claimant recalls that it had been raining earlier.
  - span `statement.body` [150:177] 'it had been raining earlier'
- `ex_017` **road_surface** (claimant) — The claimant recalls that the pavement was wet.
  - span `statement.body` [187:207] 'the pavement was wet'
- `ex_018` **speed_before_turn** (claimant) — The claimant says they were driving around 25 to 30 mph before beginning the turn.
  - span `statement.body` [218:283] 'they were driving "around 25 to 30 mph" before beginning the turn'
- `ex_019` **vehicle_slid** (claimant) — The claimant says the turn was normal until the vehicle suddenly slid.
  - span `statement.body` [313:364] 'the turn was normal until the vehicle suddenly slid'
- `ex_020` **correction_attempt** (claimant) — The claimant says they tried to correct the vehicle.
  - span `statement.body` [384:417] 'they tried to correct the vehicle'
- `ex_021` **contact_configuration** (claimant) — The claimant says the front of the Mercedes contacted a parked SUV.
  - span `statement.body` [422:470] 'the front of the Mercedes contacted a parked SUV'
- `ex_022` **occupancy_observation** (claimant) — The claimant says they did not see anyone inside the parked SUV.
  - span `statement.body` [491:536] 'they did not see anyone inside the parked SUV'
- `ex_023` **injury_belief** (claimant) — The claimant says they did not believe anyone was injured.
  - span `statement.body` [541:575] 'did not believe anyone was injured'
- `ex_024` **post_collision_actions** (claimant) — The claimant says they stopped after the collision, looked at the vehicles, and then left.
  - span `statement.body` [596:667] 'they stopped after the collision, looked at the vehicles, and then left'
- `ex_025` **reason_for_leaving** (claimant) — The claimant says they left because they were concerned about being stranded late at night.
  - span `statement.body` [668:730] 'because they were concerned about being stranded late at night'
- `ex_026` **reporting_intention** (claimant) — The claimant says they intended to report the incident.
  - span `statement.body` [741:777] 'they intended to report the incident'
- `ex_027` **claimant_non_recall** (claimant) — The claimant says they do not recall the exact distance travelled, whether traction control activated, whether another vehicle was nearby, whether there was a witness, or the exact impact location.
  - span `statement.body` [780:967] 'The claimant does not recall the exact distance traveled, whether traction control activated, whether another vehicle was nearby, whether there was a witness, or the exact impact location'

## Proposed differences

- `d_001` **direction_of_travel** (extracted), materiality=None
  - `ex_001` — The FNOL records the vehicle as travelling northbound on Karlov Avenue.
  - `ex_012` — The recorded statement has the claimant driving southbound.

## Failures by stage

### extraction — 0
### grounding — 0
### attribution — 0
### normalization — 0
### difference_proposal — 0

## Stage counts

```
{
  "passages": 2,
  "facts_deterministic": 25,
  "facts_extracted": 27,
  "facts_dropped": 0,
  "facts_final": 52,
  "differences_deterministic": 0,
  "differences_extracted": 1,
  "open_questions": 2
}
```
