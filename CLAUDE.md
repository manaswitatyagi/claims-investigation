# Claims Investigation Copilot

## Project Overview

I am building a small AI product as a learning project to understand:

* Product management
* Insurance claims workflows
* AI product design
* Data modeling
* LLM application architecture
* Evaluation
* Responsible AI
* Shipping an end-to-end product

The product is currently called **Claims Handoff Copilot**.

The directory name (`Claim Fraud Signal Flagger`) and the earlier title (`Claims Investigation Copilot`) are historical. The project began as a fraud-risk flagger and pivoted on evidence (D-017). Neither name reflects the current direction; both are left alone because renaming a directory mid-project is churn, not progress.

---

# Current Product Direction

The original idea was an AI fraud-risk flagger.

After domain research, that is **not the V1 direction**.

The current V1 hypothesis is:

> An adjuster **inheriting** a contested, long-lived personal auto claim can reach a defensible account of it faster and with fewer missed material items when given an evidence-backed, span-cited representation of what each source asserts, where sources disagree, and what remains unresolved — **without** the system asserting which disagreements matter, which account is true, or what the claim is worth.

The V1 product should help that adjuster **understand a claim quickly by synthesizing the claim file into an accurate, evidence-backed representation of what is known, what happened, what conflicts, and what remains unresolved.**

Fraud detection is NOT the primary V1 objective.

**Corrected by Phase 2 research — do not reuse the earlier framing.** Two claims that appeared in earlier versions of this file are contradicted by `research/claims-synthesis-research.md` and must not resurface:

* **Synthesis does NOT help on 100% of claims** (§5.4, D-017). Auto physical damage is among the most automated claim categories; a clear-liability PD claim has nothing to synthesize. That claim was the argument that drove the pivot away from fraud. The pivot survives; its reasoning does not.
* **The time premise is unmeasured** (§5.3, D-021). No public study measures how personal auto adjusters allocate their time, and the statistic that dominates this space traces to an unattributed vendor blog and is **barred from this project**. No time-savings claim may be made until we measure one ourselves.

---

# V1 Product Concept

## Working concept

**Claims Handoff Copilot**

Product promise:

> "Inherit a claim without inheriting the guesswork."

**"Open a claim. Get the story" is retired** (D-015, D-018, D-019). It implied day-zero value the information does not support — at FNOL there is one narrative and nothing to reconcile — it implied every claim, and it described what Guidewire already ships inside ClaimCenter.

The product takes an existing claim file **at the post-statement or post-supporting-documents checkpoint** and produces an evidence-backed synthesis.

Full definition: **`product/v1-prd.md`**. Output contract and domain model: **`data/schema.md`**.

### Input

A claim may contain:

* Policy information
* Claim metadata
* FNOL / First Notice of Loss
* Claimant statements
* Recorded statements
* Adjuster notes
* Police report
* Repair estimate
* Emails or correspondence
* Prior claims
* Other relevant claim documents

The user should NOT manually re-enter information that already exists in the claim file.

---

# V1 Output

The six candidate outputs below were the Day 1 starting point. Two changed status on the evidence. The authoritative version of this table is `product/v1-prd.md` §7.

## 1. Claim summary — **CUT from V1** (D-025)

Replaced by a **structured header** on large loss report subheads — Coverage, Loss description, Jurisdiction, Damages, Status, Reserve — each field individually cited, each carrying an explicit `present | absent_from_file | not_assessed` state.

Four reasons: it is the commodity Guidewire ships inside ClaimCenter; hallucinations concentrate toward the end of long generations; its dominant failure mode ("generic content generation") passes a faithfulness check *because it asserts nothing*; and it is the output most replaceable by a template.

## 2. Timeline — **KEEP**, with two axes

Built in **code** from normalised dates, never by a model. Two axes, shown distinctly:

