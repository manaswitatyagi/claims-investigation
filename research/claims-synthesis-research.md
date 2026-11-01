# Claims Synthesis — Product Validation Research

**Status:** Phase 2 discovery. Tests the V1 hypothesis. No product or architecture decisions made here.
**Date:** 2026-08-07
**Scope:** US personal auto claims, with the injury/casualty layer included where the evidence points there.
**Supersedes nothing.** `research/claims-workflow-old.md` (Day 1, fraud framing) remains the record of why the project pivoted. Its regulatory findings are carried forward here and re-cited, not assumed.

## How to read this document

Every substantive claim is tagged. Same vocabulary as Day 1, per decision D-001.

| Tag | Meaning |
| --- | --- |
| **[REGULATION]** | Written into statute or regulation. Verifiable, binding. |
| **[INDUSTRY]** | Documented industry practice from a reputable source. |
| **[EMPIRICAL]** | Supported by a study with a stated methodology. |
| **[INFERENCE]** | My reasoning from the above. Not sourced. A hypothesis to test. |
| **[UNCERTAIN]** | Weakly sourced, contested, or from a party with an interest in the answer. |

A note on this round's sourcing environment, because it changes how much weight the document can carry. Searching for "how do adjusters spend their time" in 2026 returns an almost unbroken wall of vendor content marketing — AI claims platforms, BPO providers, and SEO farms, all citing each other. Several widely repeated statistics dissolve when traced (§5.3). Where I could not verify something I say so rather than filling the gap, and I have deliberately written up one *failed* verification as a finding, because the failure is more useful to this project than the number would have been.

---

# 1. Executive summary

## 1.1 What was asked

Whether "claims adjusters lose significant time mentally reconstructing a claim from fragmented documents" is a real, ownable product problem — before building anything.

## 1.2 The verdict

**PROMISING BUT UNVALIDATED — with a required scope correction.** Full reasoning in §10.4.

The problem is real. It is not the shape `CLAUDE.md` currently states.

"Open a claim. Get the story," applied to *every* personal auto claim, is simultaneously where the evidence is weakest and where the competition is strongest. Most personal auto claims are not complex enough to need synthesis, and four funded vendors already ship claim summarization — one of them inside the system of record itself.

The evidence supports a narrower wedge: **comprehension at pickup on long-lived, multi-handler, injury-or-liability-disputed claims** — the adjuster inheriting a file they did not open.

## 1.3 The seven findings that matter

1. **The industry's most-quoted adjuster productivity statistic does not survive checking.** "Adjusters spend 50–70% of their time on administrative tasks, per McKinsey and Accenture" traces to a vendor blog that cites neither organisation. There is still no public measurement of personal-auto adjuster time allocation. The project's central premise is *unmeasured*, not disproven. (§5.3)

2. **The output we propose already exists as a manual artifact.** Adjusters hand-write large loss reports with an executive summary, loss description, coverage, jurisdiction, damages, reserves, status, and a deliberately segregated **Conclusions** section. Claim-file audit practice uses pre-transfer document checklists precisely because handoffs lose context. This is the strongest single piece of evidence in the document: someone is already doing this work by hand, and the profession has already decided what belongs in it. (§4.2, §5.2)

3. **The pain has a growing driver, and it is a people problem.** Deloitte's Sept 2025 interviews with 17 chief claims officers: ~20% attrition, each exit costing nearly six years of experience, new-hire productivity down ~15%, error rates climbing against rising complexity. More people are picking up files cold, with less context to bring. (§5.1)

4. **Value concentrates in a minority of claims, and that minority is growing.** Auto physical damage is among the most automated claim categories, while represented bodily-injury claimants wait a median of nearly 440 days to closure and litigation rates roughly doubled. A four-document PD claim needs no synthesis. A 440-day BI file with three handlers does. (§5.1, §5.4)

5. **Incumbents already ship this, and they ship it where the claim lives.** CLARA DocIntel Pro produces chronological summaries with clickable page-level citations. Verisk Discovery Navigator and XactAI ship generative record and note summaries. Guidewire ships auditable claim summarization *inside ClaimCenter*. The unserved gap is narrow but real: they all summarize **medical records**; nobody clearly reconciles the **heterogeneous non-medical auto file**. (§9)

6. **Cross-document faithfulness is genuinely unsolved, and it is the core V1 claim.** Multi-document summarization research reports up to 75% of generated content hallucinated on average, and models producing confident summaries of entirely non-existent topics 44% of the time (GPT-4o) to 79% (GPT-3.5-turbo). Hallucinations cluster toward the end of summaries. Post-hoc mitigation is only moderately effective. (§8.2)

7. **Adoption is a trust problem before an accuracy problem.** Day 1 established that machine-generated output in this workflow starts distrusted — SIU acceptance of automated referrals fell to 15%. If an adjuster verifies every citation, net time saved is zero or negative, and given that claim files are discoverable in litigation, verifying is the *rational* behavior. (§8.5)

## 1.4 The three assumptions that must be tested before any code

Stated in full in §11.1. In short:

1. That the bottleneck is **comprehension**, not **acquisition**.
2. That an adjuster will **rely on** the synthesis rather than re-read the file behind it.
3. That **"material conflict"** is a category two experienced adjusters would agree on.

Assumption 3 is testable in a week with no product (§12). If it fails, the most differentiated feature in V1 is not viable.

---

# 2. Claims workflow

## 2.1 Scope of this section

Day 1 mapped the full lifecycle. This section does not repeat it. It answers the specific question asked this round: **what happens after FNOL, and where in that does synthesis work actually sit?** The stage list is carried forward from Day 1 and re-verified against O*NET; the analysis is new.

## 2.2 The stages after FNOL

Stages overlap heavily. This is not a strict sequence. **[INDUSTRY]**

| # | Stage | What the adjuster is actually doing | Synthesis load |
| --- | --- | --- | --- |
| 1 | **Coverage verification** | Policy in force on DOL? Vehicle scheduled? Driver listed/permissive/excluded? Which coverages, limits, deductibles? Exclusions in play? | **Low.** Structured lookup against the policy system. |
| 2 | **Assignment / segmentation** | Routing by severity, complexity, injury presence, litigation risk, coverage type. Simple clear-liability PD claims go to fast-track; injury and complex claims go to senior adjusters or specialty units. | **Low** for the assigner. **High for the receiver** — this is the handoff moment. |
| 3 | **Investigation / fact-gathering** | Contact insured and claimants, take statements, obtain police report, inspect vehicles, obtain estimates, interview witnesses, obtain medical records and bills, run index/database checks. | **High and continuous.** This is where the file becomes fragmented. |
| 4 | **Liability determination** | Who is at fault and to what degree, under the applicable state negligence regime. | **Highest.** Requires the reconciled account. |
| 5 | **Damages evaluation** | PD: repair estimate vs. ACV, total-loss determination. Injury: medical specials, treatment duration and modality, wage loss, general damages, permanency. | **Medium.** Largely arithmetic over structured data, plus clinical narrative reading. |
| 6 | **Reserving** | Setting and revising the insurer's estimate of ultimate claim cost. | **High, and on a deadline.** Forces a severity judgment on incomplete information. |
| 7 | **Resolution** | Settlement negotiation, payment, or denial. Denials must be explained. | **High.** A denial or a large reserve change requires a written, defensible account. |
| 8 | **Post-resolution** | Subrogation, salvage, inter-carrier arbitration, closure. Claims can reopen. | **Medium.** Subrogation and arbitration require re-presenting the file to an outside party. |

**[INFERENCE]** Reading down the right-hand column, synthesis load is not evenly spread. It spikes at four moments: **assignment/handoff, liability determination, reserve changes, and any point where the file must be presented to someone outside it** (supervisor, arbitrator, opposing carrier, counsel). Those are not "reading the file" moments in general — they are moments where the adjuster must *produce a defensible account*. That distinction matters for the product: the trigger is not "opening a claim," it is "having to explain a claim."

## 2.3 The regulatory clock, and why it sets the product's deadline

Carried forward from Day 1 §A.2, re-verified. **[REGULATION]**

