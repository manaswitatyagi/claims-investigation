# V1 PRD — Claims Handoff Copilot

**Status:** Phase 3 product definition. Written on Day 2 from `research/claims-synthesis-research.md`, `research/claim-document-map.md`, and `docs/decision_log.md`.
**Date:** 2026-08-13
**Verdict this document inherits:** PROMISING BUT UNVALIDATED (D-014). Nothing here is validated by a claims professional. Zero have been consulted.

## How to read this document

Evidence tags are carried forward from D-001 and used identically:

| Tag | Meaning |
| --- | --- |
| **[REGULATION]** | Written into statute or regulation. Verifiable, binding. |
| **[INDUSTRY]** | Documented industry practice from a reputable source. |
| **[EMPIRICAL]** | Supported by a study with a stated methodology. |
| **[INFERENCE]** | Reasoning from the above. Not sourced. A hypothesis to test. |
| **[UNCERTAIN]** | Weakly sourced, contested, or from an interested party. |

`§n.n` references point into `research/claims-synthesis-research.md` unless prefixed `DOCMAP §`, which points into `research/claim-document-map.md`. `D-nnn` references point into `docs/decision_log.md`.

**Two standing constraints on this document.** No quantitative success metric is invented — where no baseline exists, a hypothesis and its measurement are stated instead (§16). And the barred figure from D-021 appears nowhere: no time-savings claim is made as fact, because no public study measures personal auto adjuster time allocation (§5.3).

---

# 1. Problem

## 1.1 The problem, stated narrowly

A personal auto claim that is contested and long-lived will outlive the person who opened it.

Represented bodily-injury claimants wait a median of nearly **440 days** to closure, with litigation rates roughly doubled. **[EMPIRICAL]** (§5.1) Claims-organisation attrition runs around **20% annually**, and each departure removes close to **six years of experience**; new-hire productivity is down about **15%** and error rates are climbing against rising case complexity. **[EMPIRICAL, n=17 executive interviews]** (§5.1)

Those two curves cross constantly. A substantial share of long-lived claims change hands at least once, and the person picking the file up did not do the earlier work, cannot ask the person who did, and is on a regulatory clock the moment they inherit it.

The profession already has a control for this and it is a weak one: a **pre-transfer document checklist**. **[INDUSTRY]** (§4.3) A checklist verifies that documents are *present*. It does nothing about whether the receiving adjuster can *understand* them. That gap is the problem.

## 1.2 Why this is not "adjusters read a lot of documents"

**[INFERENCE]** The generic framing — fragmented information, slow reading — is where the evidence is weakest and the competition strongest.

- **The time claim is unmeasured.** No public study measures how personal auto adjusters allocate time (§5.3). The statistic that dominates this space traces to an unattributed vendor blog and is **barred from this project** (D-021).
- **Most personal auto claims do not need this.** Auto physical damage is among the most automated claim categories; a clear-liability PD claim has an FNOL, a policy record, photos, and an estimate, and there is no story to reconstruct (§5.4). Day 1's claim that synthesis "helps on 100% of claims" is contradicted by the research and must not be reused (D-017).
- **Four funded vendors already ship claim summarization**, one of them inside the system of record (§9). A generic summary is a checkbox someone else already ticked.

The problem survives only in its narrow form: **comprehension at pickup, on files big enough that inheriting them is expensive.**

## 1.3 What is genuinely unserved

**[INFERENCE]** (§9.2, D-019) Every shipping product does **volume reduction within one corpus** — CLARA organises clinical notes chronologically, Verisk Discovery Navigator indexes and de-duplicates medical records, XactAI condenses claim notes. No product found claims to surface contradictions *between* a claimant's statement and a police report.

The reason is commercial rather than technical: medical records are where the page count is, so the ROI story writes itself. Reconciling a six-page FNOL against a twelve-page transcript saves minutes, not hours, and does not demo well — **even though it is where the disagreements are** (§3.1).

> Value in the injury layer is proportional to **page count**. Value in the core auto layer is proportional to **disagreement**.

Two honest caveats carried from D-019. This is a **feature-sized position, not a company-sized one** — appropriate for a learning project and not to be dressed up as a market opportunity. And it is possible that funded teams tried cross-document reconciliation and retreated, since the research on the underlying task is discouraging (§5.6, §8.2).

---

# 2. Target user

## 2.1 Primary user

**The adjuster picking up a personal auto claim they did not open.** (D-016)

Not the adjuster who has handled a claim from FNOL — they already know it, and a synthesis tells them nothing they do not have. They are the worst case for demonstrating value, and building for them is how the product ends up as a generic summarizer.

The user arrives through one of: reassignment, escalation to a senior or specialty unit, supervisor review, coverage of a colleague's desk, or return from absence.

## 2.2 Claim segment

**[INFERENCE]** (D-018, §10.2) In scope only if **all four** hold:

| Criterion | Threshold |
| --- | --- |
| Age | Open more than ~60 days |
| Accounts | At least one recorded statement **plus** one independent account (police report or witness statement) |
| Handling | More than one handler, or a handoff imminent |
| Dispute | Contested on liability or damages |

Everything else is out of scope **by construction**. A clear-liability PD claim is not a small version of this problem — it is a different problem that does not need the product.

## 2.3 Lifecycle position

**[INFERENCE]** (D-015, §6.3) Analysis runs at **Checkpoint 3 (post-statement, roughly days 5–30)**, with **Checkpoint 4 (supporting documents, days 15–90+) as the primary target**.

At C1 (FNOL) there is one narrative, nothing to reconcile, and a product built there is a form-summarizer. At C3 the recorded statement and usually the police report arrive, making the two highest-value conflict pairs checkable for the first time. At C4 the estimate arrives, every conflict pair is live, and documents begin arriving continuously and asynchronously — the condition under which a human loses track and a machine does not.

C5 (pre-settlement) is deliberately excluded from V1: the audience there is a supervisor, defense counsel, or mediator, which makes it a **reporting** need rather than a **comprehension** need, and plausibly a different product (D-022, still open).

## 2.4 Users this product is not for

| Would-be user | Why not in V1 |
| --- | --- |
| SIU investigator | Deferred with the fraud capability (D-017). Their need is dossier assembly, not comprehension. |
| Fraud analyst | Same. |
| Claims supervisor / defense counsel / mediator | A real need at C5, but a reporting artifact with different failure costs (D-022). |
| Adjuster who opened the claim | Already holds the context the product would supply. |
| Claimant or claimant's attorney | Never. The product reads a file written under litigation constraints. |

---

# 3. User workflow

## 3.1 The job, stated as one sentence

> An adjuster who did not open a contested personal-auto claim — 60+ days old, 10–20 documents, at least one recorded statement plus one independent account — must produce a **defensible account** of it, on a deadline, in their first working session with the file.

## 3.2 The trigger is "having to explain a claim," not "opening a claim"

**[INFERENCE]** (§2.2) Synthesis load is not evenly spread across the claim lifecycle. It spikes at four moments: assignment/handoff, liability determination, reserve changes, and any point where the file must be presented to someone outside it. Those are not "reading the file" moments in general — they are moments where the adjuster must **produce a defensible account**.

The regulatory clock supplies the most reliable of these triggers. California's § 2695.7 requires a written status update every **30 calendar days** on an open claim, and an accept/deny decision within **40 days** of proof of claim. **[REGULATION]** (§2.3) On a 440-day claim that is roughly fourteen forced occasions on which someone must know enough about the file to write about it.

**[INFERENCE]** That has a consequence the product must not miss: **this is a recurring need, not a one-shot one.** A synthesis useful only the first time you open a claim addresses perhaps a tenth of the real occasions. V1 does not build the recurring case (see §7, "what changed since you last looked" is deferred), but the data model must not preclude it (D-020 P6).

## 3.3 Before / after

### Before (current workflow)

