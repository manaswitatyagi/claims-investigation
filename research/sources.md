# Sources — Claims Synthesis Research

Sources for `research/claims-synthesis-research.md` and `research/claim-document-map.md`. Retrieved 2026-08-07.

The Day 1 fraud-era source index is preserved unchanged at **`research/sources-old.md`** and supports `research/claims-workflow-old.md`. A small number of Day 1 sources are re-cited here where this round's documents depend on them directly; those entries say so.

## Grading

Per decision D-001. Every source is graded and every limitation stated.

- **A — Primary/authoritative.** Statute, regulation, government occupational data, or a study with a stated methodology from a body without a direct commercial interest in the answer.
- **B — Reputable secondary.** Industry body, professional press, practitioner reference, or research reported at one remove. Reliable but derivative.
- **C — Interested party.** Vendor, advocacy organisation, or marketing content. Useful for practitioner vocabulary, product capability, and market framing. **Treat every number with suspicion.**

Research question mapping uses the numbering from the Phase 2 brief: **RQ1** adjuster workflow · **RQ2** claim file · **RQ3** where synthesis is difficult · **RQ4** what a useful summary contains · **RQ5** information availability · **RQ6** human/AI boundary · **RQ7** evidence and grounding · **RQ8** existing products · **RQ9** validation plan.

---

# Occupational and workforce evidence

**O*NET OnLine — Claims Adjusters, Examiners, and Investigators (13-1031.00)**
US Department of Labor / National Center for O*NET Development · https://www.onetonline.org/link/summary/13-1031.00 · continuously updated, accessed 2026-08-07
**Grade A.** Supports **RQ1**, **RQ3**.
The authoritative, non-commercial account of what adjusters do and which systems they use. Its technology list — claims platform, estimating software (Xactimate), document management, external databases, Excel, Outlook — is the strongest public evidence that the adjuster is the integration layer across fragmented systems, and therefore the factual basis of the project's fragmentation premise. Re-cited from Day 1, where it was the single best support for the same claim.
**Limitation:** establishes *that* fragmentation exists, not what it *costs* in time. It cannot carry a time-savings claim on its own, and §5.3 of the research document explains why nothing else public can either.

**"Soft skills solve claims management shortage crisis"**
Deloitte Insights · https://www.deloitte.com/us/en/insights/industry/financial-services/soft-skills-claims-management-shortage.html · 18 September 2025
**Grade B.** Supports **RQ1**, **RQ3**.
The most important new source in this round. Based on interviews with **17 chief claims officers** at leading P&C insurers. Reports ~20% average attrition with each departure "resulting in the loss of nearly six years of experience"; new-hire productivity down ~15%; rising error rates against increasing case complexity; ~12% higher operational costs at insurers with high experienced-adjuster turnover; up to 20% higher indemnity payouts where organisations lean on underprepared talent; US$8,000–10,000 first-year onboarding cost per adjuster.
**Why it matters:** supplies the causal mechanism the synthesis hypothesis was missing. The problem is not that reading is slow — it is that the person reading did not do the earlier work and the person who did has left.
**Limitation:** n=17 executive interviews is a small qualitative sample, and the respondents are precisely the people whose budgets a talent-crisis narrative supports. Graded B, not A, for that reason. Directionally corroborated by independent evidence on claim duration (IRC, below).

---

# Claim duration, complexity, and segment evidence

**"Attorney Involvement in Auto Injury Claims" / "Study Finds More Auto Injury Claimants Are Hiring Attorneys"**
Insurance Research Council · https://insurance-research.org/auto-injury-claims-trends/attorney-involvement-auto-injury-claims and https://insurance-research.org/news/study-finds-more-auto-injury-claimants-are-hiring-attorneys · study series, accessed 2026-08-07
**Grade A methodology / B access.** Supports **RQ3**, **RQ5**.
Source of the finding that **represented BI claimants wait a median of nearly 440 days to claim closure — more than double unrepresented claimants**, that litigation rates roughly doubled (10% → 18%), and that attorney representation has risen over successive studies (36% of PIP claimants in 2012, up from 31% in 2007). IRC's newer Auto Injury Claims Analytics Database is described as covering over 7.4 million claims.
**Why it matters:** the 440-day median is the structural fact that makes the handoff hypothesis coherent — a claim that runs well over a year will routinely outlive its handler's tenure at ~20% annual attrition. It also identifies precisely which segment is worth building for.
**Limitation:** graded B for access, not method. **Only summaries and press releases are public; the full reports are paywalled**, and specific figures here were read via IRC's own summaries and secondary reporting rather than the underlying reports. Different figures come from different study years and should not be treated as a single consistent series.