The NAIC Unfair Claims Settlement Practices Act (Model #900) prohibits, among other things, "refusing to pay claims without conducting a reasonable investigation" and "failing in the case of claims denials or offers of compromise settlement to promptly provide a reasonable and accurate explanation of the basis for such actions."

California's Fair Claims Settlement Practices Regulations (10 CCR § 2695.7) put hard numbers on it:

| Requirement | Deadline |
| --- | --- |
| Accept or deny the claim, in whole or in part | No more than **40 calendar days** after proof of claim |
| Written status update if more time needed | Every **30 calendar days** |
| Tender payment after acceptance | No more than **30 calendar days** |
| Notice before statute of limitations expires | **60 days** (30 for UM) |

**[INFERENCE]** Two consequences for a synthesis product, and they pull in opposite directions.

The 40-day accept/deny window and the 30-day status cadence are *recurring forced re-reads of the file*. Every 30 days someone must know enough about the claim to write a status update. On a 440-day represented BI claim (§5.1) that is roughly fourteen forced re-reads. **That is the product's actual usage pattern** — not one dramatic synthesis at pickup, but a repeated "what has changed and what still matters" question. A synthesis that is only useful the first time you open a claim addresses maybe a tenth of the real occasions.

Against that: the regulation also means the "explanation of the basis" is a regulated artifact. Anything the product generates that flows into a denial rationale inherits that regulatory weight. This is not a low-stakes summarization surface.

## 2.4 What the adjuster interacts with

O*NET's occupational profile for Claims Adjusters, Examiners, and Investigators (13-1031.00) documents the tasks — examining claim forms, analyzing information gathered by investigation, reviewing police reports and medical records, interviewing claimants and witnesses, appraising property values, negotiating settlements, verifying accuracy of records, maintaining data in information systems, conferring with legal counsel — and the technology: general office software (Excel, Word, Outlook), claims platforms, estimating software (Xactimate), document management systems, and predictive analytics platforms. **[INDUSTRY]**

**[INFERENCE]** This is the single best public evidence for the fragmentation premise, and it was already the strongest evidence Day 1 found. It is worth being precise about what it does and does not establish. It establishes that the adjuster works across a claims system, an estimating system, a document repository, external database portals, email, and spreadsheets — that the adjuster *is* the integration layer. It does **not** establish that being the integration layer is expensive in time, or that the expense is in comprehension rather than navigation. A tool that eliminated re-reading would not help an adjuster whose actual cost is logging into six systems.

## 2.5 What requires judgment and should not be automated

**[INFERENCE]**, informed by the regulatory material.

| Work | Why it stays human |
| --- | --- |
| Liability determination | Applies state negligence law to contested facts. A legal conclusion. |
| Coverage decisions | Bad-faith exposure. Day 1 §F.3 marked this out of scope and nothing here changes that. |
| Deciding a claimant is not credible | A judgment about a person, made on incomplete information, with discrimination exposure. |
| Deciding an inconsistency is material | Requires knowing what would change the outcome. The system can *propose*; a human must *decide*. See §7.4. |
| Reserve setting | A financial commitment. The system can supply inputs. |
| Settlement negotiation | Interpersonal, strategic, relational. |
| SIU referral | Day 1 §C.1: in California this creates a legal obligation on the SIU. **[REGULATION]** |
| Denial | Regulated, explained, discoverable, and the highest-consequence act in the workflow. |

**[INFERENCE]** Notice that the entire *decision* column is human, and the entire *reading* column is not. That is the actual shape of the opportunity, and it is narrower and less exciting than "AI claims copilot" implies. The product's honest ceiling is: it can make the file legible faster. It cannot make any of the decisions the job is actually evaluated on.

---

# 3. Claim file / document map

Full detail is in **`research/claim-document-map.md`**. This section states only the structural findings that bear on the product hypothesis.

## 3.1 The file is two files

**[INFERENCE]** A personal auto claim file is really two document populations with different characteristics:

- **The core auto layer** — FNOL, policy record, recorded statements, adjuster notes, police report, repair estimate, photographs, correspondence, prior claims, reserves/payments. Heterogeneous: every document has a different format, author, and vocabulary. Mostly available early. Modest in volume — tens of pages.
- **The injury layer** — medical records and bills, IME reports, peer reviews, wage-loss documentation, demand packages, EUO transcripts, litigation documents. Homogeneous in type but enormous in volume — hundreds to thousands of pages. Arrives late and continuously.

This split explains the entire competitive landscape (§9). Incumbents attacked the injury layer, because it is where the page count is, which makes the ROI arithmetic trivial to demonstrate. Nobody clearly attacked the core auto layer, because the page count is low — even though **that is where the contradictions live**. A conflict between a claimant's account and a police report narrative is a core-layer conflict. Two hundred pages of physical therapy notes contain volume, not disagreement.

**[INFERENCE]** If there is a defensible product position in this space, it is on that observation: *value in the injury layer is proportional to page count; value in the core layer is proportional to disagreement.* Incumbents optimised for the first. The second is unclaimed and is what `CLAUDE.md` describes.

## 3.2 Structure varies more than expected

**[INDUSTRY]** The FNOL is not free text. The ACORD Automobile Loss Notice is a standardised form with well over a hundred fields — policy and agency identifiers, loss date/time/location, "Description of Accident" free-text (with ACORD 101 attachable for overflow), authority contacted and report number, insured vehicle and driver, damage description, other vehicles, injured parties, property damaged, witnesses, even child-restraint questions.

**[INFERENCE]** This matters more than it looks. The narrative *content* of an FNOL sits in one or two free-text boxes surrounded by ~100 structured fields. Most FNOL information does not need extraction at all — it needs reading from a database. Any V1 that treats the FNOL as an unstructured document to be parsed is doing avoidable work and introducing avoidable error, and it violates `CLAUDE.md`'s own deterministic-first principle.

The police report is the opposite: a structured state-specific form plus a narrative plus a diagram, with the format varying by state. The repair estimate is highly structured line-item data from CCC, Mitchell, or Audatex. Medical bills carry CPT/ICD codes alongside clinical prose.

**[INFERENCE]** So the honest characterisation is not "claim files are unstructured." It is: **claim files are mostly structured, with a small number of high-value unstructured passages, and the unstructured passages are exactly the ones that disagree with each other.** The narrative boxes and the transcripts are where the product earns its place. Everything else is a database read.

## 3.3 Conflicts live in specific pairs

**[INFERENCE]** This is the most actionable finding for Phase 4 data design. Conflicts are not diffuse across the file; they arise between a small number of document *pairs*:

| Pair | Typical conflict |
| --- | --- |
| FNOL narrative ↔ recorded statement | Vehicle moving vs. parked; who was driving; passengers present |
| Recorded statement ↔ police report narrative | Direction of travel, sequence of impact, right-of-way, speed |
| Narrative mechanism ↔ repair estimate damage location | Rear impact described, side damage estimated |
| Statement ↔ medical records | Injury onset timing, symptom description, prior conditions |
| FNOL/statement ↔ policy record | Who was driving vs. who is a listed driver; garaging location |
| Prior claims ↔ current damage | Pre-existing damage claimed as new |
| Adjuster notes ↔ any of the above | The handler already noticed something and wrote it down |

The synthetic dataset should be built around **these pairs**, not around the document list. A claim file with ten documents and no conflict-bearing pair tests nothing.

---

# 4. Adjuster pain points

## 4.1 What the evidence actually supports

**[EMPIRICAL]** From Deloitte's September 2025 study, based on interviews with 17 chief claims officers at leading P&C insurers:

- Average attrition around **20%**, with each claims professional's exit "resulting in the loss of nearly six years of experience"
- **Productivity among new hires down about 15%**
- **Error rates climbing** as adjusters "struggle to keep pace with rising case complexity"
- Insurers with high turnover among experienced adjusters reporting operational costs up **~12%**
- Organisations relying more heavily on underprepared talent reporting **up to 20% higher indemnity payouts**
- Onboarding a new adjuster costing **US$8,000–10,000** in the first year

Note the methodology honestly: 17 executive interviews is a small qualitative sample, and the respondents are the people whose budgets a talent narrative supports. The numbers are directional, not precise. But the *direction* is corroborated by an independent structural fact — represented BI claims taking a median of nearly 440 days to close (§5.1) — which means a claim can easily outlive the tenure of the person who opened it.

**[INFERENCE]** This is the strongest causal story available for why claim synthesis would be worth money, and it is not the story `CLAUDE.md` tells. The premise is not "reading is slow." The premise is **"the person reading did not do the earlier work, and the person who did has left."** Institutional memory is draining out of claims organisations at ~20% a year in six-year chunks, while claim duration is increasing. The gap between those two curves is the product.

## 4.2 Adjusters already write syntheses by hand

**[INDUSTRY]** When a loss reaches roughly $100,000 or a reserve change takes it there, adjusters write a **large loss report** to summarize claim status for senior management and justify the reserve. Practitioner guidance (Gary Blake, published via Claims Journal 2009 and IRMI 2013) recommends:

- An **RE line** carrying claim handler, report date, current and proposed reserve, policy number, insured, broker, paid-to-date, location, policy term
- An **executive summary** that states the report's purpose immediately rather than opening with background
- A **claim narrative** that "tells the story" by contrasting the positions of claimant and insurer, establishing the plaintiff's view "in a single succinct sentence"
- A separate **Conclusions** section, so that subjective assessment is not mixed into the factual presentation
- **Subheads** for Coverage, Jurisdiction, Damages/Injury, Loss Description, Reserves, Status
- Explicit status labels on individual items — Blake's example distinguishes invoices as "Related and justified," "Unrelated," and "Those requiring further inquiry"

**[INFERENCE]** Four things fall out of this, and they are the most useful paragraphs in this document.

**First — the product's output has a real-world analog.** We are not inventing a format. Adjusters produce this artifact by hand today, and it is expensive enough that a communications consultant makes a living teaching people to write it. That is far better evidence of demand than any survey.

**Second — the profession independently arrived at `CLAUDE.md`'s core principle.** Blake's insistence on a segregated Conclusions section, so opinion never contaminates the factual presentation, is precisely the fact/inference separation `CLAUDE.md` demands. This is strong external validation of an idea the project arrived at on its own.

**Third — the per-item status labels are an output schema.** "Related and justified / Unrelated / Requiring further inquiry" is a resolution status on a fact. That maps directly onto the project's Fact, Conflict, and OpenQuestion entities and suggests they may be **one entity with a status field** rather than three, which is a Phase 3 question worth carrying forward.

**Fourth — and this cuts against us — the large loss report is written at $100k+.** It is a *management reporting* artifact, produced on high-severity claims, not a daily comprehension aid. It confirms the format is valuable; it does not confirm the format is wanted on a routine claim.

## 4.3 Documentation practice confirms that handoffs lose context

**[INDUSTRY]** Practitioner guidance on claims documentation (James DeRosa, Claims Journal, 2014) is organised around "if it's not documented in the file, it doesn't exist," and recommends logging every call, meeting, and inspection; date-stamping photos; **pre-transfer audits using document checklists before files move between departments**; and keeping language factual, with subjective observations included only as direct quotes. The stated purposes include enabling informed decisions by claim managers and **facilitating handoffs between adjusters**.

Adjuster report-writing guidance similarly holds that a reviewer looks for the recommended disposition (pay, deny, reserve, investigate further) with its **evidentiary basis**, and that disputed issues must be identified explicitly rather than buried.

**[INFERENCE]** The existence of a pre-transfer checklist is evidence that handoff information loss is a known, named problem that the profession already spends effort mitigating — with a manual control. A checklist verifies that documents are *present*. It does nothing about whether the receiving adjuster can *understand* them. That gap is where the product would sit, and it is a narrow, specific, defensible gap.

"Disputed issues must be identified explicitly, not buried" is also, in effect, a professional standard requiring the conflict-detection output that V1 proposes.

## 4.4 What is repetitive

**[INFERENCE]**, from the workflow and document map rather than from time studies — no public time study exists (§5.3).

| Repetitive work | Repeats how often |
| --- | --- |
| Re-reading the file to write a 30-day status update | Every 30 days per open claim, per § 2695.7 **[REGULATION]** |
| Rebuilding the chronology from documents with scattered dates | Every handoff, escalation, supervisor review |
| Re-transcribing facts from documents into claims-system fields | Per document received |
| Re-locating a document that supports a specific fact | Every time the file is presented to anyone |
| Checking whether newly arrived documents contradict the existing account | Per document received |

**[INFERENCE]** The last row is the one no incumbent product addresses and the one a human is worst at, because it requires holding the whole file in working memory against each new arrival. It is also the row where a false positive is cheapest — a wrongly flagged difference costs a few seconds of reading, unlike a wrongly flagged fraud signal, which Day 1 established costs regulatory workload.

---

# 5. Evidence for and against the synthesis hypothesis

The instruction was to look for disconfirming evidence, not just supporting evidence. This section is organised so the disconfirming evidence is not buried.

## 5.1 Evidence for

| # | Evidence | Grade | What it supports |
| --- | --- | --- | --- |
| 1 | O*NET 13-1031.00 technology and task list — adjuster spans claims platform, estimating software, document management, external databases, email, Excel | **[INDUSTRY]**, A | Fragmentation is structural, not anecdotal |
| 2 | Deloitte Sept 2025: 20% attrition, ~6 years experience lost per exit, new-hire productivity −15%, error rates rising with complexity | **[EMPIRICAL]**, B (n=17 executives) | Growing population of people reading files they didn't build |
| 3 | IRC: represented BI claimants wait a median of nearly **440 days** to closure, more than double unrepresented; litigation rates roughly doubled (10%→18%); attorney representation rising | **[EMPIRICAL]**, A/B | Claims now routinely outlive their handler's tenure |
| 4 | Large loss reports exist and are taught (§4.2) | **[INDUSTRY]**, B | The output format has a real manual analog and demonstrated cost |
| 5 | Pre-transfer document checklists in standard documentation practice (§4.3) | **[INDUSTRY]**, B | Handoff information loss is a named, already-mitigated problem |
| 6 | § 2695.7's 30-day status cadence on open claims | **[REGULATION]**, A | Forced periodic re-reads — a recurring, not one-off, trigger |
| 7 | Four independent vendors with customer access built claim summarization (§9) | **[INDUSTRY]**, C sources but strong signal | Companies that can talk to buyers concluded the pain is real |
| 8 | Vendor data: 51–57% of auto BI and first-party medical claims involve multiple adjusters; handling time ~2.75–2.85× when they do | **[UNCERTAIN]**, C | Multi-handler files are the norm in exactly the complex segment — see caveat below |

On evidence 8: this comes from Five Sigma's blog presenting unattributed proprietary analysis of "thousands of claims" with no methodology, sample size, or precise date (published July 2022). It is directly on point and I could find nothing else like it, so I record it — graded C, and it must not be used as a load-bearing number. The direction is plausible; the magnitude is unverifiable.

On evidence 7: vendor convergence is genuine evidence — these companies have customer discovery we do not. But it is also the evidence that most undermines the *business* case, since it means the problem is being solved by better-positioned players (§5.5).

## 5.2 The strongest single argument for

**[INFERENCE]** Take evidence 3, 4, and 5 together and the case sharpens considerably.

A represented BI claim runs a median of ~440 days. Adjuster attrition runs ~20% annually. Roughly speaking, **a substantial share of long-lived claims will change hands at least once during their life**, and the departing handler takes about six years of judgment with them. The profession's existing control for this is a checklist that verifies documents are *present* — not that the successor understands them. Meanwhile, on high-severity claims, someone is already paying an adjuster to write the synthesis by hand.

That is a coherent, specific, falsifiable story about where time goes and why the problem is getting worse. It is much stronger than "adjusters read a lot of documents."

## 5.3 Evidence against, part 1: the premise is unmeasured, and the standard citation is fake

This is the most important negative finding, and I am recording the verification failure rather than the number.

The statistic that dominates this space is: *"Research from McKinsey and Accenture consistently shows that claims adjusters spend 50% to 70% of their time on administrative tasks rather than the evaluative and investigative work that determines claim outcomes."* It is repeated across vendor marketing.

**I traced it and it does not hold up.** The search result surfacing it attributes it to a Five Sigma blog post on adjuster workloads. I fetched that post. **It does not cite McKinsey, Accenture, or any external source** — every figure on the page is presented as Five Sigma's own proprietary analysis, with no methodology, no sample size, and no date beyond "the past three months" relative to a July 2022 publication. The companion "60% of time is spent on work about work" figure derives from a general knowledge-work productivity vendor survey, not from claims at all. **[UNCERTAIN]**

**Decision: this figure is barred from the project.** It appears here only inside its own debunking. If it resurfaces in a deck, that deck is wrong.

What remains after removing it: **there is no public study measuring how personal auto adjusters allocate their time.** Day 1 flagged this as open question 6 and could only find adjacent workers' compensation data (Rising's 2019 benchmarking study: 58% of frontline claims professionals spending >20% of time on compliance activity, 14% spending >40%). A second round of searching found nothing better.