```
Claim lands on the desk — reassignment, escalation, or a 30-day status update comes due
        ↓
Open the claims system. Read the FNOL fields.
        ↓
Open the document repository. Find what is there. There is no index of what should be there.
        ↓
Read the recorded statement transcript end to end — long, conversational, non-linear.
        ↓
Read the police report. Read the officer narrative. Try to hold both accounts side by side.
        ↓
Read the predecessor's notes — terse, abbreviated, written for an audience of one.
        ↓
Open the estimate. Check whether the damage matches the account you now hold in your head.
        ↓
Reconstruct a chronology on paper or in your head from dates scattered across all of it.
        ↓
Notice — or fail to notice — that two documents say different things.
        ↓
Form a view. Write the status note / set the reserve / decide the next action.
```

**What is painful about it.** **[INFERENCE]**, from §2.4, §4.3, and DOCMAP §2.2/§2.4:

1. The adjuster **is the integration layer** across a claims platform, estimating software, a document repository, external database portals, email, and spreadsheets. **[INDUSTRY]** — O*NET 13-1031.00 documents the technology span (§2.4). It does *not* establish what that costs in time, and we should not claim it does.
2. **Nothing tells you what is missing.** The document repository shows what arrived. There is no view of what was requested and never came — that lives in correspondence (DOCMAP §1.1).
3. **Cross-document comparison is the one thing a human is genuinely bad at**, because it requires holding the whole file in working memory against each new arrival (§4.4).
4. **The predecessor's reasoning is only partly recoverable.** Notes record what they thought and tried, but in abbreviated form, and six years of judgment left with them (§5.1).
5. **The chronology has to be rebuilt every time**, by every handler, from dates scattered across documents that each use a different format.

### After (with V1)

```
Claim lands on the desk — same trigger
        ↓
Open the claim. Press Analyze.
        ↓
Read a structured header: coverage, loss description, jurisdiction, damages, status, reserve —
  every field individually cited, provenance visible (system field vs. extracted from prose)
        ↓
Read the timeline: what happened, and — separately — when each fact became known
        ↓
Scan differences: where two sources say different things about the same thing,
  both positions shown verbatim with spans. Materiality NOT asserted by the system.
        ↓
Scan open questions: what is expected for this claim type and absent,
  what was requested and never arrived, what the file does not resolve
        ↓
Spot-check the two or three items that will drive the decision, by clicking through to the span
        ↓
Form a view. Write the status note / set the reserve / decide the next action.
```

**What the user does with the output.** They use it to *orient*, then they act in their own systems. Concretely: it feeds a § 2695.7 status note, a reserve conversation with a supervisor, or a next-action list ("get the supplement, re-contact the witness, order the certified police report").

**What it explicitly does not do:** it does not write anything into the claim file. V1 persists nothing to a system of record (D-028). D-012 — what the product should persist into a discoverable claim file — remains open, and until it is answered the safe position is "nothing."

---

# 4. Current workflow

Covered in §3.3 above as the "before" case. Two additional facts about the current state matter for positioning and are recorded here rather than in the workflow diagram.

## 4.1 The output already exists as a manual artifact

**[INDUSTRY]** (§4.2) When a loss reaches roughly $100,000, or a reserve change takes it there, adjusters write a **large loss report**. Practitioner guidance (Gary Blake, via Claims Journal 2009 and IRMI 2013) prescribes: an RE line carrying handler, report date, current and proposed reserve, policy number, insured, paid-to-date, location, and policy term; an executive summary that states its purpose immediately; a claim narrative that contrasts the positions of claimant and insurer; **a separate Conclusions section so subjective assessment never contaminates the factual presentation**; subheads for Coverage, Jurisdiction, Damages/Injury, Loss Description, Reserves, Status; and per-item status labels — "Related and justified," "Unrelated," "Those requiring further inquiry."

**[INFERENCE]** Three consequences, and they are the most useful paragraphs available to this PRD.

**The format is not invented.** Someone pays an adjuster to produce this artifact by hand, and pays a communications consultant to teach them how. That is better evidence of demand than any survey.

**The profession independently arrived at this project's core principle.** Blake's segregated Conclusions section *is* the fact/inference separation `CLAUDE.md` demands. V1 borrows the subheads directly (§6.2).

**And this cuts against us.** The large loss report is a **management reporting** artifact produced at $100k+, not a daily comprehension aid. It confirms the format is valuable. It does not confirm the format is wanted on a routine claim.

## 4.2 The incumbent may be the predecessor's own notes

**[INFERENCE]** The competitive frame that matters most is not Guidewire. It is that an adjuster inheriting a file may simply read the last ten diary entries and consider themselves oriented. If that is what actually happens, the incumbent is a human summary that already exists in the file, and it is free. §11.3 names this as the path to a WEAK SIGNAL verdict, and §12 metric 7 is the test.

---

# 5. V1 hypothesis

## 5.1 The hypothesis

> An adjuster inheriting a contested, long-lived personal auto claim can reach a defensible account of it **faster and with fewer missed material items** when given an evidence-backed, span-cited representation of what each source asserts, where sources disagree, and what remains unresolved — **without** the system asserting which disagreements matter, which account is true, or what the claim is worth.

## 5.2 The promise

**[INFERENCE]** (§10.1) `CLAUDE.md`'s "Open a claim. Get the story" is wrong in three ways: it implies day-zero value the information does not support (D-015), it implies every claim (D-018), and it describes what Guidewire already ships inside the system of record (D-019).

Closer to what the evidence supports:

> **"Inherit a claim without inheriting the guesswork."**

That names the user (someone who did not open this claim), the moment (pickup), the segment (files big enough that inheriting is hard), and the value (not re-deriving what a predecessor already knew).

## 5.3 The three assumptions this hypothesis rests on

Carried forward unchanged from §11.1. All three are untested. None is testable by building.

| # | Assumption | If false | Test |
| --- | --- | --- | --- |
| **A1** | The bottleneck is **comprehension**, not **acquisition** | The product inverts. Open Questions becomes primary, the summary becomes context, and **most of the valuable part needs no LLM.** `CLAUDE.md` demands we say so if AI is unnecessary; this is that scenario. | §12 metric 5 — ratio of acquisition to comprehension items in unprompted next-step lists |
| **A2** | Adjusters will **rely on** the synthesis rather than re-read behind it | Value shifts from time saved to error reduction — real, but harder to sell and measure, and not what `CLAUDE.md` currently claims. Note the trap: the good outcome is trust *calibrated to accuracy*, not maximum trust. | §12 metric 4 — observed rate of opening source documents behind citations |
| **A3** | **"Material conflict"** is a category experienced adjusters agree on | The only differentiated part of V1 dies (D-019), and V1 collapses into commodity summarization that Guidewire ships inside the system of record. **Highest-risk item in the project.** | §12 metric 2 — inter-rater agreement on materiality across 5–8 practitioners on identical planted conflicts |

§7 is designed so that A3 failing is a **de-scoping**, not a rebuild. §8 and §14 carry this forward.

---

# 6. Product experience

## 6.1 The workflow, end to end

```
Claim already exists (C3/C4, meeting the §2.2 segment criteria)
        ↓
User opens claim
        ↓
User selects Analyze
        ↓
─────────────── everything below is §10 / §11 ───────────────
Read structured data from the claim record          [deterministic]
Enumerate documents; identify narrative passages    [deterministic]
Extract facts with spans from narrative passages    [LLM]
Normalise dates, parties, locations, amounts        [deterministic]
Compute derived facts (delays, counts, sums)        [deterministic]
Build timeline by sorting normalised dates          [deterministic]
Compare facts about the same thing; propose diffs   [LLM]
Run completeness checklist for the claim type       [deterministic]
Assemble output; drop anything without a span       [deterministic]
─────────────────────────────────────────────────────────────
        ↓
Result: header + timeline + facts + differences + open questions,
        every item span-cited, provenance visible
        ↓
User reviews, spot-checks, accepts or dismisses individual items
        ↓
User acts in their own systems. Nothing is written back. (D-028)
```

**What deliberately is not in this diagram:** no retrieval step, no agent loop, no vector store, no orchestration layer. §8 explains why each is absent.

## 6.2 The result screen

Five regions, in reading order. The order is deliberate: the two regions with the lowest hallucination exposure come first.

