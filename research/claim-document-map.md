# Claim Document Map — US Personal Auto

**Status:** Phase 2 discovery. Companion to `research/claims-synthesis-research.md`.
**Date:** 2026-08-07
**Scope:** Core personal auto claim file **plus** the injury/casualty layer, per the scoping decision recorded in `docs/decision_log.md` D-018.

## Purpose

This map answers three questions the product needs before any data model exists:

1. **What is actually in a personal auto claim file**, who makes it, and when does it appear?
2. **How structured is each document**, so we know what deterministic code can handle and what genuinely needs an LLM (`CLAUDE.md`'s deterministic-first principle).
3. **Which documents can contradict which**, because that — not the document inventory — is what the synthetic dataset must be built around.

## Tags and conventions

Same evidence tags as the research documents (D-001). Two additional columns need definition:

**Availability checkpoint** — from `claims-synthesis-research.md` §6:

| Code | Checkpoint | Rough timing |
| --- | --- | --- |
| **C1** | FNOL | Day 0 |
| **C2** | Coverage verified, claim assigned | Days 1–5 |
| **C3** | Claimant/insured statement taken | Days 5–30 |
| **C4** | Supporting documents arriving | Days 15–90+ |
| **C5** | Pre-settlement / demand | Days 90–440+ |

No document appears in this map without a checkpoint. Decision **D-004** requires the evaluation set to be timestamped, and this map is where the timestamps come from.

**Conflict-bearing** — whether the document can materially disagree with another document about the same fact. This is the column that matters most for V1.

---

# 1. Master table

## 1.1 Core auto layer

| Document | What it contains | Who creates it | Available | Structure | What the adjuster extracts | Synthesis value | Conflict-bearing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **FNOL / loss notice** (ACORD Automobile Loss Notice or carrier equivalent) | ~100+ structured fields plus a free-text "Description of Accident" | Intake rep, agent, claimant via app/web, sometimes telematics | **C1** | **Semi-structured**: fields + 1–2 narrative boxes | Loss date/time/location, parties, vehicles, injuries alleged, police report existence and number, first account of what happened | **High** — the anchor account everything else is compared against | **Yes** — the primary baseline for every later account |
| **Policy record / declarations** | Inception, renewal, expiry; coverages, limits, deductibles, endorsements; listed and excluded drivers; scheduled vehicles (VIN, year/make/model); garaging address; premium and lapse history | Policy administration system | **C1** | **Structured** | Coverage in force on DOL, applicable coverages and limits, whether driver is listed, whether vehicle is scheduled | **Medium** — sets the coverage frame; needs no extraction | **Yes** — against stated driver and stated garaging/usage |
| **Prior claims history** (internal + ISO ClaimSearch) | Prior claims by insured, vehicle, party; cross-carrier matches | Claims system; Verisk ClaimSearch | **C1–C2** | **Structured** | Count, recency, type similarity, recurring parties/vehicles | **Medium** — mostly deterministic counts | **Yes** — prior damage vs. currently claimed damage |
| **Coverage position / reservation of rights** | Which coverages apply, any conditions or exclusions asserted, ROR language | Adjuster, sometimes coverage counsel | **C2** | **Semi-structured** formal letter | The position taken and its stated basis | **Medium** | Rarely |
| **Adjuster notes / diary / activity log** | Terse, abbreviated, jargon-heavy chronological entries: calls, decisions, impressions, follow-ups | Adjuster | **C2 onward, continuous** | **Unstructured**, heavily abbreviated | What the handler already knows, believes, and has tried; what is pending | **Very high** — the closest thing to a predecessor's working memory | **Yes** — notes often record a discrepancy the handler spotted |
| **Recorded statement transcript** | Long, conversational, disfluent, non-linear account, usually with timestamps | Transcription of adjuster interview with claimant/insured/witness | **C3** | **Unstructured**, long | Detailed sequence of events, positions of vehicles and people, injuries, activity before and after | **Very high** — the richest narrative and the first that can disagree with the FNOL | **Yes — highest-value pair with FNOL** |
| **Police / traffic collision report** | State-specific structured form (parties, vehicles, citations, conditions, contributing factors) + officer narrative + scene diagram | Law enforcement | **C3** (often delayed weeks) | **Mixed**: structured form + narrative + diagram; **format varies by state** | Independent account, citations issued, contributing-factor coding, diagram of impact | **Very high** — the only genuinely independent account of the loss | **Yes — highest-value pair with the recorded statement** |
| **Witness statements** | Third-party accounts, recorded or written | Adjuster, or witness directly | **C3–C4**, often absent | **Unstructured** | Corroboration or contradiction of party accounts | **High when present** | **Yes** |
| **Repair estimate + supplements** | Line-item parts, labour operations, paint, betterment, damage locations by panel | Staff or independent appraiser, or repair shop; produced in CCC / Mitchell / Audatex | **C4** | **Highly structured** line items | Damage location and severity, repair cost, whether damage matches described mechanism | **High** — the physical evidence check | **Yes** — damage location vs. narrative mechanism |
| **Photographs** | Vehicle damage, scene, documents; sometimes EXIF/timestamps | Claimant (app), appraiser, tow yard, police | **C1 (partial) – C4** | **Unstructured / binary** | Visible damage, corroboration of described impact | **Medium** — out of scope for a text-first V1 | **Yes**, but not text-comparable |
| **Total-loss valuation report** | Comparable-vehicle valuation, condition adjustments, ACV | Valuation vendor (CCC, Mitchell) | **C4**, when applicable | **Structured** | ACV, whether repair exceeds threshold | **Low** for synthesis | No |
| **Correspondence** (email, letters, portal messages) | Requests, follow-ups, claimant complaints, shop and attorney communication | All parties | **C2 onward, continuous** | **Unstructured** | Outstanding requests, commitments made, dates promised | **High for open questions** — this is where "we asked for X and never got it" lives | Sometimes |
| **Proof of loss** | Sworn statement of the loss and amount claimed | Claimant | **C4**, where required | **Structured** sworn form | Claimed amounts, sworn assertions | **Medium** — sworn status raises the weight of any conflict | **Yes**, and materially — it is sworn |
| **Reserve and payment history** | Reserve amounts and revisions, payments issued, payees, dates | Claims system / adjuster | **C2 onward** | **Structured** | Current exposure, what has been paid, when severity assessment changed | **Medium** — reserve *changes* are a strong timeline signal of when the handler's view shifted | No |
| **Rental / towing / storage invoices** | Dates, vendors, amounts | Vendors | **C4** | **Structured** | Dates of vehicle possession and drivability | **Low individually; useful for timeline corroboration** | Occasionally — dates vs. stated drivability |

## 1.2 Injury / casualty layer

| Document | What it contains | Who creates it | Available | Structure | What the adjuster extracts | Synthesis value | Conflict-bearing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Medical records** | Clinical narrative, history, examination findings, diagnoses, treatment plan, progress notes | Treating providers | **C4–C5**, continuous, high volume | **Semi-structured**: ICD/CPT codes + clinical prose | Injury type and severity, onset timing, treatment course, prior conditions, causation statements | **High but volume-dominated** — this is the incumbents' territory | **Yes** — injury onset and mechanism vs. the claimant's account |
| **Medical bills** | CPT-coded line items, dates of service, providers, charges | Providers / billing companies | **C4–C5** | **Structured** | Specials total, treatment duration, provider mix, gaps in treatment | **Medium** — mostly deterministic aggregation | Occasionally — billed dates vs. records |
| **IME report** | Independent examining physician's findings, causation and permanency opinions | Insurer-retained physician | **C5** | **Unstructured** clinical narrative with conclusions | An opposing clinical opinion | **High** | **Yes** — by design, it exists to test the treating opinion |
| **Peer review / medical audit** | Records reviewed against necessity and relatedness standards | Physician or nurse reviewer | **C5** | **Unstructured** with structured findings | Which treatment is related and necessary | **High** | **Yes** |
| **Wage-loss documentation** | Employer wage statement, pay records, disability notes | Employer, claimant, provider | **C4–C5** | **Structured** | Lost time, wage rate, claimed lost earnings | **Medium** | **Yes** — claimed disability period vs. treatment records |
| **Demand package** | Attorney's assembled narrative, liability argument, specials summary, records, settlement demand | Claimant's attorney | **C5** | **Unstructured**, argumentative, with structured attachments | The opposing account and valuation | **Very high** — a competing synthesis of the same file | **Yes — the most consequential conflicts appear here** |
| **EUO transcript** | Sworn, stenographically transcribed examination compelled under the policy | Stenographer, at insurer's request | **C5**, rare | **Unstructured**, long, **sworn** | Sworn answers to targeted questions | **High** | **Yes**, and at the highest evidentiary weight |
| **Litigation documents** | Complaint, answer, discovery responses, deposition transcripts | Counsel on both sides | **C5**, when suit is filed | **Unstructured** formal | Pleaded facts, sworn testimony | **High** | **Yes** |

---

# 2. Per-document notes that matter for extraction

## 2.1 FNOL — mostly fields, not prose

**[INDUSTRY]** The ACORD Automobile Loss Notice is a standardised form. Its sections cover agency and carrier identifiers; policy number and effective dates; named insured and contact details; **date, time, and location of loss**; **"Description of Accident"** free text with ACORD 101 (Additional Remarks Schedule) attachable for overflow; **"Police or Fire Department Contacted"** with the authority name and **report number**; insured vehicle (year/make/model, VIN, plate) and its damage description; driver details including licence and relationship to insured; other vehicles, their owners, drivers, insurers, and damage; injured parties; property damaged; **witnesses**; and additional items such as child-restraint questions. Carrier-specific FNOL forms vary but capture materially the same field set.

**[INFERENCE]** The product implication is significant and easy to get wrong. **The narrative content of an FNOL is one or two free-text boxes surrounded by roughly a hundred structured fields.** Almost everything the product needs from an FNOL — dates, parties, vehicles, whether police attended, report number, alleged injuries — should be read from fields, not extracted by a model. Treating the FNOL as an unstructured document to parse is avoidable work, avoidable error, and a direct violation of `CLAUDE.md`'s deterministic-first principle.

The LLM's job on an FNOL is exactly one thing: extract facts with spans from the Description of Accident box.

## 2.2 Recorded statement — the hardest text in the file

**[INDUSTRY]** Unsworn, taken by the adjuster, transcribed. Long, conversational, disfluent, and non-linear: people backtrack, self-correct, answer a different question than asked, and give times as "around lunchtime."

**[INFERENCE]** Three extraction problems specific to this document type, all of which need testing before any architecture is settled (uncertainty U-2 in the research doc):

- **Speaker attribution.** A transcript alternates adjuster and claimant. A fact asserted by the adjuster in a leading question ("so you were stopped at the light?") is not the claimant's assertion, and conflating them would be exactly the misattribution failure that grounding principle P3 exists to prevent.
- **Self-correction.** When a speaker revises within one statement, the final version is the assertion — but the revision itself may be what an adjuster wants to see. Both need representing, and neither is a conflict with the other.
- **Vague temporal expressions.** "A few minutes later," "that evening." These cannot be normalised to timestamps without inventing precision, and inventing precision on a timeline is exactly the incorrect-chronology risk.

## 2.3 Police report — structured, independent, and state-specific

**[INDUSTRY]** A state traffic collision report combines a structured form (parties, vehicles, insurance, citations, road and weather conditions, coded contributing factors, injury severity coding), an **officer's narrative**, and a **scene diagram**. Format, field names, and coding schemes vary by state — Pennsylvania's Police Officers Crash Report Manual (PennDOT Publication 153) is an example of the state-level specification these follow.

**[INFERENCE]** Two things make this document disproportionately valuable and disproportionately awkward.

Valuable: it is the **only genuinely independent account** in a typical file. Everything else is written by a party to the claim or by someone they hired. A conflict between a claimant's statement and a police narrative carries far more weight than a conflict between an FNOL and a statement given by the same person.

Awkward: state variation means field-level extraction does not generalise across jurisdictions, and the diagram — often the clearest statement of impact geometry — is not text. **A V1 that handles police reports properly is implicitly committing to a jurisdiction** (open decision D-006), or to narrative-only extraction that discards the structured half.

## 2.4 Adjuster notes — the predecessor's working memory

**[INDUSTRY]** Terse, abbreviated, jargon-heavy, chronological, written for an audience of one. Documentation practice holds that everything material must be logged, that notes should stay factual, and that subjective observations should appear only as direct quotes.

**[INFERENCE]** For a handoff-focused product this is arguably the highest-value document in the file, and the most under-appreciated. It is the only place recording *what the previous handler thought and tried* — which is precisely what a successor loses. It is also where a discrepancy the predecessor already noticed will be written down, meaning the conflict-detection feature must reconcile its own findings against conflicts the human already logged, or it will confidently re-report something the file already resolved.

Two cautions. Notes are the hardest text in the file to parse reliably — carrier-specific abbreviations, no grammar, no consistent structure. And they are **discoverable**, which cuts both ways: the product reads material written under litigation constraints, and anything it writes back joins that record.

## 2.5 Repair estimate — structured, and the physical-evidence check

**[INDUSTRY]** Produced in CCC, Mitchell, or Audatex as line items: part numbers, labour operations and hours, paint, betterment, with damage located by panel.

**[INFERENCE]** No LLM should read an estimate for its numbers — it is a structured document and the totals are arithmetic. Its synthesis value is one specific comparison: **the damage locations in the estimate against the impact mechanism described in the narratives.** A rear-impact account with left-side damage is a conflict a human catches only by holding two documents together. Day 1 §E.3 flagged this as plausible but unproven for an LLM, and it stays unproven.

## 2.6 Demand package — a competing synthesis

**[INDUSTRY]** The claimant attorney's assembled liability argument, specials summary, supporting records, and settlement demand.

**[INFERENCE]** Worth calling out because it is structurally unlike everything else in the file: it is *itself* a synthesis of the same underlying documents, written adversarially. The most consequential conflicts in a represented claim are between the demand's account and the file's own record. It also sets a quality bar — whatever V1 produces will, on represented claims, be read alongside a professional's synthesis of the same material.

---

# 3. Conflict pair map

**[INFERENCE]** The most actionable output of this document for Phase 4. Conflicts are not diffuse across a claim file; they arise between specific document pairs. **The synthetic dataset must be built around these pairs.** A ten-document claim with no conflict-bearing pair tests nothing.

| # | Pair | Earliest checkpoint | Typical conflict | Materiality | Detection difficulty |
| --- | --- | --- | --- | --- | --- |
| 1 | FNOL narrative ↔ recorded statement | **C3** | Vehicle moving vs. parked; who was driving; passengers present; direction of travel | **Often high** | Low–medium — same event, two accounts, both available |
| 2 | Recorded statement ↔ police report narrative | **C3** | Sequence of impact, right-of-way, speed, signal state, positions | **High** — independent source | Medium |
| 3 | Narrative mechanism ↔ repair estimate damage location | **C4** | Rear impact described, side damage estimated | **High** — physical evidence | **High** — cross-modal, needs causal reasoning |
| 4 | Statement/FNOL ↔ policy record | **C2** | Stated driver not a listed driver; garaging or usage inconsistent | **High** — coverage consequence | **Low** — largely deterministic |
| 5 | Statement ↔ medical records | **C4–C5** | Injury onset timing, symptom description, prior conditions, treatment gaps | **High** | Medium–high |
| 6 | Prior claims ↔ current damage | **C4** | Pre-existing damage claimed as new | **High** | High — needs prior-claim detail rarely in the file |
| 7 | Adjuster notes ↔ any document | **C2 onward** | Handler recorded a discrepancy, or a commitment that was never met | Varies | Medium — notes are hard to parse |
| 8 | Correspondence ↔ document inventory | **C2 onward** | Something was requested and never arrived | **Feeds open questions, not conflicts** | **Low** — largely deterministic |
| 9 | Demand package ↔ file record | **C5** | Attorney's liability account and specials vs. the file's own evidence | **High** | Medium |
| 10 | Timeline internal consistency | **C3 onward** | Treatment before loss; report before loss; statement before FNOL | **High when real** | **Low** — pure date arithmetic, no LLM |

**[INFERENCE]** Three observations that should shape both the product and the dataset.

**Pairs 4, 8, and 10 need no LLM.** Driver-not-listed, requested-but-never-received, and impossible chronology are deterministic checks over structured data. They are among the most *materially* consequential rows in the table and among the cheapest to implement. Any V1 that reaches for a model first has mis-sequenced its own build.

**Pair 1 is the workhorse for V1.** Available earliest, most common, most tractable, and it is the example `CLAUDE.md` itself uses. It should carry the first prototype.

**Pair 3 is the most differentiated and the least proven.** Cross-modal narrative-versus-physical-evidence reasoning is what no incumbent claims to do — and Day 1 explicitly declined to assume an LLM does it reliably. It is a research question before it is a feature.

---

# 4. Structure summary — what needs an LLM at all

**[INFERENCE]** Sorting the file by where the information actually lives, which is the sort `CLAUDE.md`'s deterministic-first principle asks for:

| Class | Documents | Handling |
| --- | --- | --- |
| **Fully structured** — no LLM | Policy record, prior claims, repair estimate, medical bills, reserve/payment history, total-loss valuation, wage documentation, rental/tow invoices | Database reads and arithmetic |
| **Structured with a narrative box** — LLM on the box only | FNOL, police report (form half structured, narrative half not), proof of loss | Fields deterministically; one targeted extraction pass on the narrative |
| **Genuinely unstructured** — LLM required | Recorded statement, adjuster notes, witness statements, correspondence, IME, peer review, demand package, EUO, litigation documents, medical records prose | Span-level extraction, then deterministic assembly |
| **Non-text** — out of V1 scope | Photographs, scene diagrams | Note presence and absence only |

**[INFERENCE]** The honest characterisation of a claim file is therefore **not** "unstructured information." It is: *mostly structured data, with a small number of high-value narrative passages — and those passages are exactly the ones that disagree with each other.*

That has a direct consequence for the architecture and it is worth stating before Phase 3 opens: **the LLM's surface area is smaller than the product concept implies.** It reads narrative passages and proposes candidate differences. Everything else — timeline ordering, date arithmetic, coverage checks, completeness tracking, counts and sums — is code. If a future design has a model touching the estimate totals or sorting the timeline, that is a regression against this map, not an enhancement.