**[INFERENCE]** The project's central hypothesis is a quantitative claim about time, and the quantity is unknown for the target user. That is not fatal — the qualitative and structural evidence in §5.1 is real — but it means **no time-savings claim can be made until we measure it ourselves.** It also means the validation experiment in §12 is not optional diligence; it is the only path to the number.

## 5.4 Evidence against, part 2: most personal auto claims are not complex

**[INDUSTRY / UNCERTAIN]** Auto physical damage and glass are among the most mature straight-through-processing categories. Industry-wide P&C STP rates are reported below 10% with a majority of insurers reporting none, while leading personal-lines carriers approach ~35% on eligible claim types; one carrier deployment (Admiral Seguros with Tractable) reports ~90% of auto estimates running touchless with 98% of assessments completed in under 15 minutes. These figures come from vendor and trade sources and should be treated as directional.

**[INFERENCE]** A clear-liability, property-damage-only claim has an FNOL, a policy record, photos, and an estimate. There is no story to reconstruct, no conflicting accounts, and nothing meaningful to put on a timeline. Synthesis adds nothing, and the industry is actively automating these claims out of human hands entirely.

This directly contradicts the framing in `CLAUDE.md` — and in Day 1's §F.1, which argued that synthesis "helps on 100% of claims" while fraud signals matter on ~2%. **That argument was wrong, and it was the argument that drove the pivot.** Synthesis does not help on 100% of claims. It helps on the subset that is long-lived, multi-document, multi-handler, and contested — plausibly the same injury/litigated segment where represented claimants wait 440 days.