**1 — Header.** The large loss report's own subheads (§4.1), each field individually cited: **Coverage · Loss description · Jurisdiction · Damages · Status · Reserve**. Short, structured, field-wise. Not prose. §8.2's finding that hallucinations concentrate toward the end of long generations is a direct argument for this shape.

**2 — Timeline.** Two axes, shown together and labelled distinctly:
- *When the event occurred* — the loss, the report, the statement, the estimate.
- *When the fact became known* — when the police report arrived, when the reserve changed, when the attorney letter came in.

**[INFERENCE]** The second axis is what a successor actually needs and is what a chronology of the loss alone does not give them. Reserve changes in particular are a strong signal of *when the predecessor's view of severity shifted* (DOCMAP §1.1).

**3 — Facts, split by provenance.** Structured-system facts (policy in force, listed driver, prior claim count, reporting delay) and extracted facts (what a person asserted in a document, with a span) are **visually distinct**. Users trust them differently and should be able to see which is which (§10.3).

**4 — Differences.** Where two or more sources assert different things about the same thing. Both positions shown verbatim with spans and asserters. **The system does not label these material.** See §7.4.

**5 — Open questions.** What is expected for this claim type and absent; what was requested in correspondence and never arrived; what the file does not resolve.

Running through all five: every item is span-cited, and **absence is stated rather than implied** — "no police report is present in the file" is an output, and "no differences detected" must be distinguishable from "differences not assessed" (D-020 P5).

## 6.3 What the interface must never do

**[INFERENCE]**, from §8.3 and `CLAUDE.md`:

- Never render an extracted fact as a claim about the world. Not "the vehicle was parked" but "the FNOL records the claimant as reporting the vehicle was parked" (D-020 P3).
- Never present a difference as evidence of dishonesty, and never as a fraud signal (D-017).
- Never silently merge two names into one party. Entity resolution is proposed and visible, never applied (§7.1).
- Never hedge an item it could not cite. Uncitable content does not reach the screen at all (D-020 P2).
- Never present a single overall score of any kind (D-002).

---

# 7. V1 capabilities

## 7.1 Prioritization

Six candidate outputs came from `CLAUDE.md`. Two changed status on the evidence.

| Capability | V1? | Why? | Risk | How we evaluate it |
| --- | --- | --- | --- | --- |
| **Extracted facts with spans** (LLM over narrative passages) | **Yes** | The keystone (§7.3). Nothing else exists without it — timeline, differences, and header all assemble from extracted facts. Deterministic code cannot read prose. | **High.** Span accuracy on disfluent recorded-statement transcripts is untested (U-2). Speaker misattribution is the highest-consequence error type and generic benchmarks do not measure it (§8.3). | Per-fact precision/recall against a gold fact list; **span-exactness** scored separately from fact-correctness; **asserter-correctness** scored separately from both. |
| **Structured facts** (deterministic) | **Yes** | Free. Policy in force on DOL, listed-driver check, reporting delay, prior claim count, totals — all database reads and arithmetic (§7.1, DOCMAP §4). Also the highest-trust content on the screen. | **Low.** Failure is a code bug, reproducible and fixable. | Exact-match against the source record. Not a model evaluation. |
| **Timeline** | **Yes** | High value to a successor, and it is **code, not model** — sorting normalised dates. The two-axis version (occurred / became known) is the part a chronology alone does not give (§10.3). | **Medium.** The risk is upstream: a date extracted wrongly from prose sorts wrongly. Vague temporal expressions ("that evening") cannot be normalised without inventing precision (DOCMAP §2.2). | Ordering correctness against a gold sequence; separately, **rate of invented precision** on vague expressions. |
| **Evidence / citations** | **Yes** | Not a section — a **property of every other output** (§10.3). It is the mechanism by which every other capability becomes checkable, and a procurement gate under the NAIC AI Model Bulletin (§8.1). **[REGULATION]** | **Medium.** A citation that points to the wrong span is worse than no citation, because it looks verified. | Span-resolution rate (does the cited span exist and contain the asserted content); **fabricated-citation rate** as its own metric. |
| **Differences** (candidate conflicts) | **Yes, degraded** | The differentiated capability (D-019) — no shipping product does cross-corpus reconciliation. Detecting *difference* is tractable; deciding *materiality* is not, and V1 does not attempt it. | **High, and gated.** A3 is the highest-risk assumption in the project. Base rate of ordinary inconsistency between honest accounts is unknown (U-3): if 30% of honest files contain a discrepancy, unfiltered detection is noise. Mitigating factor — a wrongly flagged difference costs seconds of reading, unlike a wrongly flagged fraud signal (§4.4). | Recall and precision against planted differences; **false-difference rate on the zero-conflict control**; and, separately from any model metric, §12 metric 2 on humans. |
| **Open questions** | **Yes, promoted** | Mostly a **deterministic completeness checklist** — expected documents for the claim type that are absent, plus requests in correspondence with no matching arrival (DOCMAP §3, pair 8). Cheapest high-value output in the set, and the hedge if A1 is false. | **Low technically. Medium in usefulness** — a checklist can be complete and still tell an experienced adjuster nothing they did not know. | Recall against a gold missing-item list; separately, **usefulness rated by a practitioner** (§12), because a correct-but-obvious question has no value. |
| **Narrative claim summary** | **No — cut** | See §7.2. | — | — |
| **"What changed since you last looked"** | **No — V1.1** | See §7.3. | — | — |

## 7.2 Why the narrative claim summary is cut (D-025)

`CLAUDE.md` lists "claim summary" as output #1. It is cut from V1. Four reasons, in order of weight:

1. **It is the commodity.** Guidewire ships auditable AI claim summaries **inside ClaimCenter**, where the claim already lives — no integration, no separate login, no procurement cycle (§9.1). Verisk XactAI ships note summarization. A standalone tool competing on "summarize the claim" is competing with a checkbox.
2. **It is where the hallucinations are.** Hallucinations concentrate **toward the end of generated summaries**. **[EMPIRICAL]** (§8.2) Long free prose is the single worst output shape available given the research.
3. **Its dominant failure mode is undetectable.** "Generic content generation" — vague statements substituted for specific ones — was one of two dominant error sources on manual evaluation of 700+ insights. **[EMPIRICAL]** (§8.2) A summary that says "the accounts contain some differences regarding the circumstances of the loss" is not detectably hallucinated. It is simply useless, and it **passes a naive faithfulness check because it asserts nothing.**
4. **It is the most replaceable by a template.** §7.3 of the research grades narration as real value at the lowest risk — and also the most substitutable. If a structured header carries the same information, the marginal value of prose is presentation, and presentation is not what this product is for.

**What replaces it:** the structured header in §6.2, using the large loss report's own subheads (§4.1), each field individually cited. This preserves everything the summary was for — orientation in seconds — while being short, field-wise, individually checkable, and immune to the end-of-summary failure.

**What would reverse this.** A practitioner in §12 reporting that the structured header is harder to read than prose, or that they cannot orient from fields alone.

## 7.3 Why "what changed since you last looked" is deferred

The research argues for it and the argument is sound (§10.3): the § 2695.7 30-day cadence and continuous asynchronous document arrival at C4 both point to a recurring rather than one-shot need, and a diff is cheaper, more verifiable, and less prone to vacuity than a full re-synthesis.

It is still deferred, for one reason: **a diff needs two prior syntheses and we have zero.** Building it now is building on nothing. D-020's P6 requirement — every synthesis versioned against the document set it covers — is what makes it possible later, and it is in the V1 schema for exactly that reason.

## 7.4 The hard boundary: the system proposes differences, a human decides materiality

**[INFERENCE]** (§7.4) People telling the truth about a stressful event are routinely inconsistent. A recorded statement taken three weeks after a collision **will** differ from an FNOL taken twenty minutes after it. Detecting differences is easy. Deciding which matter is the entire problem.

Two facts sharpen this:

**Materiality is the regulator's own filter.** California's SIU investigation-summary requirement demands that a summary address **how a misrepresentation was material to the claim** (10 CCR § 2698.36). **[REGULATION]** We are not inventing the category; we are inheriting a legal one.

