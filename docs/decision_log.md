# Decision Log

Records decisions made, the reasoning, alternatives considered, and what would change our mind.
Decisions that are **open** are listed at the bottom — they are surfaced, not resolved.

Format: each entry has Context / Decision / Alternatives / Consequences / Revisit if.

---

## D-001 — Research sourcing standard: grade every source, never launder a citation

**Date:** 2026-08-07
**Status:** Accepted

**Context.** Insurance fraud is a topic where the loudest sources are the most interested ones. Vendors sell detection tools, advocacy bodies lobby with prevalence figures, plaintiff firms market against insurers. Several genuinely authoritative sources (IRC full reports, *Journal of Risk and Insurance*, the CAIF SIU benchmarking survey) are paywalled or private.

**Decision.** Every source in `research/sources.md` is graded A (primary/authoritative), B (reputable secondary), or C (interested party). Every substantive claim in `research/claims-workflow.md` is tagged `[REGULATION]`, `[INDUSTRY]`, `[EMPIRICAL]`, `[INFERENCE]`, or `[UNCERTAIN]`. Where a paper was read only through another paper's summary, that is stated explicitly. Sources consulted but unusable are recorded rather than silently dropped.

**Alternatives.** Cite without grading (faster, and standard practice for internal docs) — rejected because the failure mode here is specifically that a C-grade number gets repeated until it feels like an A-grade fact. Restrict to A-grade only — rejected because practitioner sources are the only public account of the red flag vocabulary, which we need even though it is unvalidated.

**Consequences.** The research document is longer and hedged in places. In exchange, later phases can tell which foundations bear weight. The `$308.6bn` figure and the "three or more red flags" heuristic are both explicitly marked as weak, so neither can quietly become a design premise.

**Revisit if.** We obtain access to IRC reports or the CAIF benchmarking survey, at which point several `[UNCERTAIN]` items can be upgraded.

---

## D-002 — Treat commonly cited fraud indicators as investigative prompts, not predictors

**Date:** 2026-08-07
**Status:** Accepted

**Context.** The user explicitly asked not to assume commonly cited indicators are predictive. The evidence supports the caution more strongly than expected. Derrig & Francis, modelling 162,761 Massachusetts BIL claims with 21 engineered predictors, reached a best held-out AUROC of **0.667** for the SIU-referral decision and **0.678** for a favourable SIU outcome (0.50 = no predictive ability). Viaene et al. found simple logistic regression matched neural networks and SVMs on the same class of problem — the signature of an information ceiling in the features, not a modelling deficiency.

**Decision.** Indicators are treated as things worth *looking at*, not as evidence of fraud. No V1 component will assign predictive weight to an individual indicator without our own measurement. The product will not ship an overall claim risk score.

**Alternatives.** Adopt a published indicator list with weights — rejected, no public list carries validated weights. Learn weights from data — rejected for V1, we have no labelled data (see D-003).

**Consequences.** Rules out the most demo-friendly feature (a single suspicion score) and pushes the product toward evidence assembly, where value does not depend on indicator predictiveness. Also implies that "an LLM will find more signal in the same structured indicators" is a bad bet — the case for AI rests on *new* information extracted from unstructured text.

**Revisit if.** We obtain Derrig & Francis (2006), which contains variable-importance rankings for the 21 AIB predictors, or any dataset permitting our own measurement.

---

## D-003 — Ground truth in evaluation will mean "suspicion", and we will say so

**Date:** 2026-08-07
**Status:** Accepted

**Context.** No public source measures adjudicated fraud. IRC measures *appearance of fraud* as judged by claims professionals. Derrig & Francis model *the decision to investigate* and *favourable outcome*. Viaene et al. predict *expert opinion on suspicion*. Derrig & Francis further note most insurance databases contain no fraud label at all.

**Decision.** The evaluation set's labels represent *what a competent reviewer would consider worth investigating* — not proven fraud. This is stated in the evaluation artefacts themselves, not just in research notes. Metrics are never described as "fraud detection accuracy."

**Alternatives.** Label synthetic claims as fraudulent/legitimate by construction — rejected as it would measure whether the system finds what we planted, while sounding like it measures fraud detection.

**Consequences.** Caps the strength of any claim we can make about the system. Prevents the most likely self-deception in this project.

**Revisit if.** A dataset with adjudicated outcomes becomes available.

---

## D-004 — The evaluation set must be timestamped to a decision point

**Date:** 2026-08-07
**Status:** Accepted

**Context.** Derrig & Francis warn directly: their analysis uses closed claims, and variables such as total amount billed by outpatient providers "may not be fully known until the claim is nearly closed. When building a model to detect fraud and abuse prospectively, the modeler will be restricted to information available relatively early in the life of a claim."

**Decision.** Every document and structured field in the evaluation set carries the point in the claim lifecycle at which it became available. Evaluation runs at a declared decision point (e.g. post-FNOL, post-statement) using only information available at that point.

**Alternatives.** Evaluate against the complete closed file — rejected; it is target leakage and would silently inflate every metric in a way that only surfaces in production.

**Consequences.** Adds structure to `data/evaluation-set.json` before it is written, which is cheap now and expensive later. Forces D-006 (which decision point) to be answered early.

**Revisit if.** Never — this is a correctness requirement, not a preference.

---

## D-005 — Align product output to California 10 CCR § 2698.36's investigation summary

**Date:** 2026-08-07
**Status:** Proposed

**Context.** California requires an SIU investigation summary addressing: what facts suggested fraud; the alleged misrepresentations and who made them; **how they were material to the claim**; pertinent witnesses; supporting documentation; and whether the investigation is complete. This is a regulator-authored specification for exactly the artefact this product would produce. The materiality requirement also supplies the filter that Section E.4 of the research identifies as the hard part of inconsistency detection.

**Decision (proposed).** Structure signal output along these dimensions rather than inventing a schema.

**Alternatives.** Design our own output schema — rejected unless there is a reason; free alignment with a regulator's own framing is rare.

**Consequences.** Makes output directly usable by an SIU. Ties V1 to a California framing (see D-006). Makes materiality a first-class field rather than an afterthought.

**Revisit if.** V1 targets a jurisdiction whose requirements differ materially.

---