---

# Claim summary format and documentation practice

**"Five Tips on Writing Large Loss Reports"**
Gary Blake, The Communication Workshop, via *Claims Journal* · https://www.claimsjournal.com/news/national/2009/05/13/100476.htm · 13 May 2009
**Grade B.** Supports **RQ4** — the single most useful source for the output schema.
Establishes that adjusters hand-write structured claim syntheses when a loss reaches ~$100,000 or a reserve change takes it there, that the audience is senior management, and that the purpose is to summarize status and justify reserves. Supplies the recommended structure: an **RE line** (claim handler, report date, current and proposed reserve, policy number, insured, broker, paid-to-date, location, policy term); an **executive summary** stating purpose immediately; a **claim narrative** contrasting claimant and insurer positions with "the plaintiff's view in a single succinct sentence"; a segregated **Conclusions** section keeping subjective assessment out of the factual presentation; and subheads for Coverage, Jurisdiction, Damages/Injury, Loss Description, Reserves, Status.
**Why it matters:** the product's proposed output already exists as a manual artifact that professionals pay to learn to write — far better evidence of demand than any survey. The insistence on a segregated Conclusions section is independent professional confirmation of `CLAUDE.md`'s fact/inference separation principle.
**Limitation:** 2009, single practitioner author, and describes a **$100k+ management reporting** artifact rather than a routine comprehension aid. It confirms the format is valuable; it does not confirm the format is wanted on an ordinary claim. The research document states this caveat explicitly.

**"Organizing Large Insurance Loss Reports"**
Gary Blake, via IRMI Expert Commentary · https://www.irmi.com/articles/expert-commentary/organizing-large-insurance-loss-reports · 1 November 2013
**Grade B.** Supports **RQ4**.
Companion to the above from the same author. Adds the section vocabulary (Attachments, Cause of Loss, Adjustment, Subrogation) and, more usefully, the recommendation to attach **explicit status labels to individual items** — the example distinguishes invoices as "Related and justified," "Unrelated," and "Those requiring further inquiry."
**Why it matters:** those three labels are a resolution status on a fact, which maps onto the project's Fact / Conflict / OpenQuestion entities and raises the Phase 3 question of whether they are one entity with a status field rather than three.
**Limitation:** same author as the preceding source, so the two are not independent corroboration.

**"Quality Insurance Claims Documentation Guidelines"**
James DeRosa, via *Claims Journal* · https://www.claimsjournal.com/news/national/2014/02/20/244768.htm · 20 February 2014
**Grade B.** Supports **RQ1**, **RQ4**.
Organised around "if it's not documented in the file, it doesn't exist." Recommends logging every call, meeting, and inspection; date-stamping photos; **pre-transfer audits using document checklists before files move between departments**; and factual language with subjective observations included only as direct quotes. States that quality documentation exists partly to **facilitate handoffs between adjusters** and enable informed decisions by claim managers.
**Why it matters:** the pre-transfer checklist is direct evidence that handoff information loss is a known, named problem the profession already spends effort mitigating — with a manual control that verifies documents are *present* but does nothing about whether a successor *understands* them. That gap is where the product sits.
**Limitation:** practitioner opinion piece, 2014, no methodology.

**Adjuster report-writing and claim-file review standards (practitioner compilations)**
Adjuster Authority / National Claims Adjuster Authority · https://adjusterauthority.com/adjuster-report-writing-standards/ · accessed 2026-08-07
**Grade C.** Supports **RQ4**.
Used only for practitioner vocabulary around what a file reviewer looks for: recommended disposition (pay, deny, reserve, investigate further) stated with its **evidentiary basis**, disputed issues identified explicitly rather than buried, reserve figures recorded with their factual basis, and notes kept factual rather than emotional.
**Limitation:** SEO-oriented practitioner content of uncertain authorship with no sourcing. Used for framing only; **no numbers taken from it**. The "disputed issues must be explicit" standard is corroborated by the Blake and DeRosa sources above, which is why it survived into the research document.

---

# Claim documents — primary form specifications