**Materiality is claim-specific, not conflict-specific.** Whether "was the vehicle moving?" matters depends on what is in dispute. On a clear-liability rear-end claim with an admitted at-fault party it may be irrelevant; on a disputed-liability claim it may decide the outcome. **[INFERENCE]** So it cannot be a static rule table, and it may not be learnable from the conflict text alone — the model would need to know what is contested.

**V1's position.** The system surfaces differences and says nothing about their materiality. The human marks each one, and **the marking is captured** (D-020 P8). Those markings are the only realistic path to measuring materiality agreement in production (D-013), and they are the V1 asset that would make a future materiality model possible.

The `materiality` field exists in the schema and is marked `PROVISIONAL — GATED ON D-014` (D-024). If §12 metric 2 comes back at chance, the field is deleted and V1 ships as "differences noted, materiality not assessed" — which is precisely §12.6's narrowed-scope branch, pre-built.

## 7.5 Concept A vs. Concept B — the unresolved question, and how V1 survives either answer

The research identified this as assumption A1 and could not resolve it (§11.1). This section does not resolve it either. It states the comparison and explains how V1 is structured so the answer is a de-scoping decision rather than a rebuild.

### The two concepts

**Concept A — Claim Synthesis.** The product explains what is already in the file: facts, timeline, differences, evidence.

**Concept B — Claim Completeness.** The product identifies what is missing and what the adjuster may need next: expected-but-absent documents, requested-but-never-received items, unresolved questions.

### Comparison

| Dimension | Concept A — Synthesis | Concept B — Completeness |
| --- | --- | --- |
| **User value** | High **if** A1 holds. Directly addresses handoff comprehension, which the research supports structurally (§4.3, §5.1) but has never measured. | High **if** A1 is false. Practitioner accounts of what adjusters chase are about missing documents, not confusing ones (§11.1). Unmeasured either way. |
| **Technical feasibility** | **Hard.** Cross-document faithfulness is the unsolved part: up to 75% hallucinated content in multi-document summarization, 44% confabulation on non-existent topics for GPT-4o. **[EMPIRICAL]** (§8.2) | **Easy.** A checklist over a document inventory plus date arithmetic over correspondence. DOCMAP §3 pairs 8 and 10 are explicitly deterministic. |
| **AI necessity** | **Genuine.** Deterministic code cannot read a recorded statement. This is where the LLM earns its place (§7.3). | **Largely none.** This is the scenario in which `CLAUDE.md`'s "if AI is unnecessary, say so" applies, and we should say it plainly. |
| **Differentiation** | **The unserved slice** (§9.2). Nobody does cross-corpus reconciliation. | **Low.** A checklist is easy for anyone to copy, and diary/task systems partly do it already. |
| **Evaluation** | **Hard.** Needs gold fact lists, span accuracy, asserter accuracy, hallucination and omission rates, and a specificity metric because vacuity passes faithfulness checks. | **Easy.** Recall against a known missing-item list. But **usefulness** is hard — a correct question an adjuster already knew has no value. |
| **Risk** | **High.** Hallucination, misattribution, anchoring — and anchoring gets *worse* as the product gets better (§8.3). Discoverable claim file (§8.1). | **Low.** A false "this is missing" costs a lookup. A missed "this is missing" is the pre-existing state. |
| **Potential time savings** | Unknown and unmeasurable until §12 metric 1. Capped by A2 — if every cited fact gets verified, net saving is zero or negative (§8.5). | Unknown. Plausibly smaller per use but on more claims, since a checklist works on simple files too. |

### Recommendation (D-026)

**Build A's machinery. Ship B's output as a first-class V1 capability.**

The reasoning is asymmetric cost. B is nearly free once A's document inventory exists — the checklist runs off the inventory and correspondence dates, needs almost no LLM, and is the lowest-risk row in the entire product. A is where the LLM earns its place and carries all the hallucination exposure. Shipping both means:

- If §12 metric 5 shows **comprehension items are a real share of next steps** → A1 holds, A is the product, B is a valuable secondary.
- If metric 5 is **dominated by acquisition** → A1 is false. We delete the extraction layer and keep a working, mostly-deterministic product. That is a **de-scoping, not a rebuild** — and the schema in `data/schema.md` is arranged so the deletion is clean.

**Stated plainly, as the brief requires:** the evidence does not resolve which is the bottleneck. No public study measures personal auto adjuster time allocation (§5.3), the standard citation is barred (D-021), and zero practitioners have been asked. §12 metric 5 is the only thing that will resolve it. This PRD proceeds on A **provisionally**, having deliberately made the fallback cheap.

---

# 8. Non-goals

Every item below is excluded from V1 with a reason. Exclusions marked **permanent** are not roadmap items.

## 8.1 Product exclusions

| Excluded | Why deferred |
| --- | --- |
| **Fraud score** | **Permanent for V1** (D-017, D-002). No public indicator list carries validated weights; the best published models on this problem reach AUROC ~0.667 for the SIU-referral decision. Also the most demo-friendly feature available, which is exactly why it is dangerous. |
| **Fraud classification / red flags** | Deferred to a separate capability with its own evidence, evaluation, regulatory, and bias considerations (`CLAUDE.md`). Importing it now would bring the entire regulatory and bias surface into a product that has not proved its core value. |
| **SIU referral** | **Permanent for V1.** In California a referral creates a legal obligation on the SIU. **[REGULATION]** (Day 1 §C.1) Machine-originated referrals also start distrusted — SIU acceptance fell to 15% (§8.5). |
| **Automated claim decisions** (accept, deny, settle) | **Permanent.** Denials are regulated, must carry an accurate explanation of basis, and are discoverable. **[REGULATION]** (§8.1) The highest-consequence act in the workflow. |
| **Automatic claim-file writeback** | Deferred pending D-012. Claim files are discoverable; anything persisted may be read aloud in a deposition years later. V1 persists nothing to a system of record (D-028). |
| **Coverage decisions / reserve setting / liability determination** | **Permanent.** Bad-faith exposure, financial commitment, and legal conclusion respectively (§2.5). The system may supply inputs. |
| **Deciding a claimant is not credible** | **Permanent.** A judgment about a person on incomplete information with discrimination exposure (§2.5). |
| **Materiality assessment by the system** | Gated on D-014 / A3, not permanently excluded. §7.4. |
| **Photographs and scene diagrams** | Deferred. Out of scope for a text-first V1 (DOCMAP §4). Presence and absence are noted; content is not read. |
| **"What changed since you last looked"** | Deferred to V1.1. §7.3 — needs two prior syntheses. |
| **Real insurer system integrations** | Deferred. Requires a customer. Also the exact axis on which Guidewire's embedded position cannot be matched (§9.1). |

## 8.2 Technical exclusions

| Excluded | Why |
| --- | --- |
| **RAG / vector database** (D-029) | **Not excluded for complexity.** A C4 claim file is tens of pages in the core auto layer (§3.1) and **fits in context whole**. Retrieval would *reduce* faithfulness by hiding documents from the extractor — an omission is invisible where a hallucination is not — and it would make "we processed the entire file" unprovable, which D-020 P6 requires. Retrieval is a scaling answer to a problem we do not have. **Revisit if** the injury layer enters scope, where volume is hundreds to thousands of pages. |
| **Agents / tool-calling loops** | The pipeline in §6.1 is a fixed sequence with no branching and no decision points. Introducing non-determinism where a `for` loop suffices is a regression against `CLAUDE.md`'s deterministic-first principle, and it makes evaluation harder by making runs non-reproducible. |
| **Complex workflow orchestration** | Same reason. Nine stages, executed in order, once. |
| **Fine-tuning** | We have no labelled data, and D-003 caps what any label could mean. Fine-tuning before measuring base model performance also destroys the ability to attribute a result to anything. |
| **Predictive models** | D-002. No validated indicators, no labelled data, and a documented information ceiling in the available features. |
| **Production-scale infrastructure** | This is a learning project evaluating 10–50 synthetic claims. Anything beyond a script and a file store is premature. |
| **Multi-jurisdiction police report parsing** (D-030) | State traffic collision reports have state-specific fields and coding schemes (DOCMAP §2.3). V1 extracts from the **officer narrative only** and ignores the coded form, which sidesteps the jurisdiction commitment entirely. **D-006 stays open.** |
| **Multi-modal / diagram reading** | The scene diagram is often the clearest statement of impact geometry and is not text. Out of scope; note its presence only. |