```text
OCCURRED                          BECAME KNOWN
Jan 4   Policy begins             Feb 20   Claim reported to carrier
Feb 14  Reported loss             Feb 21   FNOL completed
Feb 14  Police attended scene     Feb 25   Recorded statement taken
                                  Mar 2    Repair estimate received
                                  Mar 9    Police report received
                                  Mar 11   Reserve increased
```

The second axis is what a **successor** actually needs and is what a chronology of the loss alone does not give them.

Dates stated vaguely in prose ("that evening") must stay vague. Inventing a timestamp is a chronology error, not a normalisation.

## 3. Key facts — **KEEP**, split by provenance

Deterministic facts (policy in force, listed-driver check, reporting delay, prior claim count) and extracted facts (what a person asserted in a document, with a span) are **visually distinct**. Users trust them differently and should see which is which.

Every fact carries **who asserted it in which document**. Not "the vehicle was parked" but "the FNOL records the claimant as reporting the vehicle was parked."

## 4. Conflicting information — **KEEP, degraded to "differences noted"**

The system surfaces where two or more sources assert different things about the same thing, showing every position verbatim with its span and asserter.

**The system does not assess materiality.** Materiality is claim-specific rather than conflict-specific — whether "was the vehicle moving?" matters depends on what is contested — and whether experienced adjusters even agree on it is the highest-risk untested assumption in the project. A human marks each difference; the marking is captured.

The system must also not re-report a difference the previous handler already noticed and resolved in their notes.

## 5. Open questions — **KEEP, promoted to first-class** (D-026)

Mostly a **deterministic completeness checklist**: expected documents for the claim type that are absent, and requests in correspondence with no matching arrival. The cheapest high-value output in the set, and the hedge if the comprehension premise turns out to be wrong.

## 6. Evidence — **KEEP**, as a property, not a section

Every item in every other output is span-cited. A citation names a locatable region — document, version, and paragraph or timestamp or character offsets. "FNOL" is not a citation.

Anything whose span cannot be resolved is **dropped, not hedged**.

## 7. "What changed since you last looked" — **DEFERRED to V1.1**

The research argues for it: the § 2695.7 30-day status cadence forces roughly fourteen re-reads on a 440-day claim, so the real need is recurring rather than one-shot. Deferred only because a diff needs two prior syntheses and we have zero. Every synthesis is versioned against its document set so this stays possible.

---

# Critical Product Principle

The system should distinguish between:

### Facts

What the source material explicitly says.

### Evidence

The underlying source supporting a fact.

### Conflicts

Places where sources disagree.

### Inferences

Potential interpretations derived from the available evidence.

### Human decisions

Conclusions or actions made by the adjuster/investigator.

Do not collapse these into one category.

---

# What V1 Should NOT Do

V1 should NOT:

* Determine whether a claim is fraudulent
* Assign a fraud probability
* Automatically refer a claim to SIU
* Automatically deny a claim
* Make underwriting decisions
* Make legal conclusions
* State that a claimant is lying
* Treat inconsistencies as proof of fraud
* Automatically write conclusions into a production claim file
* Replace an adjuster's judgment

Avoid language such as:

> "This claim is fraudulent."

> "The claimant lied."

Prefer:

> "The records contain conflicting accounts."

> "Potential inconsistency requiring review."

> "The available information does not resolve this issue."

---

# V1 AI Problem

The primary AI problem is:

> **Can an AI system construct an accurate, evidence-backed representation of a claim from fragmented structured and unstructured information?**

The most important capabilities to investigate are:

1. Fact extraction
2. Timeline construction
3. Cross-document synthesis
4. Contradiction/conflict detection
5. Evidence grounding
6. Uncertainty representation
7. Identification of unresolved questions

The AI should NOT simply generate a narrative summary.

The summary must be grounded in the source material.

---

# Deterministic vs AI Responsibilities

Do not use an LLM when normal code can solve the problem reliably.

## Prefer deterministic logic for:

* Date calculations
* Reporting delays
* Policy age
* Claim counts
* Prior claim counts
* Amount calculations
* Chronological ordering where timestamps are known
* Structured field validation