**ACORD Automobile Loss Notice (form and index)**
ACORD · https://www.acord.org/docs/default-source/forms/forms_index.pdf and specimen copies at https://www.cfins.com/wp-content/uploads/2021/04/ACORD-Automobile-Loss-Notice-12.05.16.pdf, https://www.mabe.org/wp-content/uploads/2012/01/AutoLossNotice.pdf · form revision 12.05.16
**Grade A (form itself) / B (as accessed).** Supports **RQ2**, **RQ5**.
The industry-standard FNOL form. Establishes the field structure used in `claim-document-map.md` §2.1: policy and agency identifiers, loss date/time/location, "Description of Accident" free text with ACORD 101 attachable for overflow, "Police or Fire Department Contacted" with authority name and report number, insured vehicle and driver, damage description, other vehicles, injured parties, property damaged, witnesses, child-restraint questions.
**Why it matters:** demonstrates that an FNOL is ~100+ structured fields around one or two narrative boxes — which means most FNOL information should be read from a database, not extracted by a model. This is the finding that keeps V1 honest against `CLAUDE.md`'s deterministic-first principle.
**Limitation, stated plainly:** the specimen PDFs could not be machine-read (one returned HTTP 403, the other is encrypted with 144 undecodable field identifiers). **The field list was assembled from field-level descriptions in search results and secondary form documentation, not by reading a rendered form.** It is very likely correct in substance and should be verified against a rendered form before any schema depends on it.

**Police Officer's Crash Report Manual, Publication 153**
Pennsylvania Department of Transportation · https://www.pa.gov/content/dam/copapwp-pagov/en/penndot/documents/travelinpa/safety/documents/pub153.pdf · accessed 2026-08-07
**Grade A.** Supports **RQ2**.
Cited as a concrete example that police crash reports are governed by **state-specific** specifications — structured form plus officer narrative plus scene diagram, with field names and coding schemes varying by state.
**Limitation:** used only to establish state variation and the general three-part structure; the manual's specific fields were not extracted, and Pennsylvania was chosen as an available exemplar, not because it is the target jurisdiction (open decision D-006).

---

# Grounding, faithfulness, and hallucination

**"From Single to Multi: How LLMs Hallucinate in Multi-Document Summarization"**
Guo, Xiao et al. (arXiv 2410.13961; NAACL Findings 2025) · https://arxiv.org/abs/2410.13961 · 2024–2025
**Grade A.** Supports **RQ7** — the most important technical source in this round.
Directly addresses the exact task V1 proposes. Finds that **up to 75% of content in LLM-generated summaries was hallucinated on average**; that models generate confident summaries for **entirely non-existent topics** 79.35% of the time (GPT-3.5-turbo) and **44% of the time (GPT-4o)**; that hallucinations concentrate toward summary endings; that manual evaluation of 700+ insights identifies **instruction non-compliance** and **generic content generation** as the two dominant error sources; and that simple post-hoc mitigation is "only moderately effective." Notes that hallucination in multi-document summarization "remains largely unexplored" relative to single-document work.
**Why it matters:** supplies the empirical risk floor for cross-document synthesis, and directly motivates three design decisions in §8.4 — extract-then-generate with the generator blind to raw documents, short structured output over long prose, and a **null-input test** (a claim file with zero planted conflicts) as a day-one evaluation case.
**Limitation:** general-domain multi-document summarization, not claim files, and the headline percentages depend on task setup. The *shape* of the findings transfers; the exact numbers should not be quoted as our expected error rate. Read via the arXiv abstract page — the full PDF did not extract cleanly.

**Faithfulness and citation-attribution evaluation literature (survey level)**
Various, via ACL Anthology and arXiv · e.g. https://aclanthology.org/2025.findings-naacl.293.pdf, https://aclanthology.org/2025.emnlp-industry.54/ · 2025
**Grade A (venues) / B (as used).** Supports **RQ7**.
Used only to establish that verifiable grounding through citation faithfulness is an active, recognised evaluation axis — including in legal AI, where audits of both general-purpose and domain-specific systems consistently find a substantial fraction of claims uncited or misattributed.
**Limitation:** consulted at abstract and search-summary level to establish that the field exists and what it measures. **No specific quantitative finding from these papers is relied on** in the research documents. Worth reading properly before the Phase 6 evaluation framework is designed.

---

# Existing products

All vendor sources. **Graded C without exception.** Every quantified outcome below is a vendor assertion with no published methodology, and is recorded as such in the research document — these are precisely the numbers decision D-001 exists to stop from hardening into premises.