---

# 9. Data required

## 9.1 Per claim, at C3/C4

**[INDUSTRY]** for availability, per DOCMAP §1.1. A V1 claim fixture contains:

| Input | Structure | Handling |
| --- | --- | --- |
| Claim record (metadata, dates, parties, status) | Structured | Deterministic read |
| Policy record / declarations | Structured | Deterministic read |
| Prior claims history | Structured | Deterministic counts |
| FNOL | **Semi-structured** — ~100 fields + 1–2 narrative boxes | Fields read deterministically; **LLM on the Description of Accident box only** |
| Recorded statement transcript | Unstructured, long, disfluent | LLM span extraction |
| Police report | **Mixed** — coded form + officer narrative + diagram | **Narrative only** in V1 (D-030); form and diagram noted as present, not parsed |
| Adjuster notes / diary | Unstructured, abbreviated, jargon-heavy | LLM span extraction |
| Repair estimate | Highly structured line items | Deterministic; **no LLM reads an estimate for its numbers** |
| Correspondence | Unstructured | LLM extraction of requests and commitments; deterministic matching of request → arrival |
| Reserve and payment history | Structured | Deterministic; reserve *changes* feed the "became known" timeline axis |
| Witness statements (when present) | Unstructured | LLM span extraction |

**[INFERENCE]** (DOCMAP §2.1) The FNOL point is worth restating because it is easy to get wrong: the narrative content of an FNOL is one or two free-text boxes surrounded by roughly a hundred structured fields. Treating the whole FNOL as an unstructured document to parse is avoidable work, avoidable error, and a direct violation of the deterministic-first principle.

## 9.2 Data source strategy

**Synthetic only for V1.** Real personal auto claim files are proprietary and contain sensitive personal, medical, and financial information. No legitimate public source provides complete, document-level claim files.

Per D-003, synthetic evaluation measures **what we planted**, never real-world performance, and every evaluation artifact must say so in the artifact itself, not only in research notes.

## 9.3 Evaluation dataset design

Target: **10 realistic claims** for development, expanding to **30–50** for evaluation. Not generated on Day 2 — this section specifies what they must contain.

Every claim is authored **as of a checkpoint** (D-004, D-015), with documents that would not yet exist at that checkpoint withheld. Evaluating against a complete closed file is target leakage: every conflict is visible at once, which is not how real conflicts arrive.

### Categories

Each maps to a capability and, where applicable, to a conflict pair from DOCMAP §3.

| # | Category | What it tests | Conflict pair |
| --- | --- | --- | --- |
| 1 | **Straightforward claim** | Baseline. Does the system produce a correct, complete, boring result without inventing interest? | — |
| 2 | **Zero-conflict control** | **The most important case in the set.** §8.2 reports GPT-4o confidently summarizing entirely non-existent topics 44% of the time. **[EMPIRICAL]** The correct output is an empty differences list. If the system invents one, no other metric matters. | none, by construction |
| 3 | **Document-heavy claim** | Completeness and omission under volume. Does the one contradicting document get dropped? | many |
| 4 | **Missing information** | The Concept B path — open questions, expected-but-absent documents, requested-but-never-arrived items. | 8 |
| 5 | **Conflicting statements** | The core differentiator. FNOL narrative vs. recorded statement — moving vs. parked, who was driving, passengers present. | **1** |
| 6 | **Independent-account conflict** | Recorded statement vs. police report narrative — sequence, right-of-way, signal state. Higher weight because the police report is the only genuinely independent source. | **2** |
| 7 | **Ambiguous chronology** | Vague temporal expressions ("that evening", "a few minutes later"). Correct behaviour is to preserve the vagueness, **not** to invent a timestamp. | 10 |
| 8 | **Irrelevant documents** | Does an unrelated document (a rental invoice, a duplicate) generate spurious facts or differences? Tests precision under noise. | — |
| 9 | **Structured vs. unstructured contradiction** | Stated driver is not a listed driver; garaging inconsistent with stated usage. **Deterministic to detect, materially consequential.** Tests whether the system reaches for a model where code suffices. | **4** |
| 10 | **Multiple parties** | Entity resolution — "Robert Smith" / "Bob Smith" / "R. Smith", two claimants, a passenger who is also a witness. LLMs are confidently wrong here (U-7). Correct behaviour is to **propose, never merge**. | — |
| 11 | **Prior claims** | Pre-existing damage claimed as new. Requires prior-claim detail rarely present in the file — tests whether the system asserts a connection it cannot support. | **6** |
| 12 | **Already-noticed-by-predecessor** | A difference the previous handler already logged **and resolved** in their notes. The system must not re-report it as new. Directly from DOCMAP §2.4 — this is a failure mode no benchmark measures and it would destroy trust immediately. | **7** |
| 13 | **Physical-evidence mismatch** | Rear impact described, side damage estimated. The most differentiated and least proven capability — a research question before it is a feature. | **3** |
| 14 | **Complicated claim** | All of the above at once, as the segment in §2.2 actually looks. The realism check (U-4). |  many |

Categories 5, 6, 9, and 2 are the minimum viable set. Category 13 may fail entirely and that is an acceptable V1 outcome.

### Gold answer specification

Each fixture ships with an authored gold answer containing:

1. **Fact list** — every fact a correct system should extract, each with: assertion text, asserter, document, exact span, and normalised value where applicable.
2. **Facts that must NOT appear** — plausible-but-absent facts, to catch hallucination directly rather than by inference.
3. **Timeline** — the correct ordered sequence on both axes, with vague expressions marked as **must remain vague**.
4. **Planted differences** — each with the two-or-more positions, the documents, and an **authored materiality intent** (clearly material / clearly immaterial / deliberately ambiguous). Several must sit in the ambiguous middle, because the middle is what §12 is actually about.
5. **Differences that must NOT be reported** — including the already-resolved one from category 12.
6. **Open questions** — the correct missing-item list.
7. **A standing disclaimer**, in the artifact itself: *these labels record what we planted. They are not evidence of real-world performance* (D-003).

---

# 10. AI responsibilities

**[INFERENCE]** (§7.3) Being strict about it, the LLM earns its place in **two stages of nine** (§6.1), plus one optional third:

## 10.1 Stage — extract facts with spans from narrative passages

**Input:** one narrative passage (FNOL Description of Accident box, recorded statement transcript, police officer narrative, adjuster note, correspondence body, witness statement).
**Output:** a list of `(assertion, asserter, span)` triples. Nothing without a locatable span survives (D-020 P2).
**Why the LLM:** deterministic code cannot read prose. This is the capability that unlocks everything else.

Three known difficulties specific to recorded statements (DOCMAP §2.2, U-2):
- **Speaker attribution.** A fact asserted by the adjuster in a leading question ("so you were stopped at the light?") is not the claimant's assertion. Conflating them is exactly the misattribution failure P3 exists to prevent, and it is the error most likely to be invisible in evaluation and damaging in a deposition (§8.3).
- **Self-correction.** When a speaker revises within one statement, the final version is the assertion — but the revision is itself informative. Both need representing, and **they are not a conflict with each other**.
- **Vague temporal expressions.** "A few minutes later." These cannot be normalised without inventing precision.

## 10.2 Stage — propose candidate differences between normalised facts

**Input:** the normalised fact set. **Never raw documents** (D-020 P4).
**Output:** candidate differences, each holding a *set* of positions (not a pair — three-way disagreement between FNOL, statement, and police report is real), with the facts and their spans.
**Why the LLM:** this is the one thing a human is genuinely bad at, because it requires holding the whole file in working memory against each new arrival (§4.4).
**Boundary:** proposes difference. Never asserts materiality (§7.4). Never asserts that a party is being untruthful.

