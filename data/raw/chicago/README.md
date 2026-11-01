# Raw anchor data — TODO

**Nothing here yet. This directory is a placeholder.**

`data/fixtures/claim_001/` is authored against one real crash record as its factual
anchor. That record has not been supplied, so the fixture ships as a skeleton and
`load_claim()` raises `FixtureIncompleteError` on any file still containing
`__TODO__`. A placeholder can therefore never be silently evaluated and reported
as a result.

## What is needed

Three structured record sets for **one** crash, plus their provenance:

| File | Contents |
| --- | --- |
| `crashes.csv` (or `.json`) | The single crash row — date, time, location, road/weather/lighting conditions, crash type, contributory cause, number of units |
| `vehicles.csv` | One row per unit involved — make, model, year, travel direction, manoeuvre |
| `people.csv` | One row per person — **role and seating position only** (see the constraint below) |

## Provenance fields to fill in

These go into `data/fixtures/claim_001/claim.json` under `provenance.anchor`, and
into the table below. **No source name, URL, or licence is asserted anywhere in
this repository until it has been verified** — `CLAUDE.md` forbids inventing
datasets, sources, licences, or URLs, and D-001 exists because unsourced claims
harden into premises.

| Field | Value |
| --- | --- |
| Source name | TODO |
| URL | TODO |
| Licence / terms of use | TODO |
| Retrieved at | TODO |
| Crash record identifier | TODO |

## Responsible-AI constraint on using the anchor

Crash datasets are person-level records of real incidents. This project attaches
**invented statements** to the events in them, which is a different act from
analysing them.

The rule for this fixture:

* **Carry across:** crash geometry, timing, road surface, weather, lighting,
  vehicle make/model/year, travel direction, manoeuvre, number of units.
* **Do not carry across:** any person-level attribute — age, sex, injury
  severity coding, or anything else describing a real individual.
* **Invent every party name and identifier**, and never attribute a fabricated
  statement to a real crash participant.

The anchor exists to make the scenario physically plausible. It does not make the
evaluation real-world evidence, and per D-003 the fixture says so in its own
`provenance.disclaimer` rather than only in a research note.