**CLARA Analytics — DocIntel Pro + Triage integration**
CLARA Analytics, via syndicated press release · https://lasvegassun.com/news/2026/jul/27/clara-analytics-introduces-industry-first-integrat/ and https://claraanalytics.com/ · 27 July 2026
**Grade C.** Supports **RQ8**.
The closest existing product to V1's concept. Ingests medical notes, medical bills, legal demand documents, and clinical records; outputs **visit-level summaries organising clinical notes chronologically by patient visit rather than by page**, "Risk Notes" narratives showing the factors behind a surfaced risk, and **clickable in-line citations linking summary statements to source documents with exact page highlighting**. Target user: adjusters at carriers, MGAs/MGUs, reinsurers, and self-insured organisations, in casualty and liability lines.
**Claimed outcome:** 83% reduction in time spent reviewing medical records — **vendor assertion, basis not disclosed in the announcement**.
**Why it matters:** chronological reconstruction with page-level citations is already shipping. It is not a differentiator V1 can claim.

**Verisk — Discovery Navigator (generative AI record summary)**
Verisk · https://www.verisk.com/company/newsroom/verisk-launches-generative-ai-tool-to-support-faster-insurance-claim-processing/, https://www.verisk.com/products/discovery-navigator/, https://www.verisk.com/company/newsroom/verisks-ai-powered-innovation-cuts-medical-records-review-time-by-up-to-90/ · generative summary feature launched 8 February 2024
**Grade C.** Supports **RQ8**.
Medical record review for P&C bodily injury: indexing, de-duplication, extraction of treatment data, and an automated generative summary built on Amazon Bedrock.
**Claimed outcomes:** up to 90% faster than manual review, up to 95% accuracy — **vendor assertions; "accuracy" is undefined and no methodology is published**.
**Limitation:** the Verisk product and newsroom pages are JavaScript-rendered and returned title-only content to automated fetching. Details were assembled from search-result summaries and the Reinsurance News report of the same launch.

**Verisk — XactAI**
Verisk, via GlobeNewswire · https://www.verisk.com/company/newsroom/verisk-introduces-new-ai-tools-to-streamline-the-property-claims-experience/ and https://www.globenewswire.com/news-release/2025/09/30/3158573/0/en/Verisk-Introduces-New-AI-Tools-to-Streamline-the-Property-Claims-Experience.html · 30 September 2025
**Grade C.** Supports **RQ8**.
Property claims AI suite; relevant capability is **Note Summarization**, condensing long claim notes into short overviews tailored to loss type.
**Why it matters:** adjuster-notes summarization — one of V1's proposed inputs — is a shipped feature. Property rather than auto, but the capability transfers trivially.
**Limitation:** page body not retrievable by automated fetch; capability description taken from the release summary.

**Guidewire — ClaimCenter claim summarization**
Guidewire · https://www.guidewire.com/products/technology/guidewire-cloud-platform-releases · accessed 2026-08-07
**Grade C.** Supports **RQ8** — strategically the most significant entry.
Context-aware, **auditable** AI-generated claim summaries embedded in ClaimCenter with full change history.
**Why it matters:** ClaimCenter is a dominant P&C claims system of record. Summarization delivered inside it requires no integration, no separate login, no data-sharing agreement, and no separate procurement. "Auditable, with change history" also indicates Guidewire has already identified traceability as the requirement. A standalone tool competes against a checkbox.
**Limitation:** capability description assembled from release-notes summaries; depth of the feature and whether it does cross-document reconciliation could not be established from public material. **This is the most important open question in the competitive picture** and would be worth resolving before any build.

**EvolutionIQ — claims guidance**
EvolutionIQ · https://www.evolutioniq.com/ · accessed 2026-08-07
**Grade C.** Supports **RQ8**.
Claims guidance across **Auto Casualty**, group and individual disability, workers' compensation, and income protection. Ingests medical records, claim files, and policy documents; outputs tactical guidance, medical insights, severity assessment, return-to-work recommendations, risk alerts, and triage prioritisation.
**Claimed outcomes:** 5–10 point combined-ratio reduction, 20%+ improvement in handling capacity — **vendor assertions, no methodology**.
**Why it matters:** occupies the adjacent, more valuable position — "what to do next" rather than "what happened." Evidence that summarization is becoming table stakes while the frontier moves to guidance.

**Roots Automation — document indexing accelerator**
Roots Automation, via PR Newswire · https://www.prnewswire.com/news-releases/roots-ai-powered-document-indexing-accelerator-validated-by-guidewire-transforming-claims-processing-with-automation-302654825.html · accessed 2026-08-07
**Grade C.** Supports **RQ8**.
Claim document classification and indexing, validated by Guidewire. Noted because the ingestion layer V1 would need is itself an established product category.