## 10.3 Stage (optional) — narrate the structured header fields

Even here the generation reads only extracted-and-cited facts. Given §7.2, this may be a template rather than a model, and V1 should try the template first.

## 10.4 What the LLM must never do

| Never | Because |
| --- | --- |
| Arithmetic of any kind | Slower, costlier, non-reproducible, and less accurate than code (§7.1) |
| Sort the timeline | Ordering is done in code from normalised dates. A model sorting dates is a regression against DOCMAP §4. |
| Read the repair estimate for its numbers | Structured line items. The totals are arithmetic. |
| Read the FNOL's structured fields | ~100 fields, all readable from the record (DOCMAP §2.1) |
| Merge two party names | Propose only, always visible (§7.1, U-7) |
| See a raw document during generation | D-020 P4. The single strongest structural defence against §8.2's failure modes: the model cannot fabricate from a source it cannot see. |
| Assert materiality, suspicion, credibility, liability, or coverage | §7.4, §8.1 |

---

# 11. Deterministic responsibilities

**[INFERENCE]** (§7.1, DOCMAP §4) Seven of nine pipeline stages:

| Responsibility | Detail |
| --- | --- |
| **Structured field reads** | Policy in force on DOL, coverages, limits, deductibles, listed drivers, scheduled vehicles, garaging address, prior claim count and recency, reserve and payment history, estimate line items and totals. |
| **Date arithmetic** | Days from policy inception to loss; loss to report; report to FNOL completion; statement lag; treatment lag; policy age. |
| **Chronological ordering** | Timeline sorting on both axes, from normalised dates only. |
| **Counts and sums** | Prior claims, document counts, estimate totals, paid-to-date, reserve movements. |
| **Structured validation** | Set-membership and range checks — is the stated driver a listed driver, is the vehicle scheduled, was the policy in force. **DOCMAP §3 pair 4 is materially consequential and needs no model.** |
| **Timeline internal consistency** | Treatment before the loss, report before the loss, statement before the FNOL. **DOCMAP §3 pair 10 — pure date arithmetic, no LLM.** |
| **Completeness checklist** | Expected documents for the claim type that are absent; requests in correspondence with no matching arrival. **DOCMAP §3 pair 8.** This is most of the Open Questions output. |
| **Citation resolution** | Verifying that every cited span exists and contains the asserted text. Anything that fails is **dropped** (D-020 P2). |
| **Assembly and versioning** | Building the output object; stamping it with the document set and versions it covers (D-020 P6). |

**[INFERENCE]** Worth stating explicitly before any architecture exists: **three of the ten conflict pairs in DOCMAP §3 — pairs 4, 8, and 10 — need no LLM at all**, and they are among the most materially consequential rows in the table. Driver-not-listed, requested-but-never-received, and impossible chronology are deterministic checks over structured data. Any V1 that reaches for a model first has mis-sequenced its own build.

---

# 12. Evaluation strategy

## 12.1 Two experiments, different questions, running in parallel

| | **§12 study** (human) | **E1** (technical) |
| --- | --- | --- |
| Question | Is the thing worth doing? | Can the machine do it? |
| Needs | 5–8 practitioners | No practitioners |
| Gates | D-014 — Phase 5 onward | Nothing; informs architecture |
| Answers | A1, A2, A3 | U-2, and the §8.2 confabulation risk |

**[INFERENCE]** They need **the same synthetic fixtures**, and E1 needs no recruiting. So the fixtures are the real bottleneck for both, and E1 can run while recruiting happens. That does not weaken D-014's gate — E1 tells us whether the machine can do it; §12 tells us whether what it does is worth doing, and a machine result cannot substitute for that.

## 12.2 E1 — the first technical experiment (Part 8)

Smallest thing that answers: *can an LLM accurately extract span-cited facts from realistic claim narratives and propose differences between them without inventing any?*

### Scope

**One claim file. Three documents. One conflict pair.** Pair 1 — FNOL narrative ↔ recorded statement (DOCMAP §3) — chosen because it is available earliest, most common, most tractable, and is the example `CLAUDE.md` itself uses. Plus the policy record, so the deterministic path is exercised alongside.

Deliberately **not** optimising for model sophistication. One model, one prompt version, no chaining, no retrieval.

### Input

- `claim_record` — structured JSON: claim number, loss date, report date, parties, status
- `policy_record` — structured JSON: inception, expiry, coverages, limits, listed drivers, scheduled vehicles
- `fnol` — structured fields **plus** one `description_of_accident` free-text passage
- `recorded_statement` — one transcript with speaker labels and timestamps

### Processing before the LLM

1. Read all structured fields deterministically. No model involvement.
2. Compute derived facts: reporting delay, policy age at loss, listed-driver check, vehicle-scheduled check.
3. Identify narrative passages: `fnol.description_of_accident`, `recorded_statement.body`. **Two passages, that is all.**
4. Assign stable passage IDs and character offsets so spans are resolvable.

### The LLM task

**Call 1 — extraction, once per passage.** Given one passage and its ID, return a list of assertions, each with: the assertion, who asserted it, the exact quoted span, and its character offsets. Instructions include: attribute to the speaker who said it, not the questioner; if a speaker self-corrects, return the final version and mark the revision; **do not normalise vague time expressions**; return only what the passage states.

**Call 2 — difference proposal, once per claim.** Given the **normalised fact set only — never the passages** (D-020 P4), return candidate differences: which facts disagree, about what, with the fact IDs. Explicit instruction: **do not assess materiality; if there are no differences, return an empty list.**

### Post-processing (deterministic)

Resolve every span against the source passage. **Anything that does not resolve exactly is dropped, not hedged** (D-020 P2). Sort the timeline in code. Assemble the output and stamp it with the document set.

### Evaluation metrics

Scored against the authored gold answer (§9.3). Every metric reported separately — a single composite score would hide exactly the failures that matter.

| Metric | Definition | Why separate |
| --- | --- | --- |
| **Fact recall** | Gold facts correctly extracted / total gold facts | Omission |
| **Fact precision** | Correct extracted facts / total extracted | Noise |
| **Span exactness** | Extracted facts whose span resolves and contains the assertion | A correct fact with a wrong span is unverifiable, and looks verified |
| **Asserter accuracy** | Facts attributed to the correct speaker | **The highest-consequence error type** (§8.3). Generic benchmarks do not measure it. |
| **Hallucination rate** | Extracted facts appearing in the gold "must NOT appear" list, or citing a non-existent span | The core risk |
| **Omission rate** | Gold facts absent from output, weighted toward facts marked material-in-intent | Completeness scored separately from accuracy (§8.3) |
| **Timeline ordering accuracy** | Correctly ordered events / total | |
| **Invented-precision rate** | Vague expressions normalised to a specific timestamp | Directly from DOCMAP §2.2 |
| **Difference recall / precision** | Against planted differences | The differentiator |
| **False differences on the zero-conflict control** | Count. **Target: zero.** | §8.2's 44% confabulation finding. If this fails, no other metric matters. |
| **Specificity** | Human-rated: does each output item assert something checkable, or is it vacuous? | Scored **separately from accuracy** (D-020) because "the accounts contain some differences" passes a faithfulness check while asserting nothing |
| **Open-question usefulness** | Human-rated: would an experienced adjuster not already know this? | A correct-but-obvious question has no value |

**Run each fixture at least 3 times.** Variance across runs is itself a finding — a capability that works one time in three is not a capability.

### Decision rules for E1

Committing before seeing data:

- **False differences on the zero-conflict control > 0** → the extraction-then-generate architecture is not sufficient on its own. Investigate before anything else. Nothing downstream is trustworthy.
- **Span exactness or asserter accuracy is poor** → grounding is not achievable at this level of effort, D-020 P2 drops most output, and the product does not work. This is a stop-and-rethink, not a tuning problem.
- **Fact recall poor but precision good** → acceptable for V1. D-020 explicitly accepts lower recall as the price of the drop-if-uncitable rule.
- **Everything passes** → the technical risk is lower than §8.2 predicted, which is informative but changes nothing about D-014's gate.