## Consider LLMs for:

* Extracting facts from unstructured documents
* Summarizing documents
* Comparing statements
* Identifying potential contradictions
* Connecting facts across documents
* Producing concise evidence-backed explanations
* Identifying unresolved questions

The architecture should make this distinction explicit.

---

# Evidence and Grounding

Every important claim in the generated synthesis should be traceable to evidence.

Prefer structured output such as:

```json
{
  "fact": "The claimant reported the loss six days after the reported loss date.",
  "sources": [
    "claim_record.reported_date",
    "claim_record.loss_date"
  ]
}
```

For document-based information:

```json
{
  "fact": "The claimant stated that the vehicle was parked.",
  "source": {
    "document": "FNOL",
    "location": "paragraph 3"
  }
}
```

The system should never invent supporting evidence.

If evidence is insufficient, explicitly state that.

---

# Evaluation Philosophy

Evaluation is a major part of the project.

Do NOT evaluate V1 primarily on "fraud detection accuracy."

Instead evaluate:

## Fact extraction

Did the system extract the correct facts?

## Timeline accuracy

Did it correctly identify and order important events?

## Evidence grounding

Can important statements be traced back to the source?

## Conflict detection

Did it correctly identify meaningful differences between sources?

## Hallucination rate

Did it invent facts, events, people, or evidence?

## Completeness

Did it omit important information?

## Summary usefulness

Can a claims professional understand the claim faster?

## Time savings

Does the product reduce the time required to understand a complicated claim?

**There is no baseline for this and no public study supplies one** (D-021). The "50–70% of adjuster time on administrative tasks" figure is **barred from this project** — it traces to an unattributed vendor blog that cites neither organisation it is credited to. No time-savings claim may be made until the §12 study measures one.

Note also the arithmetic that caps this metric: if an adjuster verifies every cited fact, the product costs time rather than saving it. Grounding makes verification *possible*; it does not make it *unnecessary*. So the measure that actually decides whether this works is not accuracy — it is **the rate at which users stop checking, and whether that rate is justified by the accuracy.** A product that earns unjustified trust is worse than one that earns none.

---

# Ground Truth

Public insurance datasets generally do not provide clean, adjudicated fraud ground truth.

Do not pretend that suspicion, SIU referral, claim outcome, or settlement outcome equals proven fraud.

For V1 synthesis evaluation, create explicit evaluation criteria for:

* facts
* timeline events
* evidence references
* conflicts
* omissions
* hallucinations

Synthetic data may be used, but clearly distinguish:

> "The system detected what we intentionally created"

from:

> "The system works on real-world claims."

Synthetic evaluation is useful for controlled testing but is not sufficient evidence of real-world performance.

---

# Data Strategy

Real insurance claim files are generally proprietary and may contain sensitive information.

For development, prefer:

1. Legitimate public datasets
2. Public crash/event datasets
3. Academic/research datasets
4. Synthetic claim records

Do not invent datasets, sources, licenses, or URLs.

When using public data:

* Verify the source
* Check usage restrictions
* Clearly distinguish real claims data from synthetic data
* Document limitations

---

# Domain Model

Designed on Day 2. Authoritative version: **`data/schema.md`**. Provisional — see the gate note below.

**Stored:** `Claim` · `Policy` · `Document` · `Passage` · `Fact` · `Difference` · `OpenQuestion` · `HumanDecision` · `Synthesis`

**Cut, with reasons:**

| Candidate | Outcome |
| --- | --- |
| `Evidence` | → a `Citation` value object on `Fact`. No identity, nothing points at it, never outlives its owner. Evidence is a *property* of every output, not a type. |
| `PriorClaim` | → a value object on `Claim`. V1 uses prior claims for a count and a recency check. Modelling more would model data the file rarely contains. |
| `TimelineEvent` | → **derived**, not stored. Recomputed from Facts carrying dates. Storing it creates two sources of truth for one date. |
| `Signal` | → cut. A fraud-era entity with no V1 output to hold (D-017). |
| `Inference` | → **no type in V1.** Nothing produces one, and an empty container gets filled by convenience. |