The good news is that this segment carries a hugely disproportionate share of loss dollars and adjuster hours. The bad news is that the addressable population is far smaller than the pivot assumed, and the product must be scoped for it deliberately rather than discovering it in user testing.

## 5.5 Evidence against, part 3: this is a crowded market

Detail in §9. Summary: CLARA Analytics, Verisk (twice), Guidewire, and EvolutionIQ all ship claim summarization capability today, with Guidewire's embedded in the system of record where the claim already lives. A standalone synthesis tool has no distribution advantage and must be substantially better on a specific axis to matter.

## 5.6 Evidence against, part 4: the technology is not obviously up to it

Detail in §8.2. Multi-document summarization — the exact task — shows hallucination rates that would be disqualifying in a claims context, and cross-document is materially harder than single-document. Every incumbent above ships **single-corpus** summarization (medical records, claim notes) rather than cross-document reconciliation. **[INFERENCE]** It is worth taking seriously that they may have tried the harder thing and retreated, rather than never having thought of it.

## 5.7 So: real problem, or invented problem?

**[INFERENCE]** **Real problem, mis-scoped, and partially served.**

- The *fragmentation* is real and documented (O*NET).
- The *cost* of fragmentation is undocumented for personal auto and the standard citation is fabricated.
- The *demand* for the output is evidenced by adjusters already producing it by hand at high severity, and by four vendors building it.
- The *population* is much narrower than "every claim."
- The *unserved slice* is narrow but genuine: cross-document reconciliation of the heterogeneous core auto file, as opposed to volume-reduction over medical records.

An honest one-line statement of what we have: **someone is already doing this work by hand on expensive claims, the workforce doing it is losing six years of experience per departure, and the tools that exist attack the page count rather than the disagreement.**

---

# 6. Claim lifecycle and information availability

The most consequential section for everything downstream. Day 1 decision **D-004** requires the evaluation set to be timestamped; this section supplies the timestamps.

## 6.1 The checkpoints

**[INDUSTRY]** for document availability; **[INFERENCE]** for the synthesis-value assessments.

### Checkpoint 1 — FNOL (day 0)

**Available:** the ACORD-style loss notice (structured fields + a short accident description), the policy record from the policy administration system, prior internal claims history, and often an ISO ClaimSearch match. Sometimes an initial photo set from a mobile app.

**Deterministic facts available immediately:** policy in force on DOL, days from inception to loss, days from loss to report, listed-driver check, vehicle-scheduled check, prior claim count and recency, coverage/limits/deductible.

**Not yet available:** any second account of the loss, police report, estimate, medical information, witness statements.

**Synthesis value: near zero.** There is one narrative. Nothing to reconcile, nothing meaningful to place on a timeline beyond dates the claims system already holds. **[INFERENCE]** Building for FNOL means building a form-summarizer, not a synthesis tool.

### Checkpoint 2 — after coverage verification and assignment (days 1–5)

**Adds:** the coverage position, segmentation/routing decision, the adjuster's first contact notes, initial reserve.

**Synthesis value: still low**, with one exception — **[INFERENCE]** this is the first handoff. The intake rep who took the FNOL is not the adjuster who now owns it. The information volume is small enough that the handoff is cheap, but the *pattern* of the product's real trigger appears here for the first time.

### Checkpoint 3 — after the claimant / insured statement (roughly days 5–30)

**Adds:** recorded statement transcript(s) — long, conversational, disfluent, non-linear; further adjuster notes; often the police report; often the first vehicle inspection or photo estimate; witness statements where they exist.

**Synthesis value: this is where it begins.** **[INFERENCE]** The recorded statement is the first document that can disagree with the FNOL, and the police report is the first *independent* account. Two of the highest-value conflict pairs in §3.3 become checkable here for the first time. Before this point the product literally has nothing to do; from this point it does.

### Checkpoint 4 — after supporting documents (roughly days 15–90+)

**Adds:** repair estimate and supplements (CCC/Mitchell/Audatex line items), total-loss valuation if applicable, medical records and bills as they trickle in, wage-loss documentation, correspondence, reserve revisions, attorney representation letter if one arrives.

**Synthesis value: peak.** **[INFERENCE]** All the §3.3 conflict pairs are now live, including narrative-mechanism vs. estimate-damage-location, which needs the estimate. This is also where document arrival becomes *continuous and asynchronous* — the file changes under the adjuster repeatedly, which is precisely the condition under which a human loses track and a machine does not.

### Checkpoint 5 — pre-settlement / demand (days 90–440+)

**Adds:** demand package, complete medical specials, IME report, peer review, EUO transcript if invoked, litigation documents.

**Synthesis value: high, but the buyer changes.** **[INFERENCE]** At this stage the audience for a synthesis is a supervisor approving authority, defense counsel, or a mediator — not the handling adjuster, who by now knows the file. This is where the large loss report gets written (§4.2). It is a *reporting* need, not a *comprehension* need, and it may be a different product.

## 6.2 The availability map

| Information | C1 FNOL | C2 Coverage | C3 Statement | C4 Support docs | C5 Pre-settlement |
| --- | --- | --- | --- | --- | --- |
| Policy terms, limits, deductibles | ✅ | ✅ | ✅ | ✅ | ✅ |
| Loss date / report date / location | ✅ | ✅ | ✅ | ✅ | ✅ |
| Claimant's first account | ✅ (brief) | ✅ | ✅ | ✅ | ✅ |
| Prior claims history | ✅ | ✅ | ✅ | ✅ | ✅ |
| Coverage position | ⬜ | ✅ | ✅ | ✅ | ✅ |
| Initial reserve | ⬜ | ✅ | ✅ | ✅ | ✅ |
| Detailed claimant account (recorded statement) | ⬜ | ⬜ | ✅ | ✅ | ✅ |
| Independent account (police report) | ⬜ | ⚪ | ✅ | ✅ | ✅ |
| Witness statements | ⬜ | ⬜ | ⚪ | ✅ | ✅ |
| Damage detail (estimate) | ⬜ | ⬜ | ⚪ | ✅ | ✅ |
| Injury / treatment detail | ⬜ | ⬜ | ⚪ | ⚪ | ✅ |
| Attorney representation | ⬜ | ⚪ | ⚪ | ⚪ | ✅ |
| Total damages picture | ⬜ | ⬜ | ⬜ | ⚪ | ✅ |

✅ reliably present · ⚪ sometimes present · ⬜ not yet

## 6.3 Conclusion: the earliest useful point

**[INFERENCE]** **Checkpoint 3 (post-statement) is the earliest point where a synthesis product has anything to synthesize, and Checkpoint 4 (post-supporting-documents) is where it becomes clearly valuable.**

Three consequences, all of which bind on later phases:

1. **The evaluation set must be built at C3/C4, not against closed files.** Day 1's §D.3 Evidence 4 recorded Derrig & Francis's warning that closed-claim analysis overstates prospective performance because key variables are unknown until a claim nearly closes. The same trap applies to synthesis: evaluating against a complete file makes conflict detection look easy, because every conflict is visible at once. Real conflicts arrive one document at a time. **This resolves open decision D-007.**