**Straight-through processing and touchless claims (trade and vendor reporting)**
Various, incl. Tractable/Mitchell partnership announcement · https://www.prnewswire.com/news-releases/tractable-to-make-ai-enabled-straight-through-processing-available-to-north-american-insurers-backed-by-mitchells-open-platform-and-comprehensive-repair-data-301528281.html · 2022–2026
**Grade C.** Supports **RQ3** — used as **evidence against** the hypothesis.
Source of the figures that industry-wide P&C STP sits below 10% with a majority of insurers reporting none, that leading personal-lines carriers approach ~35% on eligible claim types, and that one deployment (Admiral Seguros with Tractable) reports ~90% of auto estimates running touchless with 98% of assessments completed under 15 minutes.
**Why it matters:** supports the scope correction — auto physical damage is among the most automated categories, so synthesis value cannot be claimed across all personal auto claims.
**Limitation:** entirely vendor and trade sourcing with no consistent methodology. Recorded as **directional evidence for a qualitative conclusion only**; none of these percentages should be quoted as fact.

---

# Sources consulted but not usable

Recorded for transparency and to avoid re-treading, per decision D-001.

**McKinsey — "Claims 2030: Dream or reality" / "Five areas of focus for adopting the next generation of claims management"**
https://www.mckinsey.com/industries/financial-services/our-insights/claims-2030-dream-or-reality
**Repeated fetch timeouts (60s, two attempts).** Would likely be the best available source on claims operating-model change and adjuster role evolution. **Worth another attempt** — this is the most significant gap in the round.

**"Adjusters spend 50–70% of their time on administrative tasks (McKinsey/Accenture)" — VERIFICATION FAILED**
This is recorded as a finding, not a source. The figure is repeated widely across vendor content. Tracing it led to a Five Sigma blog post (https://fivesigmalabs.com/blog/exclusive-data-claims-adjusters-day-to-day-workloads/, July 2022), which I fetched. **It does not cite McKinsey, Accenture, or any external source.** Every figure on that page is presented as Five Sigma's own proprietary analysis of "thousands of claims" with **no methodology, no sample size, and no date beyond "the past three months."** The companion "60% of time on work about work" figure derives from a general knowledge-work productivity vendor survey, not from claims.
**The figure is barred from this project.** It appears in `claims-synthesis-research.md` §5.3 only inside its own debunking. Its collapse is the reason that document states plainly that no time-savings claim can be made until we measure one ourselves.

**Five Sigma — adjuster workload data**
https://fivesigmalabs.com/blog/exclusive-data-claims-adjusters-day-to-day-workloads/ · July 2022
**Grade C, used with an explicit warning.** Reports that 57% of first-party medical, 51% of bodily injury, and 38% of physical damage auto claims involve multiple adjusters, and that handling time is roughly 2.75–2.85× when they do. Directly on point for the handoff hypothesis and **nothing comparable exists publicly**, so it is recorded — but with no methodology, no sample size, and no precise date, it **must not be load-bearing**. Cited in the research document as evidence item 8 with this caveat attached.

**Verisk product and newsroom pages**
JavaScript-rendered; automated fetches returned title-only content. Product details were assembled from search-result summaries and third-party reporting. Capability descriptions are therefore less precise than for CLARA, whose syndicated press release was fully retrievable.

**ACORD Automobile Loss Notice specimen PDFs**
One returned HTTP 403; another is encrypted with 144 undecodable field identifiers. See the ACORD entry above — the field list is assembled from secondary descriptions and should be verified against a rendered form.

**arXiv 2410.13961 full PDF**
The 3.7MB PDF did not extract to readable text. Findings were taken from the arXiv abstract page, which carries the headline results. The paper's detailed taxonomy and per-model breakdowns have **not** been read and would be worth reading before Phase 6.

**Practitioner discussion (Reddit, adjuster forums)**
Multiple search strategies failed to surface usable practitioner discussion — results returned Louisiana insurance statutes, job listings, and SEO content. This is a genuine gap: the research contains **no practitioner voice at all**, which is one reason the verdict is "unvalidated" and why §12 is a talking-to-humans experiment rather than more desk research.

**General search environment**
Worth recording as a methodological note. Queries about adjuster time allocation, claims workflow, and claims AI in 2026 return an almost unbroken wall of vendor content marketing that cites itself circularly. Several searches returned nothing usable at all. The verification failure above is the clearest symptom, and it is why every quantified claim in this round has been traced to its origin rather than accepted from a search summary.