**`Fact`, `Difference`, and `OpenQuestion` are three types, not one with a status field** (D-027, resolving D-023). They share a `ReviewStatus` value object. They differ on everything else — an `OpenQuestion` about an absent document **cannot** be cited, so a single type would make the drop-if-uncitable rule conditional on an enum, and a conditional safety rule is one that will eventually be evaluated wrong.

Do not add entities simply because they seem architecturally elegant.

First determine whether the product actually needs them.

---

# Fraud Signals — Future Capability

Fraud/red-flag detection is a **future extension**, not the primary V1 objective.

Eventually the product may identify potential investigation signals based on the synthesized claim information.

For example:

```text
Claim synthesis
       ↓
Potential conflict
       ↓
Potential investigation signal
```

The system must never equate:

> inconsistency = fraud

or:

> unusual claim = fraud

Fraud/buildup detection should be treated as a separate product capability with its own evidence, evaluation, regulatory, and bias considerations.

---

# User

Primary V1 user (D-016):

**The adjuster picking up a claim they did not open** — reassignment, escalation, supervisor review, covering a colleague's desk, or return from absence.

Not the adjuster who has handled the claim from FNOL. They already know it, a synthesis tells them nothing they do not have, and building for them is how the product ends up as a generic summarizer.

The trigger is **"having to explain a claim,"** not "opening a claim."

This remains an open product assumption. Zero claims professionals have been consulted.

## Claim segment — in scope only if all four hold (D-018)

* Open more than ~60 days
* At least one recorded statement **plus** one independent account
* More than one handler, or a handoff imminent
* Contested on liability or damages

Everything else is out of scope **by construction**. A clear-liability property-damage claim is not a small version of this problem — it is a different problem that does not need the product, and the industry is automating it out of human hands.

## Lifecycle position (D-015)

Analysis runs at **C3 (post-statement)**, targeting **C4 (post-supporting-documents)**. Not at FNOL: there is one narrative there, nothing to reconcile, and a product built at FNOL is a form-summarizer.

## Potential future users

* SIU investigators
* Fraud analysts
* Claims supervisors, defense counsel, mediators

Do not assume their needs are identical.

An inheriting adjuster needs:

> Fast comprehension of a file someone else built.

An SIU investigator needs:

> Evidence/dossier assembly.

A supervisor at pre-settlement needs:

> A reporting artifact — the large loss report.

These may ultimately become different products. The comprehension-versus-reporting split is unresolved (D-022).

---

# Product Discovery Questions

Before locking the product, investigate:

1. How do personal auto adjusters actually spend their time?
2. How much time is spent reading/reconciling claim documents?
3. What information do adjusters need to piece together manually?
4. What does a useful claim summary look like to an experienced adjuster?
5. Which information is most difficult to find?
6. How often do claim documents contain meaningful contradictions?
7. What does an adjuster consider a "material" inconsistency?
8. What information must always be preserved with source references?
9. What information would an adjuster distrust if AI generated it?
10. What information should never be automatically written back to the claim file?

These questions should guide product discovery.

---

# Responsible AI Considerations

Be particularly careful with:

* socioeconomic proxies
* geographic proxies
* protected characteristics
* provider characteristics
* claimant characteristics
* anchoring effects
* false positives
* unsupported inferences

Do not use a characteristic merely because it correlates with historical fraud without understanding what it represents and whether it is appropriate to use.

The system should assist human judgment rather than silently steering it.

---

# Development Philosophy

This is a learning project.

I want to understand **why** product and architecture decisions are being made, not simply receive generated code.

Do not blindly execute my ideas.

If an idea is unrealistic, say so.

If AI is unnecessary, say so.

If a simpler solution works, recommend it.

If an architectural component is unnecessary, challenge it.

For major decisions, explain:

1. Problem
2. Proposed solution
3. Alternatives
4. Tradeoffs
5. Recommendation
6. What evidence would change the recommendation

Do not generate the entire application at once.

Build incrementally.

---

# Research Standards

When researching:

* Prefer primary and authoritative sources
* Use academic research where appropriate
* Cite important claims
* Verify datasets and URLs
* Do not fabricate sources
* Clearly distinguish evidence from inference
* Identify uncertainty
* Flag conflicting evidence
* State when evidence is weak or unavailable

---

# Current Project Stage

**Phases 1–3 are done. Phase 4 (data) is next, and it is the bottleneck for everything after it.**

## The gate

D-014 holds: **no application code until the validation experiment in `research/claims-synthesis-research.md` §12 has run.** D-024 amends it — documents may proceed, code may not, and every part of the domain model that depends on materiality being a real category is labelled `PROVISIONAL — GATED ON D-014` in place.

Two experiments answer different questions and run in parallel:

* **The §12 human study** (5–8 practitioners) asks *is the thing worth doing?* Its headline number is inter-rater agreement on materiality. **This is the gate.**
* **E1** (`product/v1-prd.md` §12.2) asks *can the machine do it?* One claim, three documents, one conflict pair. Needs no practitioners.

Both need the same synthetic fixtures, so **the fixtures are the real bottleneck**.

## What Day 2 produced

* `product/v1-prd.md` — the V1 definition
* `data/schema.md` — output contract and domain model
* `docs/decision_log.md` — D-024 through D-032

The current sequence is:

## Phase 1 — Domain research

Understand:

* Claims lifecycle
* Adjuster workflow
* Claim file contents
* Document types
* Investigation workflow
* Information fragmentation
* Current pain points

## Phase 2 — Product validation

Validate whether claim synthesis is actually a meaningful problem for adjusters.

## Phase 3 — Domain model ✅ done (provisional)

`data/schema.md`. Entities that survived, entities that were cut, and the deletion walk for both gate-failure cases.

## Phase 4 — Data ← **current**

Real personal auto claim files are proprietary and no legitimate public source provides complete document-level files. **V1 fixtures are synthetic**, and per D-003 they measure *what we planted*, never real-world performance — stated in the artifacts themselves, not only in research notes.

Every claim is authored **as of a checkpoint** (D-004, D-015), with documents that would not yet exist at that checkpoint withheld. Evaluating against a complete closed file is target leakage: every conflict is visible at once, which is not how real conflicts arrive.

Build fixtures around the **conflict pairs** in `research/claim-document-map.md` §3, not around the document list. A ten-document claim with no conflict-bearing pair tests nothing. Categories and gold-answer specification: `product/v1-prd.md` §9.3.

Initial target:

**2 fixtures** for the §12 study and E1, then **10 realistic claims**

Then expand toward:

**30–50 evaluation claims**

## Phase 5 — AI prototype

Test:

* Fact extraction
* Timeline construction
* Cross-document synthesis
* Conflict detection
* Evidence grounding

## Phase 6 — Evaluation

Build a structured evaluation framework.

## Phase 7 — MVP

Build:

```text
Claim list
    ↓
Claim detail
    ↓
Analyze
    ↓
AI synthesis
    ↓
Timeline + facts + conflicts + open questions
    ↓
Evidence
```

## Phase 8 — User testing

Test with claims professionals if possible.

Measure:

* usefulness
* trust
* accuracy
* time saved
* missed information
* false/confusing conflicts
* willingness to use

## Phase 9 — Future fraud capability

Only after V1 synthesis is validated should we investigate:

* red flags
* fraud signals
* SIU workflows
* investigation prioritization

---

# Core Product Question

Continuously test this hypothesis:

> **Can we reduce the time and cognitive effort required for a claims professional to understand a complex claim without hiding uncertainty or losing the underlying evidence?**

The goal is NOT:

> "Put an LLM on insurance claims."

The goal is:

> **"Make a complex claim understandable, traceable, and actionable."**