2. **"Open a claim, get the story" is wrong at FNOL.** The promise implies day-zero value the information does not support. Any demo built on an FNOL will be a demo of a form-summarizer.

3. **C3 and C5 may be different products** — comprehension for the handling adjuster versus reporting for a supervisor, counsel, or mediator. Day 1's open decision D-009 framed this as adjuster-versus-SIU; the sharper framing is **comprehension versus reporting**, and V1 should pick comprehension.

---

# 7. Human vs AI task boundary

## 7.1 The table

Legend: ● primary owner · ○ contributes · ✗ must not.

| Task | Human | Rules/code | LLM | Hybrid shape |
| --- | --- | --- | --- | --- |
| Date arithmetic (reporting delay, policy age, treatment lag) | ✗ | **●** | ✗ | None. Pure computation. Using an LLM here is slower, costlier, non-reproducible, and less accurate. |
| Chronological ordering where timestamps are known | ✗ | **●** | ✗ | None. |
| Chronological ordering where dates are *stated in prose* | ○ | ● | ○ | LLM extracts the date expression and its span; code normalises and sorts. |
| Structured field validation (in force, listed driver, vehicle scheduled) | ○ | **●** | ✗ | None. Set membership and range checks. |
| Counts and sums (prior claims, totals, reserves) | ✗ | **●** | ✗ | None. |
| Fact extraction from unstructured narrative | ○ | ✗ | **●** | **The keystone.** LLM emits (fact, document, span). Nothing without a locatable span survives. |
| Fact extraction from *structured* documents (FNOL fields, estimate lines) | ✗ | **●** | ✗ | None — and worth stating explicitly, because §3.2 shows most of the FNOL is fields, not prose. |
| Entity resolution across documents ("Robert Smith" / "Bob Smith" / "R. Smith") | **●** | ○ | ○ | Propose only, always visible, never silently merged. LLMs are confidently wrong here (Day 1 §E.3). |
| Document summarization (one document) | ○ | ✗ | **●** | Lowest-risk LLM task. Verifiable against a single source. |
| Cross-document synthesis / narrative | ○ | ○ | **●** | Generation reads **only extracted-and-cited facts**, never raw documents (§8.4). |
| Comparing two statements of the same event | ○ | ○ | **●** | Requires normalising both to comparable facts first. |
| Identifying a candidate contradiction | ○ | ○ | **●** | Detecting *difference* is the easy part. |
| **Deciding a contradiction is material** | **●** | ○ | ○ | **The hard boundary.** See §7.4. System proposes with reasoning; human decides; the decision is captured. |
| Identifying unresolved / missing information | ○ | ● | ○ | Largely a **completeness checklist** against expected documents for the claim type — mostly rules, not LLM. |
| Assessing whether damage matches described mechanism | **●** | ✗ | ○ | Physical/causal reasoning. Unproven; propose only. |
| Deciding a claim is suspicious | **●** | ✗ | ✗ | Out of V1 scope per `CLAUDE.md`. |
| Deciding to refer to SIU | **●** | ✗ | ✗ | **[REGULATION]** In California this creates a legal obligation on the SIU (Day 1 §C.1). |
| Liability determination | **●** | ✗ | ✗ | Legal conclusion under state negligence law. |
| Coverage decision / denial | **●** | ✗ | ✗ | Bad-faith exposure. |
| Reserve setting | **●** | ○ | ✗ | Code may supply inputs. |

## 7.2 The architecture the table implies

**[INFERENCE]** Reading the ● column top to bottom yields one shape:

```
Structured data ──────────────────────────► deterministic computation ──┐
                                                                        ├──► assembled, cited claim state
Unstructured passages ──► LLM span extraction ──► normalised facts ─────┘           │
                                                                                    ▼
                                                              LLM narration over facts only
                                                                                    │
                                                                                    ▼
                                                                    human materiality decision
```