## 12.3 The §12 human study

Unchanged from `research/claims-synthesis-research.md` §12 and not restated here. Its shape matters to this PRD in three ways: the aided condition uses a **hand-written** synthesis (Wizard of Oz, no model) so that model quality cannot confound the result; **metric 2 — inter-rater agreement on materiality — is the headline number**; and the decision rules in §12.6 are already committed.

## 12.4 What neither experiment tests

Real claim files (synthetic only, D-003), long-term adoption, the anchoring risk (§8.3 — there is no purely technical mitigation and a *better* product makes it worse), and whether an insurer would buy it.

---

# 13. Risks

## 13.1 Risks to the product being right

| Risk | Evidence | Mitigation |
| --- | --- | --- |
| **The premise is unmeasured** | No public study measures personal auto adjuster time allocation; the standard citation is fabricated (§5.3, D-021) | No time-savings claim until §12 metric 1 measures one. Barred figure stays barred. |
| **The segment is much smaller than assumed** | Auto PD is among the most automated claim categories; a clear-liability PD claim has nothing to synthesize (§5.4) | Segment defined by construction in §2.2, not discovered in user testing |
| **The incumbent is Guidewire, inside the system of record** | Auditable AI claim summaries embedded in ClaimCenter — no integration, no separate login, no procurement (§9.1) | Position on cross-document reconciliation, which nobody claims (D-019). Honestly: a feature-sized position. |
| **The incumbent is the predecessor's own notes** | §4.2, §11.3 | §12 metric 7 and the closing behavioural questions |
| **The output's only real-world analog is a $100k+ management report** | §4.1 | Acknowledged. §12 tests whether the format is wanted on a routine complex claim. |

## 13.2 Risks to the system working

| Risk | What it looks like here | Mitigation |
| --- | --- | --- |
| **Hallucination** | A passenger, injury, or witness who appears in no document | Drop-if-uncitable (D-020 P2); zero-conflict control as a day-one test case |
| **Incorrect attribution** | "The police report states X" when the claimant stated X | Attribution to asserter-in-document (P3); asserter accuracy as its own metric |
| **Omission** | The one document contradicting the summary is left out | Completeness scored separately; per-document coverage check |
| **Generic vacuity** | "There are some inconsistencies in the accounts" | Specificity scored separately from accuracy. **This is why the narrative summary is cut** (§7.2). |
| **Incorrect chronology** | Treatment before the loss; invented timestamps from "that evening" | Ordering in code, never by the model; invented-precision as its own metric |
| **Source confusion** | Two parties merged into one narrative | Entity resolution proposed, never applied (U-7) |
| **Overconfident language** | "The vehicle was parked" instead of "the FNOL records the claimant as reporting…" | Assertion framing enforced at the output layer |
| **Stale synthesis** | Output reflects the file as of last week | Versioned and stamped with its document set (P6) |
| **Re-reporting a resolved difference** | A discrepancy the predecessor already noticed and closed | Eval category 12. Not measured by any benchmark, and would destroy trust on first contact. |

## 13.3 Risks with no technical mitigation

**Anchoring.** The adjuster adopts the system's framing and stops looking. **[INFERENCE]** (§8.3) This is the one risk where **improving the product makes the risk worse**: a vague summary is ignored, a crisp well-cited confident summary is adopted wholesale — *including its omissions*. There is no purely technical fix. What partly helps: making absence explicit (P5), showing provenance so the user knows which items are model-derived, and never asserting materiality.

**Unjustified trust.** The metric that decides whether this product works is not accuracy — it is **the rate at which users stop checking, and whether that rate is justified by the accuracy** (§8.5, A2). A product that earns unjustified trust is worse than one that earns none.

## 13.4 Regulatory and responsible-AI risks

| Risk | Basis |
| --- | --- |
| Anything the product produces that reaches a denial rationale inherits regulated status | NAIC Model #900 and 10 CCR § 2695.7 require a prompt, accurate explanation of the basis for a denial. **[REGULATION]** (§8.1) |
| Anything persisted is discoverable and may be read aloud in a deposition | §8.1. **Why V1 persists nothing (D-028), and why D-012 stays open.** |
| Third-party AI is the insurer's responsibility, with a written program requiring validation and testing for errors and unfair discrimination | NAIC AI Model Bulletin, adopted December 2023. **[REGULATION]** (§8.1) Grounding evidence is a procurement gate, not a nicety. |
| **Socioeconomic and geographic proxies entering a summary** | D-011, still open. Reduced but not eliminated by D-017: a synthesis product still chooses what to surface, and "claimant unfamiliar with the process" or "mobile-only contact" can enter a summary as easily as a fraud score. **Needs an explicit position, not a default.** |

---

# 14. Open assumptions

Nothing in this section is resolved. Listed items must stay synchronised with `research/claims-synthesis-research.md` §11.2 and the open-decisions table in `docs/decision_log.md`.

## 14.1 The three that could each invalidate the product

Restated from §5.3: **A1** (comprehension vs. acquisition), **A2** (reliance vs. re-reading), **A3** (materiality agreement — the highest-risk item in the project).

## 14.2 Other open uncertainties

| # | Uncertainty | Blocks | Status |
| --- | --- | --- | --- |
| **U-1** | How personal auto adjusters actually spend their time | Any time-savings claim | Unresolved. Two search rounds found nothing. §12 metric 1 gives us our own small measurement. |
| **U-2** | Whether an LLM produces span-accurate extraction on disfluent recorded-statement transcripts | The entire architecture | Untested. **E1 tests this** — cheap, and no practitioners needed. |
| **U-3** | Base rate of *ordinary* inconsistency between honest accounts | Threshold setting, fixture realism | Unresolved. If 30% of honest files contain a discrepancy, detection without materiality filtering is noise. |
| **U-4** | Whether synthetic claim files are realistic enough for practitioners to engage with | §12's validity, all evaluation | Untested and **load-bearing**. If practitioners reject the fixtures, the experiment measures nothing. Mitigate by piloting with one participant first. |
| **U-7** | Whether cross-document entity resolution is reliable enough to propose at all | Cross-document synthesis quality | Untested. Eval category 10. |
| **U-8** | Whether "no differences found" can be safely asserted | Output design | Open, sharpened by §8.2's confabulation finding. Eval category 2. |

Research §11.2's **U-5** (jurisdiction) and **U-6** (C3 comprehension vs. C5 reporting) are not dropped — they graduated into decisions and are tracked as **D-006** and **D-022** in §14.3 below.

## 14.3 Open decisions

| # | Question | Why it is still open |
| --- | --- | --- |
| **D-006** | Which jurisdiction and tort regime? | Deliberately deferred by D-030 — narrative-only police report extraction sidesteps the commitment. Returns if the coded form or contributing-factor fields enter scope. |
| **D-011** | Policy on indicators that proxy for socioeconomic status | Needs an explicit position before any output-phrasing rules are written. §13.4. |
| **D-012** | What does the product persist into the claim file? | D-028 answers it for V1 by persisting nothing. The general question survives. |
| **D-013** | How is adjuster disagreement captured? | Partially answered by the HumanDecision entity in `data/schema.md`. The production loop is unresolved. |
| **D-022** | Is the C3 comprehension product the same as the C5 reporting product? | V1 picks comprehension. Whether the other is an extension or a separate product is undecided. |
| **D-031** | Is a structured header genuinely usable in place of prose? | **Newly surfaced by this document** (§7.2). Cutting the narrative summary assumes an adjuster can orient from six cited fields as fast as from a paragraph. Cheap to test — one added question in the §12 protocol, and it should be added before the study runs. |
| **D-032** | Does a completeness checklist tell an experienced adjuster anything they did not already know? | **Newly surfaced by this document** (§7.5). The checklist is trivially correct and may be trivially useless — an adjuster who has read the file already knows the police report never arrived. This is the difference between Concept B being a product and being a footnote. |

---

# 15. Validation plan

## 15.1 Sequence