## D-014 — Verdict on the synthesis hypothesis: PROMISING BUT UNVALIDATED. No application code until the §12 experiment runs

**Date:** 2026-08-07
**Status:** Accepted

**Context.** Phase 2 research (`research/claims-synthesis-research.md`) tested whether claim synthesis is a real, ownable problem. It is real but narrower and more contested than assumed. Supporting: O*NET establishes structural fragmentation; Deloitte (Sept 2025, 17 chief claims officers) reports ~20% attrition costing ~6 years of experience per exit, new-hire productivity down ~15%, error rates rising with complexity; IRC reports represented BI claims closing in a median ~440 days with litigation rates roughly doubled; adjusters already hand-write this exact artifact as large loss reports; documentation practice uses pre-transfer checklists precisely because handoffs lose context. Against: the premise is unmeasured for personal auto (see D-021); most personal auto claims are too simple to need it; four funded vendors already ship claim summarization, one inside the system of record; and multi-document summarization research reports up to 75% hallucinated content with GPT-4o confabulating summaries of non-existent topics 44% of the time.

**Decision.** The verdict is **PROMISING BUT UNVALIDATED**. No application code is written until the validation experiment in `claims-synthesis-research.md` §12 has run. Phase 3 (domain model) is gated on it — specifically on whether materiality survives inter-rater agreement.

**Alternatives.** Declare STRONG SIGNAL and start building — rejected; zero claims professionals have been consulted and the core time claim has no measurement. Declare WEAK SIGNAL and stop — rejected; the manual analog, the attrition/duration mechanism, and the unserved reconciliation slice are all real.

**Consequences.** Delays building by roughly the time it takes to recruit 5–8 practitioners. In exchange, the three assumptions that could each individually invalidate the product get tested for the cost of a week and some synthetic fixtures rather than a built MVP.

**Revisit if.** The §12 experiment returns, on the decision rules committed in §12.6.

---

## D-015 — Analysis runs at the post-statement / post-supporting-documents checkpoint (resolves D-007)

**Date:** 2026-08-07
**Status:** Accepted

**Context.** D-007 asked at what lifecycle point analysis runs. `claims-synthesis-research.md` §6 maps five checkpoints against information availability. At **C1 (FNOL)** there is one narrative and nothing to reconcile — synthesis value is near zero and a product built there is a form-summarizer. At **C3 (post-statement)** the recorded statement and usually the police report arrive, making two of the highest-value conflict pairs checkable for the first time. At **C4 (supporting documents)** the estimate arrives and all conflict pairs are live, with documents now arriving continuously and asynchronously — the condition under which a human loses track.

**Decision.** V1 analysis runs at **C3, with C4 as the primary target**. The evaluation set is constructed at C3/C4 and never against complete closed files.

**Alternatives.** FNOL — rejected, nothing to synthesize. Pre-settlement (C5) — rejected for V1: high value, but the audience is a supervisor, counsel, or mediator, making it a *reporting* need rather than a *comprehension* need, and plausibly a different product.

**Consequences.** Satisfies D-004's timestamping requirement with concrete checkpoints. Kills "Open a claim. Get the story" as a day-zero promise. Means every synthetic claim in the dataset must be authored *as of* a checkpoint, with documents that would not yet exist withheld.

**Revisit if.** Practitioners in the §12 experiment describe their comprehension crunch as occurring at a different point.

---

## D-016 — Primary user is the adjuster inheriting a claim, not the adjuster who opened it (resolves D-009)

**Date:** 2026-08-07
**Status:** Accepted

**Context.** D-009 asked whether the user is the adjuster or the SIU investigator. With V1 no longer a fraud product (D-017), the SIU framing falls away, but the underlying question sharpens into something more useful: *which* adjuster? An adjuster who has handled a claim from FNOL already knows it; a synthesis tells them nothing they do not have. The Deloitte attrition data and the IRC 440-day duration figure together mean a substantial share of long-lived claims change hands, and the profession's existing control — a pre-transfer document checklist — verifies documents are present, not that a successor understands them.

**Decision.** The primary V1 user is the **adjuster picking up a claim they did not open**: handoff, reassignment, escalation, supervisor review, or return from absence. The triggering moment is "having to explain a claim," not "opening a claim."

**Alternatives.** The handling adjuster from FNOL onward — rejected; they are the worst case for demonstrating value. SIU investigator — deferred with the fraud capability. Supervisor/reporting audience — a real need (C5, large loss reports) but likely a different product.

**Consequences.** Reframes the product promise (§10.1: "inherit a claim without inheriting the guesswork"). Makes adjuster notes one of the highest-value inputs, since they are the only record of what a predecessor thought. Adds an output section `CLAUDE.md` does not have — "what changed since you last looked" — supported by the § 2695.7 30-day status cadence, which forces roughly fourteen re-reads on a 440-day claim.

**Revisit if.** §12 participants report that they rely on a predecessor's notes at handoff and do not re-read files — which would make the adjuster's own summary the incumbent, not any software.

---

## D-017 — V1 is not a fraud product (resolves D-010, on evidence this time)

**Date:** 2026-08-07
**Status:** Accepted

**Context.** D-010 was left open after Day 1 and was effectively decided by the `CLAUDE.md` rewrite, but on an inference: that synthesis "helps on 100% of claims" while fraud signals matter on ~2%. Phase 2 research **contradicts the reasoning while confirming the conclusion**. Synthesis does *not* help on 100% of claims — auto physical damage is among the most automated claim categories and a clear-liability PD claim has nothing to synthesize (§5.4). The conclusion survives for better reasons: fraud signals carry regulatory consequence for false positives (Day 1 §C.1), rest on indicators with a modest empirical ceiling (Day 1 §D.3), and start distrusted (~15% SIU acceptance of automated referrals), whereas synthesis carries none of that risk.

**Decision.** V1 is a synthesis product. Fraud and investigation signals remain a future capability, per `CLAUDE.md`.

**Alternatives.** Reopen the fraud framing — rejected. Ship synthesis with fraud signals as one output — rejected for V1; it would import the entire regulatory and bias surface into a product that has not yet proved its core value.

**Consequences.** Day 1's §F.1 argument must not be reused as justification. The decision stands; its stated reasoning is replaced.