Three properties worth naming: the LLM never does arithmetic; the generation step never sees a raw document, so it cannot invent from one; and every human decision point produces a labelled datum we can evaluate against (Day 1's open decision D-013).

## 7.3 Where AI genuinely adds value

**[INFERENCE]** Being strict about it, the LLM earns its place in exactly three tasks:

1. **Extracting facts with spans from narrative passages** — recorded statements, police report narratives, adjuster notes, FNOL description boxes, clinical prose. Deterministic code cannot read prose; this is what unlocks everything else.
2. **Detecting candidate differences between normalised facts about the same event** — the one thing a human is genuinely bad at, because it needs the whole file in working memory simultaneously.
3. **Narrating already-extracted facts into readable prose** — real value, lowest risk, and the most replaceable by a template.

Everything else on the table is either deterministic code, or a human decision, or a proposal a human must confirm.

## 7.4 Materiality is the hard boundary

**[INFERENCE]**, reinforcing Day 1 §E.4 rather than repeating it.

People telling the truth about a stressful event are routinely inconsistent. A recorded statement taken three weeks after a collision *will* differ from an FNOL taken twenty minutes after it. Detecting differences is easy; deciding which ones matter is the entire problem.

Two things sharpen this beyond Day 1's treatment:

**Materiality is already the regulator's own filter.** California's SIU investigation-summary requirement demands that a summary address **how a misrepresentation was material to the claim** (10 CCR § 2698.36). **[REGULATION]** We are not inventing the category; we are inheriting a legal one.

**Materiality is claim-specific, not conflict-specific.** Whether "was the vehicle moving?" matters depends on what is in dispute. On a clear-liability rear-end claim with an admitted at-fault party, it may be irrelevant. On a disputed-liability claim it may decide the outcome. **[INFERENCE]** This means materiality cannot be a static rule table, and it may not be learnable from the conflict text alone — the model would need to know what is contested. That is a much harder task than it looks in a demo, and it is the reason assumption 3 in §11.1 is the highest-risk item in this document.

---

# 8. Evidence and grounding requirements

## 8.1 Why the bar is higher here than in general summarization

**[REGULATION / INFERENCE]** Three compounding reasons:

1. **Claim files are discoverable.** Anything the product persists may be read aloud in a deposition years later. Day 1's open decision D-012 raised this; it constrains phrasing far more than a "don't say fraud" rule implies.
2. **Denials require an accurate explanation of basis.** NAIC Model #900 and § 2695.7 make the explanation a regulated artifact. A hallucinated fact that reaches a denial rationale is a compliance event.
3. **The NAIC AI Model Bulletin** (adopted December 2023; adopted in some form by a majority of relevant jurisdictions) requires a written AI Systems Program with validation and testing for errors and unfair discrimination, and holds the **insurer responsible for third-party AI**. **[REGULATION]** Grounding evidence is a procurement gate, not a nicety.

## 8.2 The empirical risk

**[EMPIRICAL]** Research on hallucination in multi-document summarization — the exact task V1 proposes — reports:

- Up to **75% of content in LLM-generated summaries hallucinated on average**
- Models generating confident summaries for **entirely non-existent topics**: GPT-3.5-turbo 79.35% of the time, **GPT-4o still 44%**
- Hallucinations **concentrated toward the end of summaries**
- Two dominant error sources on manual evaluation of 700+ insights: **instruction non-compliance** and **generic content generation** (vague statements substituted for specific ones)
- Simple post-hoc mitigation **"only moderately effective"**

The paper's framing is that multi-document summarization introduces failure modes single-document work does not — information repetition and source diversity — and that the area "remains largely unexplored."

**[INFERENCE]** Three implications, in decreasing order of comfort.

The 44% non-existent-topic figure is the most alarming and the most directly applicable. It is a test of whether a model will refuse. In our setting the equivalent question is: *asked to summarize conflicts in a claim file with no conflicts, does the system report none?* Given `CLAUDE.md`'s requirement that the system "never invent supporting evidence," **a null-input test belongs in the evaluation suite from day one** — a claim file containing zero planted conflicts, where the correct output is an empty conflicts list. If the system invents one, nothing else in the evaluation matters.

"Generic content generation" is the more insidious failure for this product. A summary that says "the accounts contain some differences regarding the circumstances of the loss" is not detectably hallucinated — it is simply useless, and it will pass a naive faithfulness check because it asserts nothing. **[INFERENCE]** Specificity must be an evaluation criterion in its own right, not folded into accuracy.

"Hallucinations concentrated toward summary endings" argues directly for short, structured, field-wise output over long free prose — which is what the large loss report format (§4.2) already gives us.

## 8.3 The risk taxonomy

**[INFERENCE]**, mapped to mitigations.

| Risk | What it looks like in a claim file | Mitigation |
| --- | --- | --- |
| **Hallucination** | A passenger, injury, or witness who appears in no document | Drop-if-uncitable (§8.4); null-input test |
| **Omission** | The one document that contradicts the summary is left out | Completeness scored separately from accuracy; per-document coverage check |
| **Unsupported inference** | "The claimant was likely driving to work" stated as fact | Strict fact/inference separation; inference rendered in a visually distinct channel |
| **Incorrect chronology** | Treatment placed before the loss; statement before FNOL | Ordering done in code from normalised dates, never by the model |
| **Incorrect attribution** | "The police report states X" when the claimant stated X | Attribution to *who asserted it, in which document* — the highest-consequence error type (§8.4) |
| **Source confusion** | Two parties' accounts merged into one narrative | Entity resolution proposed, never silent (§7.1) |
| **Overconfident language** | "The vehicle was parked" instead of "the FNOL records the vehicle as parked" | Assertion framing enforced at the output layer |
| **Generic vacuity** | "There are some inconsistencies in the accounts" | Specificity as an evaluation criterion |
| **Stale synthesis** | Summary reflects the file as of last week | Synthesis versioned and stamped with the document set it covers |
| **Anchoring** | Adjuster adopts the AI's framing and stops looking | Day 1 open question 11 — unresolved, and made worse by a *good* summary |

**[INFERENCE]** Incorrect attribution deserves singling out. In a claim file, "who said this" often matters more than "what was said" — a fact asserted by a police officer, by the claimant, and by the claimant's attorney carry entirely different weight, and conflating them is the error most likely to be both invisible in evaluation and damaging in a deposition. Generic summarization benchmarks do not measure it, so we will have to.

Anchoring deserves the opposite note: it is the one risk where **improving the product makes the risk worse.** A vague summary is ignored. A crisp, well-cited, confident summary is adopted wholesale — including its omissions. There is no purely technical mitigation.

## 8.4 Grounding principles

Proposed operationalisation of `CLAUDE.md`'s "every important statement should be traceable to source evidence." **[INFERENCE]**

**P1 — Span-level citation, not document-level.** A citation names a locatable region: document, page or paragraph or transcript timestamp, and character offsets where available. "FNOL" is not a citation. "FNOL, Description of Accident, chars 412–487" is.

**P2 — Drop, never soften.** A fact whose span cannot be located is discarded, not hedged. `CLAUDE.md` says the system must never invent supporting evidence; the enforceable version is that unciteable content does not reach the output at all. Hedged-but-present content is worse than absent content, because it looks verified.

**P3 — Attribution is to an asserter, not to the claim.** Every extracted fact carries who asserted it in which document. The system never says "the vehicle was parked"; it says "the FNOL records the claimant as reporting the vehicle was parked."

**P4 — Extract, then generate; generation never sees raw documents.** The narration step operates only over the extracted-and-cited fact set. This is the single strongest structural defence against §8.2's failure modes: the model cannot fabricate from a document it cannot see.

**P5 — Absence is stated, not implied.** "No police report is present in the file" is an output. Silence is not. This matters doubly for conflicts: "no conflicts detected" and "conflicts not assessed" must be distinguishable, and Day 1's open question 11 warns that a positive "no signals found" assertion is itself dangerous.

**P6 — The synthesis is versioned against a document set.** Every output records which documents, at which versions, it was derived from. Without this, the discoverability problem becomes unmanageable — nobody can later establish what the system actually saw.

**P7 — Facts, inferences, conflicts, and human decisions are separate types, all the way through.** Not styling on one output blob. `CLAUDE.md` requires the distinction; §4.2 shows the profession independently requires it too (Blake's segregated Conclusions section). If they share a type in the data model, they will eventually be collapsed in the UI.

**P8 — Every proposal a human accepts or rejects is captured.** Dismissed conflicts, corrected facts, rejected entity merges. Day 1's open decision D-013 identified this as the most valuable evaluation data available; it is also the only realistic path to measuring materiality agreement in production.

## 8.5 The trust problem

**[EMPIRICAL / INFERENCE]** Day 1 recorded that SIU acceptance of referrals from automated systems fell to 15% from 22%. Machine-generated output in this workflow starts distrusted, on evidence.

The uncomfortable arithmetic: **if an adjuster verifies every cited fact, the product costs time rather than saving it.** Grounding is what makes verification *possible*; it is not what makes verification *unnecessary*. And in a discoverable file where the adjuster carries professional responsibility, verifying is rational.

**[INFERENCE]** So the metric that actually decides whether this product works is not accuracy — it is **the rate at which users stop checking**, and whether that rate is *justified* by the accuracy. A product that earns unjustified trust is worse than one that earns none. This is measurable in §12 by observing how often participants open the source behind a citation, and it is assumption 2 in §11.1.

---

# 9. Existing product landscape

Not a competitor list. The question is what is already solved, by whom, for whom, and what would remain for us.

## 9.1 The products

### CLARA Analytics — DocIntel Pro + Triage
- **Target user:** adjusters and claims professionals at carriers, MGAs/MGUs, reinsurers, and self-insured organisations; casualty and liability lines.
- **Input:** medical notes and summaries, medical bills, legal demand documents, clinical records.
- **Output:** visit-level summaries organising clinical notes **chronologically by patient visit rather than by page**; "Risk Notes" narratives with synthesized document summaries showing the factors behind a surfaced risk; **clickable in-line citations linking summary statements to original source documents with exact page highlighting**.
- **AI capability:** document intelligence plus predictive triage, integrated (announced July 2026).
- **Claimed outcome:** 83% reduction in time spent reviewing medical records. **[UNCERTAIN]** — vendor assertion, no published methodology.
- **Why it matters to us:** this is the closest existing thing to V1's evidence-grounding concept, already shipping. Chronological reconstruction with page-level citations is not a differentiator we can claim.

### Verisk — Discovery Navigator
- **Target user:** P&C claims professionals handling bodily injury.
- **Input:** medical records.
- **Output:** indexed, de-duplicated records with extracted treatment data plus a generative auto-summary (launched February 2024, built on Amazon Bedrock).
- **Claimed outcome:** up to 90% faster than manual review, up to 95% accuracy. **[UNCERTAIN]** — vendor assertion; "accuracy" is undefined and no methodology is published.
- **Why it matters to us:** establishes that medical-record volume reduction is a mature, commoditised category with an incumbent at scale.

### Verisk — XactAI
- **Target user:** property claims professionals (September 2025).
- **Relevant capability:** **Note Summarization** — condensing long claim notes into short overviews tailored to loss type.
- **Why it matters to us:** adjuster-notes summarization, one of our proposed inputs, is already a shipped feature — in property rather than auto, but the capability transfers trivially.

### Guidewire — ClaimCenter claim summarization
- **Target user:** adjusters using ClaimCenter.
- **Output:** context-aware, **auditable** AI-generated claim summaries embedded in ClaimCenter with full change history.
- **Why it matters to us:** **the most strategically significant entry in this list.** ClaimCenter is a dominant P&C claims system of record. Summarization delivered inside it needs no integration, no separate login, no data-sharing agreement, and no procurement cycle. "Auditable, with change history" also indicates they have already identified grounding and traceability as the requirement. A standalone tool competes with a checkbox.

### EvolutionIQ — claims guidance
- **Target user:** adjusters, examiners, claims leaders.
- **Lines:** **Auto Casualty**, group and individual disability, workers' compensation, income protection.
- **Input/output:** medical records, claim files, policy documents in; tactical guidance, medical insights, severity assessment, return-to-work recommendations, risk alerts, triage prioritisation out.
- **Claimed outcomes:** 5–10 point combined-ratio reduction, 20%+ improvement in handling capacity. **[UNCERTAIN]** — vendor assertions.
- **Why it matters to us:** occupies the adjacent and more valuable position — not "understand the claim" but "what to do next." A product that only explains, while a competitor recommends, is one rung down the value ladder.

### Roots Automation — document indexing
- Document indexing accelerator, validated by Guidewire, focused on classifying and indexing inbound claim documents.
- **Why it matters to us:** the ingestion layer we would need is itself a product with an established vendor.

## 9.2 What the landscape reveals

**[INFERENCE]** Four patterns, and they are more useful than the individual entries.

**Pattern 1 — everyone attacked the medical layer.** CLARA, Discovery Navigator, and EvolutionIQ all centre on medical records. The reason is commercial rather than technical: medical records are the page-count problem, so the ROI story writes itself ("83% less review time"). Reconciling a six-page FNOL against a twelve-page transcript saves minutes, not hours, and does not demo as well — **even though it is where the disagreements are** (§3.1).

**Pattern 2 — everyone does volume reduction, not reconciliation.** Every product summarizes *within* a corpus. CLARA organises clinical notes chronologically; Discovery Navigator indexes and de-duplicates; XactAI condenses notes. **I found no product claiming to surface contradictions between a claimant's statement and a police report.** That is either a genuine gap or evidence that it is hard enough that funded teams passed on it — §5.6 — and §8.2 suggests the latter is plausible.

**Pattern 3 — the winning position is inside the system of record.** Guidewire's embedded summarization is a structurally superior distribution position that no standalone product can match.

**Pattern 4 — the frontier is moving from summarization to guidance.** EvolutionIQ sells next-best-action. Summarization is becoming table stakes. **[INFERENCE]** By the time a V1 synthesis tool were built, "summarize the claim" may be a commodity feature — which strengthens rather than weakens the case for scoping V1 around conflicts and open questions, since those are the parts nobody has commoditised.

## 9.3 What V1 would have to do differently

**[INFERENCE]** To be worth building, V1 must claim a position none of the above occupies. The only defensible one visible:

> **Cross-document reconciliation of the heterogeneous non-medical auto file** — FNOL against recorded statement against police report narrative against repair estimate — surfacing *material* disagreement and *unresolved* questions with span-level evidence, at the handoff moment.

Explicitly **not**: summarizing medical records (CLARA, Verisk own it), condensing adjuster notes (XactAI), generic claim summaries in the system of record (Guidewire), or next-best-action (EvolutionIQ).

Two hard caveats. This is a *feature-sized* position, not a company-sized one — appropriate for a learning project, and it should not be dressed up as a market opportunity. And it depends entirely on materiality being tractable (§7.4), which is untested.

---

# 10. Product implications

## 10.1 Reframe the promise

**[INFERENCE]** "Open a claim. Get the story" is wrong in three ways: it implies day-zero value the information does not support (§6.3), it implies every claim (§5.4), and it describes what Guidewire already ships (§9.1).

Closer to what the evidence supports:

> **"Inherit a claim without inheriting the guesswork."**

That names the user (someone who did not open this claim), the moment (handoff/pickup), the segment (files big enough that inheriting is hard), and the value (not re-deriving what a predecessor already knew).

## 10.2 Segment deliberately

**[INFERENCE]** V1 targets claims that are: **open more than ~60 days**, containing **at least one recorded statement plus one independent account**, with **more than one handler** or an imminent handoff, and **contested on liability or damages**. Everything else is out of scope by construction — a clear-liability PD claim is not a small version of this problem, it is a different problem that does not need the product.

## 10.3 Output structure

**[INFERENCE]** `CLAUDE.md`'s six output sections survive contact with the research, with adjustments the evidence forces:

| `CLAUDE.md` output | Verdict | Adjustment |
| --- | --- | --- |
| Claim summary | Keep | Short and structured, not free prose — §8.2 puts hallucinations at the end of long generations. Borrow the large loss report's subheads (§4.2). |
| Timeline | Keep | Built in **code** from normalised dates (§7.1). Must show *when each fact became known*, not only when events occurred — that is what a successor actually needs. |
| Key facts | Keep | Split by provenance: structured-system facts (no LLM) vs. extracted facts (LLM + span). Users trust these differently and should see which is which. |
| Conflicting information | **Keep — this is the differentiator** | Must carry a materiality assessment and a human accept/dismiss action (§7.4, P8). Untested; see §11.1. |
| Open questions | **Promote** | Possibly the highest-value section, and mostly deterministic — a completeness checklist against expected documents. Also the hedge if assumption 1 fails (§11.1). |
| Evidence | Keep | Span-level, per P1–P3. Not a section — a property of every other section. |

**[INFERENCE]** One addition the research argues for and `CLAUDE.md` does not have: **"what changed since you last looked."** The § 2695.7 30-day cadence (§2.3) and the continuous asynchronous document arrival at C4 (§6.1) both point at a recurring rather than one-shot need. A diff is also cheaper, more verifiable, and less prone to the vacuity failure than a full re-synthesis.

## 10.4 The verdict, stated plainly

### PROMISING BUT UNVALIDATED

**Why not STRONG SIGNAL.** The central time claim is unmeasured for personal auto and its standard citation is fabricated (§5.3). The output format's only documented real-world analog is a $100k+ management reporting artifact, not a routine comprehension aid (§4.2). Four funded competitors already ship the general capability, one inside the system of record (§9). The core technical claim — cross-document synthesis — sits on research showing up to 75% hallucinated content and 44% confabulation on non-existent topics (§8.2). No claims professional has been asked anything yet.

**Why not WEAK SIGNAL or PIVOT.** The fragmentation is documented at Grade A (O*NET). The pain has a growing, specific driver: ~20% attrition at ~6 years of experience per exit, against claims running a median 440 days when represented (§5.1). Adjusters already produce this artifact by hand and pay to learn how (§4.2). The profession has a *manual control* for handoff information loss, which is direct evidence of the failure mode (§4.3). And there is a genuine unserved slice — everyone does volume reduction inside one corpus; nobody does reconciliation across the heterogeneous auto file (§9.2).

**What "unvalidated" specifically means.** Zero claims professionals consulted. The core hypothesis is a time claim with no measurement. The most differentiated feature depends on materiality being tractable, which nobody has tested. §12 exists to fix all three, and no application code should be written first.

**The scope correction, which is not optional.** `CLAUDE.md` and Day 1's §F.1 assert that synthesis "helps on 100% of claims." **That is not supported and the research contradicts it** (§5.4). It was also the argument that drove the pivot away from fraud. The pivot still looks right — for different and better reasons — but the reasoning behind it needs replacing, not preserving.

---

# 11. Major uncertainties

## 11.1 The three highest-risk assumptions

Ordered by how much of the product they invalidate.

### Assumption 1 — The bottleneck is comprehension, not acquisition

**The claim:** adjusters lose meaningful time understanding information they already have.

**Why it might be false.** No public study measures where personal auto adjuster time goes (§5.3). The plausible alternative is that far more time goes to *waiting for and chasing* information — police reports, medical records, callbacks, shop supplements — than to reading what has arrived. The Day 1 workers' compensation data pointed at *compliance activity*, not reading. Practitioner accounts of what adjusters chase in the first hour are about missing documents, not confusing ones.

**If false:** the product inverts. Open Questions becomes the primary output and the summary becomes supporting context. Much of that is deterministic — a completeness checklist against expected documents — which would mean **the LLM is largely unnecessary for the valuable part.** `CLAUDE.md` explicitly demands we say so if AI is unnecessary; this is the scenario in which that is true.

**Test:** §12, metric 5 — the ratio of "what's missing" to "what's here" in participants' unprompted next-step lists.

### Assumption 2 — Adjusters will rely on the synthesis rather than re-read behind it

**The claim:** a well-cited synthesis substitutes for reading the underlying documents.

**Why it might be false.** Machine output in this workflow starts distrusted on evidence — 15% SIU acceptance of automated referrals (§8.5). Claim files are discoverable and the adjuster carries professional responsibility, so verification is rational, not paranoid. Grounding makes verification *possible*; it does not make it *unnecessary*. If every cited fact is checked, net time saved is zero or negative.

**If false:** the value proposition changes from time saved to error reduction and confidence — a real but much harder benefit to sell and to measure, and one that does not support "reduce the time required to understand a complicated claim" as `CLAUDE.md` frames it.

**Note the trap:** the *good* outcome here is not maximum trust. It is trust calibrated to actual accuracy. A product that earns unjustified trust is worse than one that earns none, because §8.3's anchoring risk gets worse as the summary gets better.

**Test:** §12, metric 4 — observed rate of opening source documents behind citations.

### Assumption 3 — "Material conflict" is a category experienced adjusters agree on

**The claim:** materiality is a real, learnable, evaluable category.

**Why it might be false.** Truthful people are inconsistent about stressful events (§7.4, Day 1 §E.4). Materiality is claim-specific rather than conflict-specific — it depends on what is contested, which the conflict text alone does not reveal. If two experienced adjusters disagree about which conflicts matter, **there is no ground truth**: no training target, no evaluation criterion, and no defensible product behaviour.

**If false:** the conflict feature — the only differentiated part of V1 (§9.3) — is not viable, and V1 collapses into commodity summarization that Guidewire already ships inside the system of record.

**This is the single highest-risk item in the project.** Day 1 named it the highest-value experiment available before building anything; it remains untested. §12 is designed primarily around it.

**Test:** §12, metric 2 — inter-rater agreement on materiality across 5–8 practitioners on identical planted conflicts.

## 11.2 Other open uncertainties

| # | Uncertainty | Blocks | Status |
| --- | --- | --- | --- |
| U-1 | How personal auto adjusters actually spend their time | Any time-savings claim | **Unresolved.** Day 1 open question 6; second search round found nothing. §12 gives us our own small measurement. |
| U-2 | Whether an LLM can produce span-accurate extraction on disfluent recorded-statement transcripts | Entire architecture | Untested. Cheap to test once synthetic transcripts exist. |
| U-3 | Base rate of *ordinary* inconsistency between honest accounts | Threshold setting, synthetic realism | Unresolved. Day 1 open question 10. If 30% of honest claim files contain a discrepancy, detection without materiality filtering is useless. |
| U-4 | Whether synthetic claim files are realistic enough for practitioners to engage with | §12's validity, all evaluation | Untested and load-bearing. If practitioners reject the fixtures, the experiment measures nothing. Mitigate by piloting with one participant first. |
| U-5 | Jurisdiction / tort regime for V1 | Regulatory framing, some signals | Open (D-006). Less blocking for synthesis than it was for fraud. |
| U-6 | Whether the C3 comprehension product and the C5 reporting product are the same product | Scope | Newly surfaced (§6.3). V1 should pick comprehension. |
| U-7 | Whether entity resolution across documents is reliable enough to propose at all | Cross-document synthesis quality | Untested. Day 1 §E.3 flagged LLMs as confidently wrong here. |
| U-8 | Whether "no conflicts found" can be safely asserted | Output design | Open (Day 1 question 11), sharpened by §8.2's 44% non-existent-topic finding. |

## 11.3 What would change the verdict

**Toward STRONG SIGNAL:** practitioner materiality agreement clearly above chance; the aided condition measurably faster with equal or better recall of material conflicts; participants spontaneously describing handoff comprehension as a real cost.

**Toward PIVOT:** next-step lists dominated by acquisition rather than comprehension (→ pivot to a completeness/open-questions product, likely with far less LLM in it); or materiality agreement near chance (→ conflict detection dies and V1 has no differentiator).

**Toward WEAK SIGNAL:** practitioners reporting that their claims systems already surface this adequately, or that they simply do not re-read files at handoff because they rely on the predecessor's notes — which would make the adjuster's own summary the incumbent, not Guidewire's.

---

# 12. Recommended next experiment

Smallest thing that tests all three assumptions in §11.1, needs no product, and can be built in about a week.

## 12.1 Design

**Test the format before betting on the technology.** The aided condition uses a **hand-written** synthesis in the proposed output format — Wizard of Oz, no model involved. If a *perfect* synthesis does not help, no model will. This also removes model quality as a confound, which at this stage would otherwise dominate the result.

## 12.2 Participants

5–8 people with personal auto liability or BI handling experience: current adjusters, former adjusters, independent adjusters, claims consultants, claims trainers. Former adjusters are easier to recruit and can speak more freely; at least two current handlers would be better.

Not enough for statistical significance. Enough to detect a large effect and — the actual purpose — to measure inter-rater agreement on materiality, which needs several raters on identical material rather than many participants.

## 12.3 Materials

Two synthetic claim files at Checkpoint 4 (§6.3), each ~10–15 documents: FNOL, policy record, recorded statement transcript, police report with narrative, repair estimate, adjuster notes, correspondence, prior claims summary, and for one file a medical records excerpt.

Each file carries **planted conflicts of deliberately varied materiality** — some clearly material (who was driving; vehicle moving vs. parked on a disputed-liability claim), some clearly immaterial (time of day off by an hour; colour of the other vehicle), and **deliberately several in the ambiguous middle, because the middle is what the experiment is actually about**. Ground truth is our authored intent, and per Day 1 decision D-003 that is explicitly *what we planted*, not what would occur in a real claim.

One file must also contain a **section with zero planted conflicts**, to test the §8.2 confabulation failure — against the human baseline as well as, later, the model.

## 12.4 Protocol

Within-subject, counterbalanced, two sessions per participant.

**Session A (unaided baseline).** Given the raw file, participant thinks aloud while forming an account of what happened. **Timed to the point they say they are confident.** Then, without the file:
1. Recount what happened.
2. List every conflict noticed; rate each **material / immaterial / unsure**, with a one-line reason.
3. List what they would obtain or do next.

**Session B (aided).** Different claim, counterbalanced order, same task — but starting from the hand-written synthesis, with the full file available. **Whether and how often they open the underlying documents is observed and counted; participants are not told this is being measured.**

Close with behavioural questions only: "When did you last inherit a claim mid-stream — walk me through what you did first." "What did you have to go find?" Never "would you use this?"

## 12.5 Metrics

| # | Metric | Tests | Supports hypothesis if |
| --- | --- | --- | --- |
| 1 | Time to a confident account, aided vs. unaided | Core value | Aided clearly faster with no loss of accuracy |
| 2 | **Inter-rater agreement on materiality** (Krippendorff's α or pairwise) | **Assumption 3** | **Meaningfully above chance — this is the headline number** |
| 3 | Recall of planted material conflicts, aided vs. unaided | Conflict feature value | Aided recall ≥ unaided, especially on conflicts requiring three or more documents |
| 4 | Rate of opening source documents behind cited claims | **Assumption 2** | Spot-checking, not systematic re-reading |
| 5 | Ratio of acquisition to comprehension items in next-step lists | **Assumption 1** | Comprehension items present and substantial |
| 6 | False conflicts reported in the zero-conflict section | Baseline for §8.2 | Near zero for humans — establishes the bar for the model |
| 7 | Unprompted mentions of handoff/inheritance as a real cost | §10.1 framing | Multiple spontaneous mentions |

## 12.6 Decision rules, set in advance

Committing now, before seeing data.

**Proceed to Phase 3** if metric 2 shows meaningful agreement **and** metric 1 shows a time reduction **and** metric 5 shows comprehension items are a real share of next steps.

**Proceed with narrowed scope** if metric 2 is weak but metrics 1 and 3 are positive: drop conflict detection to a "differences noted, materiality not assessed" presentation and compete on timeline plus evidence assembly — accepting that this is close to what incumbents ship.

**Pivot** if metric 5 is dominated by acquisition: the product becomes completeness and open-questions tracking, mostly deterministic, and we say plainly that the LLM is largely unnecessary.

**Stop** if metric 2 is at chance **and** metric 1 shows no time reduction: the differentiated feature is unbuildable and the undifferentiated one is already shipped by Guidewire.

## 12.7 What this deliberately does not test

Model quality (the aided condition is hand-written by design), real claim files (synthetic only, per D-003), long-term adoption and anchoring, and whether an insurer would buy it. Those come later and are not what currently blocks the project.

---

## Appendix — findings carried forward from Day 1

Still load-bearing, re-cited rather than re-argued. Full treatment in `research/claims-workflow-old.md`.

1. **The regulatory clock** — § 2695.7's 40-day accept/deny and 30-day status cadence. **[REGULATION]** Now reinterpreted (§2.3) as the product's recurring usage trigger rather than a fraud-investigation extension.
2. **Claim files are discoverable in litigation.** **[INFERENCE]** Constrains everything the product persists (§8.1). Day 1 open decision D-012, still open.
3. **Machine output starts distrusted** — 15% SIU acceptance of automated referrals. **[EMPIRICAL, secondary]** Now assumption 2 (§11.1).
4. **Materiality is the hard part of inconsistency detection**, and it is the regulator's own filter (§ 2698.36). **[REGULATION + INFERENCE]** Now assumption 3.
5. **Closed-file evaluation overstates prospective performance** (Derrig & Francis). **[EMPIRICAL]** Decision D-004; §6.3 supplies the checkpoints that make it actionable.
6. **Ground truth means suspicion, never adjudicated fraud.** **[EMPIRICAL]** Decision D-003; extends to synthetic conflicts, which measure only what we planted.
7. **The NAIC AI Model Bulletin** makes evaluation evidence a procurement gate, with the insurer responsible for third-party AI. **[REGULATION]** §8.1.
8. **Day 1 §F.1's claim that synthesis "helps on 100% of claims" is contradicted** by §5.4. The pivot's conclusion survives; its reasoning does not.