```
Author 2 synthetic claim fixtures at C4, with gold answers          ← the real bottleneck
        ↓
        ├──────────────────────────────┬──────────────────────────────┐
        ↓                              ↓                              │
   Pilot fixtures with 1 practitioner  Run E1 (§12.2)                 │
   (tests U-4 — do they read as real?) (tests U-2, §8.2)              │
        ↓                              ↓                              │
   Revise fixtures                Architecture findings ──────────────┘
        ↓
   Run the §12 human study, 5–8 practitioners
        ↓
   Apply §12.6 decision rules
        ↓
   D-014 gate lifts (or does not)
        ↓
   Phase 5 — AI prototype
```

**The fixtures gate everything.** Both experiments need them, and U-4 says that if practitioners do not find them realistic, the human study measures nothing. Piloting with one participant before recruiting the rest is the cheapest available insurance.

## 15.2 Decision rules (already committed, §12.6)

| Outcome | Action |
| --- | --- |
| Metric 2 shows meaningful agreement **and** metric 1 shows a time reduction **and** metric 5 shows comprehension items are a real share of next steps | **Proceed to Phase 5** as specified |
| Metric 2 weak, metrics 1 and 3 positive | **Proceed with narrowed scope** — drop materiality entirely, present "differences noted, materiality not assessed", compete on timeline plus evidence assembly, and accept that this is close to what incumbents ship |
| Metric 5 dominated by acquisition | **Pivot** — the product becomes completeness and open-questions tracking, mostly deterministic, and we say plainly that the LLM is largely unnecessary |
| Metric 2 at chance **and** metric 1 shows no time reduction | **Stop.** The differentiated feature is unbuildable and the undifferentiated one is already shipped inside the system of record |

## 15.3 What is being built before validation

Fixtures, gold answers, an E1 script, and the evaluation harness. **No application code, no UI** (D-014, D-024).

---

# 16. Success criteria

**No quantitative targets are set.** There is no baseline for any of them — U-1 is unresolved, D-021 barred the only widely quoted number, and inventing a target here would manufacture the exact false precision this project is trying to avoid.

What follows is stated as hypotheses with their measurement.

## 16.1 V1 succeeds if

| # | Hypothesis | Measured by | Currently |
| --- | --- | --- | --- |
| **S1** | An adjuster reaches a confident account of an inherited claim faster with the synthesis than without | §12 metric 1, within-subject, counterbalanced | **No baseline exists.** The measurement creates it. |
| **S2** | They miss fewer material items, especially those requiring three or more documents | §12 metric 3 | Unmeasured |
| **S3** | They **spot-check** rather than systematically re-read | §12 metric 4, observed and uncounted-to-participant | Unmeasured. Note: the good outcome is trust *calibrated to accuracy*, not maximum trust. |
| **S4** | Experienced adjusters agree, above chance, on which planted differences are material | §12 metric 2 — **the headline number** | Unmeasured. **If this fails, the differentiated feature does not exist.** |
| **S5** | The system reports **zero** differences on the zero-conflict control | E1, eval category 2 | Untested. The one criterion with an absolute target, because §8.2 makes the failure mode specific and the correct answer is unambiguous. |
| **S6** | Every output item resolves to an exact span in a source document | E1 span-exactness | Untested |
| **S7** | Facts are attributed to the correct asserter | E1 asserter accuracy | Untested |
| **S8** | Practitioners engage with the fixtures as realistic | §12 pilot, U-4 | Untested and load-bearing |

## 16.2 What V1 is explicitly not measured on

Fraud detection accuracy of any kind (D-017, D-003). Summary fluency or readability as a proxy for correctness. Coverage of every personal auto claim (D-018). Any composite score — every metric in §12.2 is reported separately, because a composite hides exactly the failures that matter.

---

# Closing — challenging the product

## What we believe

Supported by evidence, at the grade stated:

1. **Claim files are structurally fragmented and the adjuster is the integration layer.** **[INDUSTRY, Grade A]** — O*NET 13-1031.00.
2. **Long-lived claims outlive their handlers, and this is getting worse.** **[EMPIRICAL]** — ~20% attrition at ~6 years of experience per exit (Deloitte, n=17), against a median ~440 days to closure for represented BI claims (IRC).
3. **The output has a real, expensive manual analog.** **[INDUSTRY]** — large loss reports, hand-written, with a segregated Conclusions section the profession arrived at independently of this project.
4. **Handoff information loss is a named problem the profession already mitigates manually.** **[INDUSTRY]** — pre-transfer document checklists, which verify presence and not understanding.
5. **Regulation forces recurring re-reads.** **[REGULATION]** — § 2695.7's 30-day status cadence, ~14 occasions on a 440-day claim.
6. **The unserved slice is real but narrow.** **[INFERENCE]** — everyone ships volume reduction within one corpus; nobody claims cross-corpus reconciliation.
7. **The LLM's surface area is smaller than the product concept implies.** **[INFERENCE]** — two pipeline stages of nine; three of ten conflict pairs need no model at all.

## What we are assuming

Unvalidated. Zero claims professionals consulted.

1. **A1** — the bottleneck is comprehension rather than acquisition. Unmeasured, and the standard citation is fabricated.
2. **A2** — adjusters will rely on the synthesis rather than re-read behind it. Machine output here starts distrusted on evidence.
3. **A3** — materiality is a category experienced adjusters agree on. **The highest-risk item in the project.**
4. That an LLM can extract span-accurate, correctly-attributed facts from disfluent transcripts (U-2).
5. That synthetic fixtures are realistic enough to measure anything (U-4).
6. That a structured header is as usable as prose (§7.2, newly surfaced).
7. That the incumbent is not simply the predecessor's own notes (§4.2).

## What we are building

A **narrow, evidence-backed handoff aid** for an adjuster inheriting a contested, 60+ day personal auto claim at C3/C4:

- a **structured header** on the large loss report's subheads, each field cited;
- a **two-axis timeline** — when it happened, and when it became known — built in code;
- **facts split by provenance**, structured-system vs. extracted-with-span;
- **differences** between sources, both positions verbatim, **materiality not asserted**;
- **open questions** from a deterministic completeness checklist;
- **span-level citations on everything**, with anything uncitable dropped rather than hedged.

## What we are NOT building

A narrative claim summary. A fraud score, classification, or SIU referral. Any automated claim, coverage, reserve, or liability decision. Any writeback to a claim file. A materiality judgment made by the system. Photograph or diagram reading. Multi-jurisdiction police report parsing. RAG, a vector database, agents, orchestration, fine-tuning, predictive models, or production infrastructure. And — for now — the diff view, which the research argues for and which needs a history we do not yet have.

## What we need to learn next

The three highest-value experiments, in order:

1. **Do experienced adjusters agree on which differences are material?** (§12 metric 2.) Everything differentiated depends on it.
2. **Can an LLM extract span-accurate, correctly-attributed facts from a disfluent transcript — and return an empty list when there is nothing to report?** (E1, U-2, §8.2.) Cheap, no recruiting, and it can run this week.
3. **When an adjuster inherits a claim, is their first move to understand what is there or to chase what is not?** (§12 metric 5.) Decides whether Concept A or Concept B is the product.

## If we could run only ONE experiment before building the UI

> **The §12 inter-rater materiality study. Not the LLM run.**

The reasoning, plainly:

If experienced adjusters do not agree on which differences matter, there is **no ground truth** — no training target, no evaluation criterion, and no defensible product behaviour. The conflict feature is the only part of V1 that no incumbent ships (D-019). Without it, V1 is commodity summarization competing against a capability Guidewire delivers inside the system of record, with no distribution and no differentiation. The product does not survive that.

And the technical experiment cannot substitute, for a reason worth being precise about: **a model can score extremely well against a category that is incoherent.** If we author the gold labels ourselves and the model reproduces them, we will have measured our own consistency and called it performance. E1 would look like a success and tell us nothing about whether the feature should exist. That failure mode is invisible from inside the technical work, which is exactly why the human study has to come first.

E1 is cheaper, needs no recruiting, and should run alongside — it de-risks the architecture. But it answers a different question, and it is not the one that decides whether to build.