**Revisit if.** Never on the current evidence — but D-017 governs V1 only, not the roadmap.

---

## D-018 — V1 targets complex, long-lived, multi-handler claims; the document map covers the core auto file plus the injury layer

**Date:** 2026-08-07
**Status:** Accepted

**Context.** Synthesis value is not uniform across personal auto. Straight-through processing is most mature in auto physical damage; leading personal-lines carriers approach ~35% STP on eligible claim types and one deployment reports ~90% of estimates running touchless. Meanwhile represented BI claims run a median ~440 days with litigation rates roughly doubled. A four-document PD claim needs no synthesis; a 440-day BI file with three handlers does.

**Decision.** V1 targets claims that are open more than ~60 days, contain at least one recorded statement plus one independent account, have more than one handler or an imminent handoff, and are contested on liability or damages. `research/claim-document-map.md` accordingly maps both the **core auto layer** and the **injury/casualty layer**, since the target segment spans both.

**Alternatives.** All personal auto — rejected as unsupported and as the framing that walks straight into the incumbents. Core auto documents only — rejected; it would map the segment that is most automated already and least in need of the product.

**Consequences.** Shrinks the addressable population considerably and honestly. Synthetic claims must be authored as complex, contested, multi-document files — a simple PD claim is not a small version of this problem, it is a different problem. Also means V1 partly overlaps incumbent territory (the injury layer), which D-019 addresses.

**Revisit if.** §12 participants report meaningful comprehension cost on routine claims.

---

## D-019 — Differentiation is cross-document reconciliation of the heterogeneous non-medical file, not volume reduction

**Date:** 2026-08-07
**Status:** Proposed

**Context.** Four vendors ship overlapping capability: CLARA DocIntel Pro (visit-level chronological medical summaries with clickable page-level citations, claiming 83% less review time), Verisk Discovery Navigator (generative medical record summaries, claiming up to 90% faster / 95% accurate), Verisk XactAI (claim note summarization), Guidewire ClaimCenter (auditable claim summaries **inside the system of record**), EvolutionIQ (auto casualty guidance). Two patterns emerge: everyone attacked the *medical* layer because that is where page count and therefore demonstrable ROI live, and **everyone does volume reduction within one corpus rather than reconciliation across corpora**. No product found claims to surface contradictions between a claimant's statement and a police report.

**Decision (proposed).** V1's position is **cross-document reconciliation of the heterogeneous non-medical auto file** — FNOL vs. recorded statement vs. police report narrative vs. repair estimate — surfacing material disagreement and unresolved questions with span-level evidence, at the handoff moment. Explicitly not: medical record summarization, note condensation, generic claim summaries, or next-best-action.

**Alternatives.** Compete on general claim summarization — rejected; Guidewire ships it where the claim already lives and no standalone tool matches that distribution. Compete on medical records — rejected; CLARA and Verisk own it at scale.

**Consequences.** This is a **feature-sized position, not a company-sized one**. Appropriate for a learning project and it should not be dressed up as a market opportunity. It also depends entirely on materiality being tractable, which is untested — if D-014's experiment kills materiality, this position goes with it.

**Revisit if.** Guidewire's ClaimCenter summarization turns out to already do cross-document reconciliation — the most important unresolved question in the competitive picture, and worth establishing before any build.

---

## D-020 — Grounding architecture: extract, then generate over facts only, and drop anything uncitable

**Date:** 2026-08-07
**Status:** Accepted

**Context.** Multi-document summarization — the exact V1 task — shows up to 75% hallucinated content on average, models confabulating summaries of entirely non-existent topics 44% of the time (GPT-4o) to 79% (GPT-3.5-turbo), hallucinations clustering toward summary endings, and "generic content generation" as a dominant error mode. Claim files are discoverable in litigation, denials require an accurate explanation of basis, and the NAIC AI Model Bulletin makes the insurer responsible for third-party AI.

**Decision.** Eight principles, stated in full at `claims-synthesis-research.md` §8.4. The load-bearing four: **(P1)** citations are span-level — document plus page/paragraph/timestamp plus offsets — never document-level; **(P2)** a fact whose span cannot be located is **dropped, not hedged**, because hedged-but-present content looks verified; **(P3)** attribution is always to *who asserted it in which document*, never to "the claim"; **(P4)** the generation step reads **only extracted-and-cited facts and never raw documents**, so it cannot fabricate from a source it cannot see. Additionally, a **null-input test** — a claim file with zero planted conflicts, where the correct output is an empty conflicts list — is a day-one evaluation case, and **specificity is scored separately from accuracy** because vacuous output passes faithfulness checks while asserting nothing.

**Alternatives.** Generate from raw documents with post-hoc citation checking — rejected; the research finds post-hoc mitigation "only moderately effective," and it inverts the safety property. Hedge low-confidence facts rather than dropping them — rejected; it produces the most dangerous output class, unverified content that reads as verified.

**Consequences.** Constrains the architecture before it is designed, which is the point. Guarantees lower recall than an unconstrained generator — an accepted trade. Makes anchoring worse, not better: a crisp well-cited summary is adopted wholesale including its omissions, and there is no purely technical mitigation for that.

**Revisit if.** Never for P1–P4 — these are correctness requirements. Evaluation specifics may change.

---

## D-021 — The "50–70% of adjuster time on administrative tasks" figure is barred from this project

**Date:** 2026-08-07
**Status:** Accepted

**Context.** The statistic dominating this space is "adjusters spend 50–70% of their time on administrative tasks, per McKinsey and Accenture." Tracing it led to a Five Sigma blog post (July 2022) which **cites neither organisation** — every figure there is presented as unattributed proprietary analysis with no methodology, no sample size, and no date beyond "the past three months." The companion "60% of time on work about work" figure comes from a general knowledge-work vendor survey, not from claims. This is exactly the failure mode D-001 was written to catch: a C-grade number repeated until it feels like an A-grade fact.

**Decision.** The figure is **barred**. It may appear in project documents only inside its own debunking. More broadly: no quantified claim enters this project from a search summary — every number is traced to origin or graded C and marked non-load-bearing. Since no public study measures personal auto adjuster time allocation, **no time-savings claim may be made until we measure one ourselves** (D-014's experiment, metric 1).

**Alternatives.** Use it with a caveat — rejected; caveats do not survive into slides. Use the workers' compensation compliance data as a proxy — rejected as a different line of business measuring a different activity.

**Consequences.** Removes the most persuasive-sounding number available and leaves the core premise explicitly unmeasured. That is the honest position, and it is why the verdict is "unvalidated" rather than "promising."

**Revisit if.** A primary source with stated methodology measuring personal auto adjuster time allocation surfaces — the McKinsey *Claims 2030* material is the most likely candidate and could not be retrieved this round.

---

# Day 2 — product definition (2026-08-13)

Decisions made while writing `product/v1-prd.md` and `data/schema.md`. Same Context / Decision / Alternatives / Consequences / Revisit-if format as above — Context carries the evidence, Consequences carries the tradeoffs.

---

## D-024 — Amend D-014: documents proceed, code does not, and gated elements are labelled in place

**Date:** 2026-08-13
**Status:** Accepted — amends D-014

**Context.** D-014 states that "Phase 3 (domain model) is gated on" the §12 experiment, and separately that no application code is written until it runs. Those are two different gates bundled into one sentence, and only the second is load-bearing. A domain model is a document. It costs a day, it is revisable, and writing it surfaces exactly the questions the experiment should be designed to answer — D-023 (are Fact/Conflict/OpenQuestion one entity?) could not be reasoned about at all until the fields were written down. Blocking it buys nothing. Blocking *code* buys the entire value of the gate, because code is what becomes expensive to throw away.

**Decision.** D-014's Phase 3 gate is amended: **documents may proceed; application code may not.** In exchange, every element of the domain model that depends on materiality being a real category is labelled **`PROVISIONAL — GATED ON D-014`** in place, and the model is arranged so that deleting all labelled elements leaves a coherent product. `data/schema.md` §3.6 walks that deletion explicitly rather than asserting it.

**Alternatives.** Hold the gate literally and skip the schema — rejected; it delays a cheap revisable artifact and leaves the experiment less well specified. Override D-014 and design as though materiality holds — rejected; if §12 metric 2 returns at chance, the model would be built around a category that does not exist, and nothing in the document would say so.

**Consequences.** The schema carries visible scar tissue — gated markers, a deletion walk, a second deletion walk for the A1-fails case. That is the intended cost: the uncertainty is legible in the artifact rather than in a research document nobody re-reads. It also means anyone reading `data/schema.md` cold can see which parts are load-bearing and which are speculative.

**Revisit if.** The §12 experiment returns. Either the markers are removed or the marked elements are.

---

## D-025 — The narrative claim summary is cut from V1; a structured header replaces it

**Date:** 2026-08-13
**Status:** Accepted

**Context.** `CLAUDE.md` lists "claim summary" as V1 output #1. Four findings argue against it. It is the **commodity**: Guidewire ships auditable AI claim summaries inside ClaimCenter, where the claim already lives, and Verisk XactAI ships note summarization (§9.1) — a standalone tool competing on "summarize the claim" competes with a checkbox. It is **where the hallucinations are**: they concentrate toward the end of generated summaries **[EMPIRICAL]** (§8.2), making long free prose the worst available output shape. Its dominant failure is **undetectable**: "generic content generation" was one of two dominant error sources on manual evaluation of 700+ insights, and "the accounts contain some differences regarding the circumstances of the loss" passes a naive faithfulness check *because it asserts nothing*. And it is the **most replaceable by a template** — §7.3 grades narration as the lowest-risk and most substitutable LLM task in the set.

**Decision.** V1 produces no narrative claim summary. It produces a **structured header** on the large loss report's own subheads (§4.2) — Coverage, Loss description, Jurisdiction, Damages, Status, Reserve — with each field individually cited and carrying an explicit `present | absent_from_file | not_assessed` state.

**Alternatives.** Keep a short summary capped at a few sentences — rejected; it inherits the vacuity failure at reduced volume without removing it, and a length cap is not a structural fix. Generate prose from the structured header for readability — deferred, not rejected; if it happens it is a template first, and a model only if the template demonstrably fails.

**Consequences.** Removes the most demo-friendly output in the product and the one a stakeholder would most expect to see. Gains a format where every element is individually falsifiable and there is no long generation for hallucinations to cluster at the end of. Contradicts `CLAUDE.md` §"V1 Output", which is corrected accordingly.

**Revisit if.** A §12 participant reports that the structured header is harder to orient from than prose, or that they cannot form an account from fields alone. This is a newly surfaced §12 question and it did not exist before this decision.

---

## D-026 — Open Questions is promoted to a first-class V1 output, built deterministically

**Date:** 2026-08-13
**Status:** Accepted

**Context.** Assumption A1 — that the bottleneck is comprehension rather than acquisition — is unmeasured and may be false (§11.1). Practitioner accounts of what adjusters chase are about missing documents, not confusing ones. Meanwhile the completeness capability is unusually cheap: expected-documents-absent is a checklist against the claim type, and requested-but-never-received is date arithmetic over correspondence (`claim-document-map.md` §3, pair 8). Neither needs a model. It is the lowest-risk row in the entire product and the highest-value one if A1 is false.

**Decision.** Open Questions is a first-class V1 output, not a secondary section, and is built **deterministically**. Concept A's machinery (extraction, evidence, differences) is still built, because that is where the LLM earns its place and where the differentiation is — but Concept B's output ships alongside it from V1.

**Alternatives.** Build Concept A only and add completeness later — rejected; it is nearly free once the document inventory exists, and it is the hedge against the assumption most likely to invalidate the product. Build Concept B only — rejected; a checklist is easy to copy, partly exists in diary/task systems already, and abandons the only differentiated position available (D-019). Wait for §12 metric 5 before deciding — rejected; the point is that we do not have to, because building both makes the answer a de-scoping rather than a rebuild.

**Consequences.** If §12 metric 5 shows next-step lists dominated by acquisition, V1 does not pivot — it **de-scopes**: delete the extraction layer and a working, mostly-deterministic product remains. `data/schema.md` §3.6 walks that deletion. The honest cost is that the PRD must state plainly that the evidence does not resolve which concept is right, and that no public study measures it (§5.3, D-021).

**Revisit if.** §12 metric 5 resolves A1 in either direction.

---

## D-027 — Fact, Difference, and OpenQuestion are three types sharing one ReviewStatus (resolves D-023)

**Date:** 2026-08-13
**Status:** Accepted — resolves D-023

**Context.** D-023 asked whether Fact, Conflict, and OpenQuestion are one entity with a status field or three entities. The case for one was real: large loss report practice attaches per-item status labels — "Related and justified," "Unrelated," "Those requiring further inquiry" (§4.2) — which reads as one entity with a resolution status.

**Decision.** **Three types, sharing one `ReviewStatus` value object.** Blake's labels are a *status on an item*, not the item's identity. The three differ on every axis that matters: a Fact requires an asserter and at least one citation; a Difference requires two or more Facts and has no single asserter; an OpenQuestion about an absent document **cannot** be cited at all, because there is nothing to cite about something that is missing. They also differ in provenance (mostly-LLM vs. mostly-deterministic) and in characteristic failure mode (hallucination vs. false-positive-on-ordinary-inconsistency vs. correct-but-obvious).

**Alternatives.** One entity with a `kind` enum and a status — rejected on the citation row alone: the drop-if-uncitable rule (D-020 P2) would have to become conditional on an enum value, and a conditional safety rule is one that will eventually be evaluated wrong. Two types (Fact/Difference merged, OpenQuestion separate) — rejected; a Difference has no asserter, and forcing one would corrupt the field D-020 P3 depends on.

**Consequences.** Three types to define, render, and evaluate instead of one. In exchange, `CLAUDE.md`'s central principle — do not collapse fact, conflict, inference, and decision — becomes **structural** rather than dependent on every consumer remembering to branch on an enum. This is D-020 P7 applied at the data layer.

**Revisit if.** A fourth item type appears that fits none of the three cleanly — which would suggest the taxonomy, not the cardinality, is wrong.

---

## D-028 — V1 persists nothing into a claim system of record

**Date:** 2026-08-13
**Status:** Accepted — partial answer to D-012

**Context.** D-012 asks what the product should persist into the claim file, and it is still open. Claim files are discoverable in litigation; anything persisted may be read aloud in a deposition years later (§8.1). Denials require a prompt and accurate explanation of basis under NAIC Model #900 and 10 CCR § 2695.7 **[REGULATION]**, so anything that flows into a denial rationale inherits regulated status. The NAIC AI Model Bulletin makes the insurer responsible for third-party AI. Meanwhile V1 has no customer, no integration, and no validated accuracy.

**Decision.** V1 writes nothing back to any claim system of record. Output is read-only, session-scoped, and stored only in the project's own evaluation artifacts. `HumanDecision` records are kept — they are the D-013 evaluation signal — but they live in our store, not in a claim file.

**Alternatives.** Write the synthesis to the claim diary as a note — rejected; it is the single fastest route from an unvalidated system to a discoverable artifact. Write only human-accepted items — rejected for now; it is the right eventual shape, but it presumes an accept/dismiss loop that has never been used by a real adjuster.

**Consequences.** Removes a plausible-sounding integration story and makes the product strictly an overlay. Also removes the largest single legal risk in the design while accuracy is unmeasured. **D-012 stays open** — this answers it for V1 by making the question moot, not by resolving it.

**Revisit if.** The product reaches a real deployment, at which point D-012 must be answered properly rather than sidestepped.

---

## D-029 — RAG and vector retrieval are excluded on faithfulness and provability grounds, not complexity

**Date:** 2026-08-13
**Status:** Accepted

**Context.** Retrieval is the reflexive architecture for "LLM over documents," and the reflex is wrong here. A core-auto claim file at C4 is **tens of pages** (§3.1) and fits in a model's context whole. The injury layer is where the hundreds-to-thousands of pages live, and V1 excludes it by D-019.

**Decision.** No RAG, no vector database, no chunk retrieval in V1. Narrative passages are enumerated deterministically from `Document.structure_class` and passed whole.

**Alternatives.** Retrieve for cost or latency — rejected; on tens of pages the saving is trivial and the cost is correctness. Retrieve to handle the injury layer — out of scope by D-019, and the right trigger for revisiting this.

**Consequences.** Two properties are preserved that retrieval would destroy. First, **faithfulness**: retrieval hides documents from the extractor, and an omission is invisible in a way a hallucination is not — the one document that contradicts the account is exactly the one a similarity search may not return. Second, **provability**: D-020 P6 requires recording which documents a synthesis was derived from, and "we processed the entire file" is a much stronger statement than "we processed what retrieval returned." A discoverable artifact should be able to make the stronger one.

**Revisit if.** The injury layer enters scope, where volume genuinely exceeds context. At that point retrieval becomes a real engineering question rather than a reflex.

---

## D-030 — Police report handling is narrative-only; D-006 stays open with the reason recorded

**Date:** 2026-08-13
**Status:** Accepted

**Context.** D-006 — which jurisdiction and tort regime V1 targets — has been open since Day 1. It binds mainly through the police report: a state traffic collision report combines a state-specific structured form with coded contributing factors, an officer narrative, and a scene diagram, and field-level extraction does not generalise across states (`claim-document-map.md` §2.3). The police report is also the **only genuinely independent account** in a typical file, so it cannot simply be dropped.

**Decision.** V1 extracts from the **officer narrative only**. The coded form and the scene diagram are recorded as present and are not parsed. California remains the *regulatory* reference frame — § 2695.7 and § 2698.36 are cited throughout — but V1 makes no *data* commitment to any jurisdiction. **D-006 stays open**, now with a recorded reason rather than as an unresolved loose end.

**Alternatives.** Commit to California and use CHP 555 structure in the fixtures — rejected for now; it locks the evaluation set to one state before we know the coded fields matter, and the narrative carries the conflict pairs V1 actually targets (pairs 1 and 2). Commit to a no-fault/PIP state — rejected; it changes the injury-layer dynamics substantially, which is the layer V1 excludes anyway.

**Consequences.** The most valuable *independent* document is read at partial fidelity: coded contributing factors and the impact diagram are exactly the kind of structured evidence that would strengthen conflict pair 3 (narrative mechanism vs. physical damage), and V1 forgoes them. That is an accepted loss — pair 3 is already the least proven capability in the product. It also means the synthetic fixtures can use a generic narrative-plus-form shape without pretending to any state's specification.

**Revisit if.** The coded contributing-factor fields or the diagram become necessary to a capability we decide to build — most likely pair 3 — or a real deployment forces a jurisdiction.

---

## D-033 — E1 experiment scaffolding is exempt from D-024, enforced by a no-materiality guard in the runner

**Date:** 2026-08-20
**Status:** Accepted

**Context.** D-014 gates Phase 5 onward on the §12 human study; D-024 amends it to "documents may proceed, code may not." Building the E1 scaffold is code. PRD §12.1 already records that E1 "gates: nothing; informs architecture" and can run in parallel with recruiting, so the exemption is consistent with the plan — but the decision log's own closing argument names the trap precisely: **a model can score extremely well against a category that is incoherent.** If we author gold materiality labels and a model reproduces them, we have measured our own consistency and called it performance. That failure is invisible from inside the technical work, which is why it needs a structural control rather than discipline.

**Decision.** Experiment scaffolding under `src/`, `schemas/`, `data/fixtures/`, `data/gold/`, and `tests/` is exempt from D-024. The exemption is bounded by a guard rather than by intent:

1. `src/evaluation/metrics.py` **raises** `MaterialityScoringAttempt` on any metric whose name contains `material`, `importance`, `severity`, `suspicion`, or `credibility`. The E1 metric list is validated against the guard at import time.
2. `materiality_intent` on gold facts and gold differences is **§12 human-study metadata**. It is never read by the runner, and a test asserts the string "materiality" does not appear anywhere in a scored result.
3. `Difference.materiality` and `materiality_rationale` are typed `"type": "null"` in `schemas/difference.schema.json`, so writing a value fails schema validation, and `assert_invariants` raises independently at assembly.
4. The gate on **Phase 5+ product code and any UI stays fully closed.** E1 answers "can the machine do it". Only the §12 study answers "is what it does worth doing".

**Alternatives.** A plain scope exemption with no guard — rejected: it leaves the failure mode a matter of memory, and the whole reason E1 is safe to run early is a property of what it scores, which is worth making mechanical. Wait for the §12 study before writing any code — rejected: E1 needs no practitioners, the fixtures are the shared bottleneck for both experiments, and a technical result that arrives after recruiting is a wasted month.

**Consequences.** E1 can run now. Materiality cannot be scored by accident, and an attempt fails loudly at the point of the attempt. The cost is that four separate places must be kept in agreement — schema, assembly invariant, metric guard, and gold semantics — which is deliberate redundancy for the one property most likely to erode quietly.

**Revisit if.** The §12 study returns and materiality gains an evidentiary basis, at which point the guard is removed by decision rather than by drift.

---

## D-035 — The model supplies the quote; code computes the citation offsets (E1b)

**Date:** 2026-09-07
**Status:** Accepted

**Context.** E1's live baseline (`google/gemini-3.8-flash`, 3 runs) dropped 33 of roughly 40 extracted facts. **Every drop was `offset_drift`. `text_absent_from_passage` was zero in all three runs.** The model quoted the source correctly every time and miscounted character positions, error accumulating through the passage (0, −4, −4, −4, −9, −8, −13). Fact recall (0.52–0.69) and difference recall (1 of 3 runs) were dominated by a clerical failure, not a comprehension one. Character counting is something code does perfectly and language models do poorly.

**Decision.** The extraction contract no longer asks a model for character offsets. It asks for a verbatim quote; `src/extraction/quote_locator.py` computes the offsets deterministically against the exact passage the model was given. `Citation.quoted_text` becomes the passage's own text at those offsets rather than the model's transcription, so a citation cannot disagree with its source. **D-020 P2 is unchanged** — an unlocatable quote is still dropped, never hedged; only the author of the offsets changed. Ambiguous quotes (more than one occurrence, not resolved by reading order) are dropped rather than guessed, because identical text inside a question and inside an answer have different asserters and a wrong pick produces a citation that resolves while misattributing.

**Alternatives.** Prompt the model harder about counting — rejected; it is the wrong tool and the E1 evidence shows the error is systematic, not stylistic. Fuzzy or semantic matching to rescue near-misses — rejected outright; it would let ungrounded content into the trusted set, which is the one thing the architecture exists to prevent. Whitespace tolerance is permitted because whitespace is presentation, and even then the result maps back to exact canonical offsets.

**Consequences.** E1b: fact recall 1.000 across three runs, zero drops, extracted facts surviving 17/18/17 against 2/6/1, difference recall 3 of 3, cost down 62%. Precision, asserter accuracy, and hallucination rate were already perfect in E1 and stayed there. `span_exactness` now measures boundary agreement with gold rather than grounding correctness, and must be read accordingly. E1 remains reproducible: `prompts.py`, `llm_extract.py`, and `pipeline.py` are untouched, and E1b lives in parallel files under its own freeze manifest.

**Revisit if.** A model appears that counts characters reliably — though even then there is no reason to ask it to.

---

## D-036 — Evidence graph as an ARCHITECTURE HYPOTHESIS, explicitly not a validated result

**Date:** 2026-09-07
**Status:** Proposed — provisional, unvalidated

**Context.** The project is moving toward representing a claim as verified assertions about shared entities and events, with timelines, corroboration, differences, and open questions as derived views. Three distinct things must not be conflated, and this entry exists mainly to keep them apart:

1. **Research finding (supported).** Cross-document relationships are where the differentiated value appears. `research/claims-synthesis-research.md` §9.2: every incumbent does volume reduction within one corpus; none reconciles across corpora.
2. **Architecture hypothesis (proposed, untested).** An evidence graph — entity/predicate/value assertions with explicit relationships — is the best representation for those relationships.
3. **Unvalidated assumption (NOT established).** That this representation materially improves the product or technical performance.

**Decision (proposed).** Claim synthesis is treated as a **view over an evidence graph** rather than as the canonical representation itself. A `Fact` is conceptually an evidence-backed **assertion**, never unquestionable world truth: subject, predicate, value, temporal scope, asserter, source document, verified citation. Explicitly excluded: graph databases, GraphRAG, vector stores, embeddings, graph neural networks, agents. Ordinary typed Python structures with stable ids, serialised to JSON for inspection.

Relationship edges between assertions (`CORROBORATES`, `COMPATIBLE_WITH`, `CONTRADICTS`) are **derived, not stored**, until there is evidence they need independent lifecycle. No `MATERIAL`, `SUSPICIOUS`, `CREDIBLE`, or `LIKELY_TRUE` relation exists — materiality stays human-only under D-014/D-033, and no stage decides which source is true.

**Alternatives.** Keep the flat `List[Fact]` — genuinely competitive and must be beaten on evidence, not aesthetics; the honest challenge is that most of the proposed benefit comes from a controlled predicate vocabulary and normalised values, which a flat list can carry without any graph machinery. Adopt a graph database — rejected; we are testing whether a graph is the right *representation*, not selecting infrastructure.

**Consequences.** Nothing in the product changes until a design comparison shows what the graph enables that a flat list with three extra fields does not. This entry records a direction, not a result.

**Revisit if.** The deliverable-4 comparison shows the neighbourhood-based difference stage does not beat the flat fact set on difference recall, false differences, or input size.

---

## D-037 — One extracted fact may satisfy several gold facts; the scorer must be many-to-one

**Date:** 2026-09-07
**Status:** Accepted

**Context.** D-034 fixed granularity for recall and precision: containment in either direction counts as a match. It did not fix the *difference* matcher, which maps each output fact to exactly one gold fact. E1b run 2 exposed it. The model returned one fact — "the claimant was driving the Mercedes-Benz G-Class southbound" — whose span covers both `stmt.vehicle` and `stmt.direction`. The greedy pass assigned it to `stmt.vehicle`, so the planted direction difference, which the model reported identically to runs 1 and 3, scored recall 0.0 and precision 0.0. The model was right and the scorer was wrong.

**Decision.** Difference matching resolves each output fact to **every** gold fact it satisfies. Implemented as `report.rescore_differences` in the non-frozen reporting layer, so both freeze manifests stay verifiable. Both experiments were re-scored from **captured model output**; no request was re-issued and no run changed. As-run and re-scored figures are reported side by side.

**Alternatives.** Amend `src/evaluation/matching.py` — rejected; it is in both freeze manifests and editing it would make E1 unreproducible. Report only the corrected figure — rejected; the scorer changed after results were seen, and hiding that would be exactly the kind of quiet post-hoc adjustment the freeze discipline exists to prevent.

**Consequences.** E1b difference recall 1/3 → 3/3. E1 unchanged at 1/3 — the correction rescues nothing there, because runs 1 and 3 proposed no difference at all. That asymmetry is itself evidence the fix is a correctness change rather than a thumb on the scale.

**Revisit if.** Never for the many-to-one property. The threshold constants remain open under D-034.

---

## D-038 — The ontology is the load-bearing part; the graph layer is not built

**Date:** 2026-09-07
**Status:** Accepted

**Context.** D-036 recorded the evidence-graph direction as a hypothesis with three levels kept deliberately apart. E2 tested the middle one by extending `Fact` with `subject_entity_id`, `predicate`, `value`, `event_id`, building the smallest vocabulary Claim 001 requires, and running both difference strategies over the SAME verified fact set: arm A flat (all facts, one call), arm B deterministic `groupby(entity, event, predicate)` then narrow classification.

**Result.** Arm B did **not** improve what it was expected to improve. Planted-difference recall was 1.00 in both arms across three runs; false differences were zero in both. Arm B used 8–9 model calls against 1, and more total input. What it did deliver: neighbourhood keys **identical across all three runs (32/32)** where the flat arm's subject key was still model-invented and varied; **7–9 corroborating relationships per run**, which the flat model cannot express at all; and structural prevention of three category errors — vehicle speed vs posted limit, occupant count vs occupant observation, per-vehicle contact points — that the flat arm can only address by asking the model nicely. Zero mis-grouped facts and zero entity-linking errors.

**Decision.** Keep the ontology fields, the controlled vocabulary, and deterministic neighbourhood grouping. **Do not build a graph abstraction, node registry, traversal API, or graph database.** Every result above came from four optional fields on `Fact` and a `groupby`; no traversal was used or missed. The evidence-graph idea's value, on this evidence, is the controlled semantic representation — not the topology.

**Alternatives.** Build the in-memory graph scaffold as originally sketched — rejected; it would add types and indirection for capabilities nothing currently needs, against `CLAUDE.md`'s rule not to add entities because they seem architecturally elegant. Abandon the ontology and keep the flat list — rejected; grouping reproducibility and corroboration are real gains the flat model cannot provide.

**Consequences.** `Fact` gains four optional fields, omitted from serialisation when unset, so E1/E1b output is unchanged and both freezes still verify. Two honest costs are recorded rather than smoothed: value normalisation is thin (only 3 of 11 comparisons resolved deterministically; 12 assertions got a predicate but no normalised value), and 11 claim-administrative facts have no predicate and are reported ungrouped rather than forced into a bucket.

**Revisit if.** A fixture needs multi-hop reasoning across entities, or a relationship needs lifecycle independent of the assertions that produced it — most likely when `HumanDecision` starts attaching to relationships rather than to Differences.

---

## D-039 — Live ingestion reuses the experiment pipeline; SSE; runtime state is a JSON file

**Date:** 2026-09-07
**Status:** Accepted

**Context.** The MVP needed to accept a new document and show the evidence state reconcile. Three choices could each have quietly undone earlier work: building a second ingestion path for the UI, relaxing grounding so the demo looks better, and letting React decide what a relationship means.

**Decision.** (1) Ingestion calls the same components the experiments used — `prompts_e2` extraction, `quote_locator` (E1b), the ontology lookup tables, and `neighborhoods.classify`. There is no UI-specific pipeline. (2) **Grounding is not relaxed**: an unlocatable or ambiguous quote is dropped and counted, and a verified assertion the ontology cannot place is kept and marked unresolved rather than pushed into a nearly-right neighbourhood. (3) **SSE, not WebSockets** — every message flows server to client, so a duplex protocol would be unused complexity. (4) Runtime state is `data/runtime/<claim>/state.json`, seeded once from the E2 artifacts and never writing back to them; no database, queue, or object store. (5) Only affected `(entity, event, predicate)` keys are recomputed. (6) Events carry structured product state only — `make_event` raises if a payload key contains reasoning, completion, materiality, credibility, liability, fraud, or suspicion.

**Alternatives.** A generic event-sourcing layer — rejected; there is no replay requirement and the authoritative state is a file. WebSockets — rejected as above. Recomputing every neighbourhood per document — rejected; the controlled representation makes the affected set exact, which is the point of E2.

**Consequences.** A relationship *change* is distinguishable from a new *position*: the demo document changed two neighbourhoods and merely added a source to three. Every `relationship_changed` event states that it describes assertions only and implies nothing about which source is right. One real bug surfaced and was fixed — the view carried `repr(value)` from the E2 debug projection, so a newly normalised `wet` would not have matched an existing `wet`; values now come from the Fact, which is authoritative.

**Revisit if.** Multi-claim or multi-user work begins, at which point a JSON file per claim stops being adequate.

---

# Open decisions

Remaining after Day 2. See `research/claims-synthesis-research.md` §11 and `product/v1-prd.md` §14 for the uncertainties behind them. **These three lists must stay synchronised.**

## Resolved by Phase 2

| # | Question | Resolved by |
| --- | --- | --- |
| ~~D-007~~ | At what point in the claim lifecycle does analysis run? | **D-015** — C3 (post-statement), targeting C4 |
| ~~D-009~~ | Primary user: adjuster or SIU investigator? | **D-016** — the adjuster *inheriting* a claim |
| ~~D-010~~ | Should V1 be a fraud product at all? | **D-017** — no; now on evidence rather than inference |
| ~~D-008~~ | Fraud (coherence) or buildup (magnitude)? | **Moot** under D-017. Returns if the fraud capability is ever revived. |

## Resolved by Day 2

| # | Question | Resolved by |
| --- | --- | --- |
| ~~D-023~~ | Are Fact, Conflict, and OpenQuestion one entity with a status field, or three? | **D-027** — three types, one shared `ReviewStatus`. An OpenQuestion about an absent document cannot be cited, so a single type would make D-020 P2 conditional on an enum. |

## Still open

| # | Question | Blocks | Why it matters |
| --- | --- | --- | --- |
| **D-006** | Which jurisdiction and tort regime does V1 target? | Police report handling, regulatory framing | **Deliberately deferred by D-030.** Narrative-only extraction sidesteps the commitment: state traffic collision reports have state-specific fields and coding, so structured extraction implicitly commits to a jurisdiction (`claim-document-map.md` §2.3). Returns if the coded form or the diagram enter scope — most likely with conflict pair 3. |
| **D-011** | Policy on indicators that proxy for socioeconomic status | Responsible AI position, NAIC AI bulletin | Reduced but not eliminated by D-017. A synthesis product still chooses what to surface, and "claimant unfamiliar with the process" or "mobile-only contact" can enter a summary as easily as a fraud score. Needs an explicit position, not a default. **Unaddressed by Day 2 and should be taken up before any output-phrasing rules are written** (`v1-prd.md` §13.4). |
| **D-012** | What does the product persist into the claim file? | Output design, legal exposure | **Made moot for V1 by D-028** (nothing is written back), not resolved. The general question survives and gets harder at deployment. Note the tension recorded in `data/schema.md` §3.4: discoverability argues for persisting little, and also for persisting enough to reconstruct what the system did. D-020's P6 stamp is the compromise; whether it suffices is what remains open. |
| **D-013** | How is adjuster disagreement captured? | Evaluation loop, materiality | **Partially answered by Day 2**: the `HumanDecision` entity in `data/schema.md` §1.10 gives it a shape — who decided what, when, against which synthesis version. The production feedback loop is still unresolved. Under D-020's P8 a dismissed conflict is the **only realistic path to measuring materiality agreement in production**. |
| **D-022** | Is the C3 comprehension product the same product as the C5 reporting product? | Scope, roadmap | Comprehension for a handling adjuster and reporting for a supervisor, counsel, or mediator have different audiences and different failure costs (`claims-synthesis-research.md` §6.3). V1 picks comprehension (D-015). Whether the other is an extension or a separate product is undecided. |
| **D-031** | Is a structured header genuinely usable in place of prose? | Output design | **Newly surfaced by D-025.** Cutting the narrative summary assumes an adjuster can orient from six cited fields as fast as from a paragraph. Nobody has been asked. Cheap to test — it is one added question in the §12 protocol, and it should be added before the study runs. |
| **D-032** | Does a completeness checklist tell an experienced adjuster anything they did not already know? | Value of the Open Questions output (D-026) | **Newly surfaced by D-026.** The checklist is trivially correct and may be trivially useless: an adjuster who has read the file already knows the police report never arrived. Correctness is measurable; usefulness needs a practitioner. This is the difference between Concept B being a product and being a footnote. |
| **D-034** | Is deterministic span matching a good enough evaluation join, or does it understate extraction quality? | Interpretation of every E1 fact metric | **Newly surfaced by D-033's scaffold.** E1 uses no LLM-as-judge, so gold facts are matched on passage identity, character-span overlap, and asserter. This undercounts semantically correct extractions worded differently, so `fact_recall` reads low for reasons that are not always the model's fault. Resolvable only by reading `detail.unmatched_output_facts` by hand after the first live run and seeing how much is a matcher artefact. |

**Day 2 confirms this unchanged**, and adds one argument for it that was not available before. `product/v1-prd.md` closes by asking which single experiment should run first, and answers the human study rather than the LLM run — because **a model can score extremely well against a category that is incoherent.** If we author the gold materiality labels ourselves and the model reproduces them, we will have measured our own consistency and called it performance. E1 would look like a success and tell us nothing about whether the feature should exist. That failure mode is invisible from inside the technical work, which is why the human study has to come first.

**Highest-value experiment available before any building — unchanged from Day 1, still untested:** can *material* inconsistency be reliably distinguished from *ordinary* inconsistency in claim narratives? Day 1 asked this of an LLM. Phase 2 sharpens it: ask it of **humans first**. If two experienced adjusters do not agree on which conflicts matter, there is no ground truth to train against, evaluate against, or ship — and the conflict feature, the only differentiated part of V1 (D-019), dies with it. This is the experiment in `claims-synthesis-research.md` §12 and the gate in D-014.
