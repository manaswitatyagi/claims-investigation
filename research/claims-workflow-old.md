# Claims Investigation Workflow — Day 1 Research

**Status:** Discovery research. No product design decisions made here.
**Date:** 2026-08-07
**Scope:** US personal auto insurance claims.

## How to read this document

Every substantive claim is tagged:

| Tag | Meaning |
| --- | --- |
| **[REGULATION]** | Written into statute or regulation. Verifiable, binding. |
| **[INDUSTRY]** | Documented industry practice from a reputable source. |
| **[EMPIRICAL]** | Supported by a study with a stated methodology. |
| **[INFERENCE]** | My reasoning from the above. Not sourced. Treat as a hypothesis to test. |
| **[UNCERTAIN]** | Weakly sourced, contested, or from a vendor with an interest in the answer. |

Vendor blogs (claims software companies, SIU service providers, plaintiff-side law firms) are used sparingly and always tagged. They have obvious incentives — vendors overstate the fraud problem and the efficacy of detection tools; plaintiff firms overstate insurer misconduct.

A note on sourcing limits: several of the most authoritative sources are paywalled (Insurance Research Council full reports, *Journal of Risk and Insurance* articles, the Coalition Against Insurance Fraud's SIU benchmarking survey). Where I rely on a press release or a secondary citation of these, I say so. I did not fabricate any source, and where I could not verify something I have left it as an open question in Section G rather than filling the gap.

---

# A. Claims workflow

## A.1 The stages, end to end

This is the personal auto claim lifecycle. Stages overlap heavily in practice; this is not a strict sequence. **[INDUSTRY]**

### 1. First Notice of Loss (FNOL)

The claim begins when the insured (or a third-party claimant, or an agent, or sometimes a repair shop or attorney) reports the loss. Intake channels: phone, mobile app, web portal, agent, telematics-triggered auto-FNOL.

What gets captured: date/time/location of loss, description of what happened, vehicles and parties involved, injuries alleged, police report existence and number, witnesses, damage description, whether the vehicle is drivable.

A claim number is assigned and a claim file is opened.

### 2. Coverage verification

Before anything else, the insurer determines whether coverage exists. This is largely a structured-data operation against the policy system:

- Was the policy in force on the date of loss?
- Is the vehicle a scheduled vehicle on the policy?
- Was the driver a permissive user / listed driver / excluded driver?
- What coverages apply (liability, collision, comprehensive, UM/UIM, PIP/MedPay), and what are the limits and deductibles?
- Are there policy conditions or exclusions in play?

**[INFERENCE]** This is where the classic "policy purchased days before the loss" and "coverage added days before the loss" checks naturally live, because the adjuster is already pulling these dates.

### 3. Assignment and segmentation

The claim is routed to an adjuster or a queue. Segmentation typically considers severity, complexity, injury presence, litigation risk, and coverage type. Simple, clear-liability, property-damage-only claims may be routed to a fast-track/straight-through process. Complex or injury claims go to a more senior adjuster or a specialty unit (injury/casualty, total loss, catastrophe). **[INDUSTRY]**

### 4. Investigation and fact-gathering

The substantive work. Depending on claim type:

- Contact the insured and any claimants; take statements (recorded or not)
- Obtain the police report / traffic collision report
- Inspect the vehicle(s) — staff appraiser, independent appraiser, drive-in center, or photo-based estimation
- Obtain repair estimates
- Interview witnesses
- Obtain medical records and bills for injury claims
- Run index/database checks (see Section B)
- Scene investigation, photographs, sometimes accident reconstruction for disputed or severe losses

### 5. Liability determination

Who is at fault, and to what degree. This depends on state law — comparative negligence, modified comparative negligence, contributory negligence, or a no-fault/PIP regime where first-party medical benefits are paid regardless of fault. **[INDUSTRY]**

**[INFERENCE]** The state's tort regime materially changes what the adjuster is even looking at. In a no-fault/PIP state, first-party medical benefits get paid regardless of fault, which shifts the abuse pattern toward inflated medical treatment rather than disputed fault. This matters for a product: signals that are meaningful in Massachusetts or Florida PIP may be irrelevant in a full-tort state, and vice versa. Any V1 needs to pick a jurisdictional context and say so.

### 6. Damages evaluation

Property damage: repair estimate vs. actual cash value; total-loss determination and valuation.
Injury: medical specials, treatment duration and modality, lost wages, general damages, permanency, prognosis.

### 7. Reserving

The adjuster sets a financial reserve — the insurer's estimate of ultimate claim cost. Reserves are revisited as facts develop. **[INDUSTRY]**

**[INFERENCE]** Reserving is an under-appreciated deadline. It forces an early judgment about severity on incomplete information, which is exactly the condition under which a synthesis tool would be useful — and exactly the condition under which a wrong signal is most damaging, because it anchors the adjuster early.

### 8. Resolution

Settlement negotiation, payment, or denial. Denials must be explained. Partial denials and reservations of rights are common.

### 9. Post-resolution

Subrogation (recovering from an at-fault third party's insurer), salvage disposal on total losses, arbitration between carriers, file closure. Claims can be reopened.

## A.2 The workflow runs on a regulatory clock

This is the constraint that shapes everything, and it is the single most important thing to understand before designing anything. **[REGULATION]**

The NAIC **Unfair Claims Settlement Practices Act (Model #900)** sets standards "for the investigation and disposition of claims." Section 4 enumerates unfair claims practices, including:

- "Failing to acknowledge with reasonable promptness pertinent communications with respect to claims"
- "Failing to adopt and implement reasonable standards for the prompt investigation and settlement of claims"
- "Refusing to pay claims without conducting a reasonable investigation"
- "Not attempting in good faith to effectuate prompt, fair and equitable settlement of claims submitted in which liability has become reasonably clear"
- "Failing in the case of claims denials or offers of compromise settlement to promptly provide a reasonable and accurate explanation of the basis for such actions"

Note the structure: an act is only an unfair claims practice under Section 3 if committed "flagrantly and in conscious disregard" of the Act, or "with such frequency to indicate a general business practice." Single errors are not automatically violations — patterns are. **[REGULATION]**

States implement this with hard deadlines. California's Fair Claims Settlement Practices Regulations (10 CCR § 2695.7) are a concrete example: **[REGULATION]**

| Requirement | Deadline |
| --- | --- |
| Accept or deny the claim, in whole or in part | Immediately, and no more than **40 calendar days** after proof of claim |
| Written status update if more time needed | Every **30 calendar days** |
| Tender payment after acceptance | Immediately, no more than **30 calendar days** |
| Notice before statute of limitations expires | **60 days** (30 for UM) |

Critically for this project: § 2695.7 allows the accept/deny window to be **extended to 80 calendar days, or suspended, where there is a reasonable basis to believe the claim is fraudulent** — but only if the insurer can demonstrate diligent investigation during that period. **[REGULATION]**

**[INFERENCE]** This is the real shape of the problem. A fraud signal does not just flag a claim; it can legitimately buy investigation time — but only if the insurer can document a *reasonable basis* and *diligent investigation*. That reframes the product. Its output is not "here is a suspicion score." Its output is potentially part of a documented, defensible basis for extending a claim. That is a much higher evidentiary bar than a demo dashboard implies, and it argues strongly for the evidence-linking principle already in the project's CLAUDE.md.

The corresponding downside risk: delaying a legitimate claim on a weak AI signal is not a neutral error. It is the exact conduct the UCSPA prohibits. **A false positive in this product is a regulatory exposure, not just a wasted investigator hour.**

---

# B. Adjuster's information environment

## B.1 What the adjuster actually does

Per O*NET's occupational profile for Claims Adjusters, Examiners, and Investigators (13-1031.00), documented tasks include examining claim forms, analyzing information gathered by investigation, reviewing police reports and medical records, interviewing claimants and witnesses, appraising property values, negotiating settlements, verifying accuracy of records, maintaining data in information systems, and conferring with legal counsel. **[INDUSTRY]**

O*NET lists the technology in use as a mix of general office software (Excel, Word, Outlook), claims platforms, estimating software (Xactimate), document management systems, and "fraud detection software" / predictive analytics platforms. **[INDUSTRY]**

**[INFERENCE]** The tooling list is revealing: the work is spread across a claims system, an estimating system, a document repository, external database portals, email, and spreadsheets. The adjuster is the integration layer. That is a genuine fragmentation problem and it is the strongest available support for the project's core hypothesis.

## B.2 Where information comes from

This is the answer to research question 4, organized by source.

### Policy administration system
- Policy inception, renewal, and expiration dates
- Coverages, limits, deductibles, endorsements
- Listed drivers, excluded drivers, scheduled vehicles (VIN, year/make/model)
- Premium payment history, lapses, reinstatements
- Recent policy changes (coverage added/increased, vehicle added)
- Named insured, address, garaging location

### Claims administration system
- Claim metadata: loss date, report date, claim type, cause of loss, status
- Prior claims by the same insured on the same policy
- Adjuster notes / activity log / diary entries
- Reserves and payment history
- Assignment history, escalations, prior SIU touches
- Correspondence log

### Claimant / insured (self-reported)
- FNOL narrative
- Recorded statement
- Proof of loss
- Repair receipts, rental receipts, wage-loss documentation
- Photographs
- Examination Under Oath (EUO) testimony, when invoked

An **EUO** is a formal sworn examination, transcribed by a stenographer, that the policy permits the insurer to compel as a condition of coverage. It is distinct from a recorded statement, which is unsworn. Insurers reserve EUOs for claims where questions cannot be resolved through ordinary adjusting, and can request supporting documents (financial records, phone records) as part of the process. Refusal to submit can be grounds for denial. **[INDUSTRY]**

**[INFERENCE]** The EUO is a meaningful escalation with legal consequence, not a routine step. If the product ever recommends an action, "refer to SIU" and "request an EUO" are very different in weight, and V1 should probably recommend neither.

### Third parties
- Police / traffic collision report
- Repair shop estimates and supplements
- Independent appraisers
- Medical providers: records, bills, treatment notes, diagnostic imaging reports
- Independent Medical Examination (IME) reports
- Medical audit / peer review reports
- Other carriers (in liability disputes and subrogation)
- Attorneys (claimant's counsel, defense counsel)
- Tow yards, salvage vendors, rental car companies
- Witnesses

### External databases and industry sources
- **ISO ClaimSearch** (Verisk) — described by the Insurance Information Institute as "the world's largest comprehensive database of claims information." Contains property, casualty, and auto claims data including physical damage, theft, and salvage; in operation since 1971. Accessible to insurers, self-insureds, TPAs, law enforcement, and state fraud bureaus. Insurers submit claims to it and receive matches on prior/concurrent claims involving the same parties, vehicles, or providers. **[INDUSTRY]**
- **NICB** (National Insurance Crime Bureau) — nonprofit funded by member insurers; maintains databases (including flood-VIN and VINCheck), receives questionable-claim referrals, and supports law enforcement investigations. **[INDUSTRY]**
- MVR (motor vehicle records), CLUE-type loss history reports, vehicle history/title/salvage records, court records, licensing/business registration, public social media.

### Automated / telematics
Telematics and connected-vehicle crash data, dashcam footage, photo-estimation output. **[UNCERTAIN]** — availability varies enormously by carrier and by whether the policyholder is enrolled. I would not assume it exists for a given claim.

## B.3 Typical claim documents and notes

| Document | Structure | Typical author |
| --- | --- | --- |
| FNOL report | Semi-structured: fields + free-text narrative | Intake rep or claimant |
| Recorded statement transcript | Unstructured, long, conversational, disfluent | Transcription of claimant/witness |
| Adjuster activity notes / diary | Unstructured, abbreviated, jargon-heavy, chronological | Adjuster |
| Police / traffic collision report | Structured form + narrative + diagram | Law enforcement |
| Repair estimate | Highly structured line items (often CCC/Mitchell/Audatex) | Appraiser or shop |
| Medical records and bills | Semi-structured: CPT/ICD codes + clinical narrative | Provider |
| IME report | Unstructured clinical narrative with conclusions | Examining physician |
| Medical audit / peer review | Unstructured with structured findings | Physician or nurse reviewer |
| Proof of loss | Structured form, sworn | Claimant |
| EUO transcript | Unstructured, long, sworn | Stenographer |
| Demand letter | Unstructured, argumentative | Claimant's attorney |
| Denial / reservation of rights letter | Semi-structured formal letter | Adjuster / coverage counsel |

**[INFERENCE]** Adjuster notes deserve special attention as a data type. They are the adjuster's own working memory — terse, abbreviated, full of internal shorthand, and written for an audience of one. They are simultaneously the richest source of "what does the handling adjuster actually think is going on" and the hardest text to parse reliably. They are also *discoverable in litigation*, which means anything the product writes into a claim file becomes a document an opposing attorney may one day read aloud. That is a serious design constraint.

## B.4 Evidence on time burden

I could not find good public data on how personal auto adjusters allocate their time. The closest evidence is from workers' compensation:

The 2019 Workers' Compensation Benchmarking Study (Rising Medical Solutions) reported that 58% of frontline claims professionals spend more than 20% of their time on internal or external compliance activities, with 14% spending over 40%. **[EMPIRICAL, but adjacent line of business]**

**[UNCERTAIN]** Caseload figures circulating for workers' comp (110–140 claims per adjuster) come from secondary sources I could not trace to a primary study, and workers' comp caseloads are not transferable to personal auto anyway.

**This is a real gap.** The project's central hypothesis is a claim about how adjusters spend time, and I could not verify it from public sources for personal auto. See Section G.

---

# C. Investigation / SIU workflow

## C.1 SIUs are legally mandated, not optional

This is the most important structural fact in this section, and it is frequently misunderstood. SIUs exist because regulators require them. **[REGULATION]**

**New York** — Insurance Law § 409 and Regulation 95 require insurers to file a fraud prevention plan with the Department of Financial Services. The plan must provide for an SIU **"apart from any underwriting or claims units."** Requirements include fraud detection procedure manuals for both claims/underwriting personnel and investigative personnel, in-service training, cooperation with law enforcement, and public awareness programs. DFS guidance states each SIU should be a separate unit with its own budget line, and that investigative personnel may not perform claims or underwriting functions or vice versa. There are no prescribed minimum staffing ratios; insurers must justify resource adequacy against their fraud exposure. Annual reports are due by March 15. Fraud prevention plans are confidential and not subject to subpoena except by court order. **[REGULATION]**

**California** — Insurance Code §§ 1875.20–24 and 10 CCR §§ 2698.30–2698.43 require licensed insurers to establish and maintain SIUs. The regulation is unusually specific and unusually relevant to this project:

- **§ 2698.30(l)** defines *integral anti-fraud personnel* — insurer personnel not assigned to the SIU but whose duties include processing, investigating, or litigating payment. In practice: the adjusters.
- **§ 2698.35(a)** makes integral anti-fraud personnel "responsible for identifying suspected insurance fraud during the handling of insurance transactions and referring it to the SIU as part of their regular duties."
- **§ 2698.35(b)** requires the SIU to "establish, maintain, distribute, and monitor written procedures" that include **"a listing of the red flags to be used to detect suspected insurance fraud for the insurer,"** and these red flags must be **"specific to each line of insurance, or each insurance product."**
- **§ 2698.35(c)** requires detection procedures to "provide for comparison of any insurance transaction against red flags and other criteria that may indicate possible fraud."
- **§ 2698.36** requires the SIU to "investigate each credible referral of suspected insurance fraud that it receives from integral anti-fraud personnel," **including automated referrals**. A credible referral is defined as one containing "a red flag or red flags." If preliminary review shows the red flags clearly do not indicate fraud, the SIU may decline to open an investigation — but **"shall document in the claim file or SIU investigation file the reasons supporting its conclusion."**
- **§ 2698.36** also requires "a concise and complete summary of the entire investigation" addressing what facts suggested fraud, the alleged misrepresentations and who made them, how they were material to the claim, pertinent witnesses, documentation, and whether the investigation is complete.
- **§ 2698.37** requires referral to the Fraud Division and district attorneys when **"the facts and circumstances create a reasonable belief that a person or entity may have committed or is committing insurance fraud."**
- **§ 2698.33** prohibits contracts for SIU functions from containing "provisions that could provide disincentives to the referral and/or investigation of suspected insurance fraud."

The federal architecture: the NAIC Insurance Fraud Prevention Model Act and the related SIU model regulation provide the template that most state departments of insurance have adapted. **[INDUSTRY]** — I verified the state implementations directly; I did not independently verify the NAIC model regulation number cited in secondary sources, so treat "Model #901" as unconfirmed.

### Why this matters enormously for the product

Four consequences, and they are not obvious:

1. **"Red flag" is a regulated term of art in California, not a marketing word.** The insurer must maintain a written, line-specific list of them. **[INFERENCE]** A product that invents its own signal taxonomy is creating something that must be reconciled with the insurer's filed list. Aligning the taxonomy to a customer's existing documented red flags is more valuable than inventing a better one.

2. **Automated referrals are explicitly contemplated and explicitly create obligations.** § 2698.36 says the SIU must investigate each credible referral "including automated referrals," and a referral containing a red flag *is* credible by definition. **[INFERENCE]** This means an AI system that emits referrals in California is generating work the SIU is legally obligated to process or document a declination for. A high false-positive rate is not merely annoying — it manufactures regulatory workload. This is the strongest argument I found for precision-over-recall in V1.

3. **Declining is also documented work.** Since the SIU must document why red flags did not indicate fraud, every wrong signal has a paper cost. **[INFERENCE]**

4. **The § 2698.36 summary requirements are effectively an output specification.** What facts suggested fraud; what misrepresentations; by whom; why material; which witnesses; what documentation. **[INFERENCE]** If the product organizes its evidence along these lines it produces something an SIU can actually use, rather than a summary the investigator has to re-derive. This is probably the single most actionable finding in this document.

## C.2 When claims get referred

The legal trigger in California is that "the facts and circumstances create a reasonable belief that a person or entity may have committed or is committing insurance fraud" (§ 2698.37). **[REGULATION]** Note the standard: *reasonable belief*, *may have*. It is deliberately below proof.

Operationally, referral is triggered by the adjuster noticing red flags during handling, by automated screening, by a database hit (e.g., ISO ClaimSearch match), or by a tip. **[INDUSTRY]**

The industry norm — widely repeated in practitioner literature — is that **no single indicator justifies referral; it is combinations that matter**. Zalma and other practitioner sources suggest three or more red flags as a rough threshold for considering further evaluation. **[UNCERTAIN]** — this "three or more" heuristic is repeated in practitioner writing and training material but I found no empirical validation of the threshold. Treat it as folklore with reasonable face validity, not as a validated rule.

## C.3 What the SIU does

Investigative techniques, roughly in ascending order of cost: **[INDUSTRY]**

- Database and index checks; social media review
- Re-interview / detailed recorded statement
- Independent Medical Examination (IME)
- Medical audit / peer review
- Field investigation, canvassing, scene inspection
- Accident reconstruction
- Examination Under Oath
- Surveillance
- Forensic accounting (for provider/organized fraud)

Derrig & Francis, working with Massachusetts AIB data, characterize accident reconstruction, EUOs, and surveillance as "the expensive examples," and note IMEs cost approximately $350 per exam with a $75 no-show charge (mid-1990s–early-2000s Massachusetts pricing). **[EMPIRICAL]**

Outcomes: claim paid as presented, claim compromised/reduced, claim denied, referral to the state fraud bureau or prosecutor, civil recovery.

## C.4 How often does any of this happen? Base rates

This section matters more than any other for evaluation design, because it establishes the prior.

**Referral rates.** In the Massachusetts AIB Detail Claim Database (162,761 third-party bodily injury liability claims, accident years 1995–1997, closed by June 30 2003): **SIU investigation was performed on 7% of claims; an IME was performed on 8%.** **[EMPIRICAL]**

Nationally the rate is lower. Derrig & Francis, citing IRC data, note that nationally **about 4% of BI claims involved IMEs and about 2% involved SIU — one-half to one-quarter of the Massachusetts rate.** They attribute the difference to Massachusetts being a no-fault, high-frequency, urban state. **[EMPIRICAL]**

**[UNCERTAIN]** Vendor sources cite personal auto SIU referral rates of ~1.8% of claims, which is consistent with the IRC figure, but I could not trace that number to a primary source. The Coalition Against Insurance Fraud's biennial SIU benchmarking survey is the likely origin and is not publicly available.

**Hit rates.** In the Massachusetts data, **SIU produced a "favorable" outcome (claim denied or compromised based on the investigation) on 3.4% of all claims** — against 7% referred. Derrig & Francis state that "favorable outcomes average about 50% when an IME is done or a claim is referred to SIU." **[EMPIRICAL]**

So: **roughly half of SIU referrals in this dataset produced no favorable outcome.** And Massachusetts was the aggressive end of the spectrum.

**Automated referrals do notably worse.** Reporting on the Coalition Against Insurance Fraud's SIU benchmarking survey, Insurance Journal noted in 2020 that **"the percentage of referrals from automated systems accepted by special investigation units has declined to 15 percent from 22 percent."** Suggested explanations included a shift toward major fraud rings and better investigator filtering. **[EMPIRICAL — via secondary reporting of a non-public survey]**

**[INFERENCE]** That figure — 15% of automated referrals accepted — is the number this project should be measured against. It is the incumbent baseline for machine-generated signals in this exact workflow, and it is bad. An AI copilot does not have to beat human adjusters. It has to beat automated screening systems that SIUs already largely ignore. That is a lower bar, but it also explains why SIU investigators are likely to be *skeptical by default* of a new automated flag. Adoption is a trust problem before it is an accuracy problem.

**Prevalence of fraud and buildup.** The Insurance Research Council's study of 2012 auto injury claims (more than 35,000 claims closed with payment, from twelve insurers representing 52% of the US private passenger auto market) found: **[EMPIRICAL]**

- **21% of bodily injury claims and 18% of PIP claims** closed with payment "had the appearance of fraud and/or buildup"
- Fraud and buildup added an estimated **$5.6bn–$7.7bn** in excess payments in 2012, representing **13%–17%** of total payments under the five main auto injury coverages
- **Buildup** — inflation of an otherwise legitimate claim — was the most common form, accounting for ~15% of dollars paid on BI and PIP claims
- Claims with the appearance of fraud/buildup more often involved chiropractic treatment, physical therapy, alternative medicine, and pain clinics

A separate IRC study cited by Derrig & Francis found Massachusetts had the highest share of BI claims among no-fault states suspected of fraud (23%) and/or buildup (41%). **[EMPIRICAL]**

**Critical methodological caveat: "appearance of fraud" is an adjuster's subjective assessment, not an adjudicated finding.** The IRC methodology asks claims professionals to assess claims. It measures suspicion, not proven fraud. **[INFERENCE]** This distinction runs through the entire literature and is the single most important thing to internalize: essentially every published "fraud rate" is a suspicion rate. There is no large public dataset of *adjudicated* auto insurance fraud.

**The headline number everyone cites.** The Coalition Against Insurance Fraud's 2022 study (prepared by the Colorado State University Global White Collar Crime Task Force) estimated US insurance fraud at **$308.6 billion annually**, the first update since a 1995 study that estimated $80 billion. **[EMPIRICAL — with reservations]**

**[UNCERTAIN]** I would be cautious with this figure. The Coalition Against Insurance Fraud is an advocacy organization funded substantially by insurers, with an institutional interest in a large number. A 3.9× increase over 27 years, with a methodology change, is the kind of estimate that gets repeated far more often than it gets scrutinized. It is fine for motivating a slide; it is not evidence about any individual claim, and it should not appear in a product's justification.

---

# D. Potential fraud signals

## D.1 The taxonomy first

Two distinctions do most of the work:

**Hard vs. soft fraud.** Viaene and Dedene classify insurance fraud along three axes: internal vs. external, underwriting vs. claim, and soft vs. hard. **Soft fraud** (opportunistic) is where a claimant seizes the opportunity to exaggerate an otherwise legitimate claim. **Hard fraud** is a planned, executed scam. **[EMPIRICAL/INDUSTRY]**

**Fraud vs. buildup.** IRC treats these separately, and this matters enormously. *Buildup* is the inflation of a legitimate claim. *Fraud* is a fabricated or staged claim. **[EMPIRICAL]**

**[INFERENCE]** These require completely different detection approaches and imply different product responses. Buildup is a *magnitude* problem — the accident happened, the injury is real, the treatment is excessive — and it is detected by comparing this claim against a distribution of similar claims. Fraud is a *coherence* problem — the story doesn't hold together — and it is detected by comparing documents against each other and against physical evidence. **An LLM over unstructured documents is far better suited to the coherence problem than the magnitude problem.** The magnitude problem is a statistics problem and should not be given to an LLM. This is probably the sharpest scoping insight available at this stage.

Also worth stating plainly: **buildup is much more common than fraud** (IRC: buildup accounts for ~15% of BI/PIP dollars paid, and is described as the most common form of abuse). If the product only detects coherence problems, it is aimed at the smaller share of the loss. That is a defensible V1 choice but it should be a *choice*, not an accident.

## D.2 Commonly cited indicators

Organized by category. **These are commonly cited, which is not the same as validated.** See D.3.

### Policy and timing
- Loss occurring shortly after policy inception
- Loss occurring shortly before policy expiration or after lapse/reinstatement
- Coverage added or increased shortly before the loss
- Delay between loss date and report date without explanation
- Loss occurring during a grace period or shortly after a reinstatement

### Claim history
- Multiple prior claims, especially similar in type
- Prior claims across multiple carriers (ISO ClaimSearch match)
- Prior involvement of the same parties, vehicles, providers, or attorneys across claims

### Circumstances of loss
- No police report, or report filed late, or filed by a party other than the driver
- No independent witnesses, or witnesses who are all related/known to each other
- Accident occurring at an unusual time or in an unusual location relative to the parties' stated activity
- Single-vehicle loss with no independent corroboration
- Vehicle damage inconsistent with the described mechanism of impact
- Pre-existing or mechanical damage claimed as accident-related
- Vehicle previously salvaged, or at the end of its lease term, in theft claims

### Injury and treatment
- Severe injuries claimed from a minor-impact collision
- Immediate attorney representation, particularly before treatment
- Treatment beginning after a long unexplained gap
- Extended treatment with soft-tissue-only diagnoses
- Treatment at clinics with a high volume of claimants from the same accidents
- Billing on Sundays and holidays
- All occupants of a vehicle claiming identical injuries

### Behavioral
- Claimant unusually knowledgeable about insurance terminology and claims process
- Pressure for a fast settlement, or willingness to accept an unusually low amount to close quickly
- Claimant only reachable by mobile, refuses in-person contact, provides inconsistent contact information
- Out-of-state, expired, or temporary driver's license
- Hostility or evasiveness about routine verification steps

### Documentary
- Inconsistencies between FNOL and later statements
- Inconsistencies between claimant statement and police report
- Altered, duplicated, or templated documents
- Receipts without verifiable vendors

Sources for these lists are practitioner-oriented: PropertyCasualty360, Zalma's writing, SIU service providers, law firm summaries. **[INDUSTRY / UNCERTAIN]**

## D.3 The hard question: are these actually predictive?

**The user's instruction not to assume indicators are predictive is well-founded, and the evidence supports the skepticism.**

### Evidence 1: Models built on these indicators perform modestly

Derrig & Francis (Casualty Actuarial Society, *Variance*) modeled Massachusetts AIB data (162,761 BIL claims, 21 explanatory variables covering insured, claimant, accident, injury, medical treatment, outpatient providers, and attorney presence) against four targets. Area under the ROC curve on held-out test data: **[EMPIRICAL]**

| Target | Range across 8 model/software combinations | Best |
| --- | --- | --- |
| IME decision | 0.629 – 0.701 | TreeNet 0.701 |
| IME favorable outcome | 0.591 – 0.697 | Random Forest 0.697 |
| **SIU decision** | **0.539 – 0.667** | Random Forest 0.667 |
| **SIU favorable outcome** | **0.547 – 0.678** | TreeNet 0.678 |

An AUROC of 0.50 is no predictive ability. **The best SIU models reach roughly 0.67–0.68 on a very large dataset with substantial feature engineering.** That is weak-to-moderate. The authors note SIU scores are "significantly lower than for IME across all eight model/software combinations," speculating the variables were more informative about buildup than about fraud.

### Evidence 2: Sophisticated methods don't beat simple ones

Viaene et al. (2002) applied neural networks, support vector machines, and logistic regression to a dataset of insurance claim fraud indicators as predictors of expert opinion on suspicion of fraud. As summarized by Derrig & Francis: **"They found that simple logistic regression did as well as the more sophisticated procedures at predicting expert opinion on the presence of fraud."** **[EMPIRICAL — secondary citation; I did not access the Viaene paper directly]**

**[INFERENCE]** When model class stops mattering, you are usually at the information ceiling of your features. The red flags themselves are the limiting factor, not the algorithm. This is a strong prior against the assumption that a more sophisticated model — including an LLM — extracts substantially more signal *from the same structured indicators*. The bet worth making is on *new information* from unstructured text, not on better modeling of the old information.

### Evidence 3: The target variable is itself suspect

The Massachusetts models predict *the decision to investigate* and *a favorable outcome*, not adjudicated fraud. Viaene et al. predicted *expert opinion on suspicion*. IRC measures *appearance of fraud* as assessed by claims professionals. **[EMPIRICAL]**

**[INFERENCE]** Every one of these targets is contaminated by the very human judgment the system is supposed to assist. A model trained to predict which claims adjusters referred to SIU learns to imitate adjusters — including their biases and blind spots. If adjusters over-refer claims from certain zip codes, the model learns that. Derrig & Francis's own variable set includes rating territory, zip-code-level claim/attorney/provider activity ranks, and claimant-to-provider distance. Those are geographic proxies, and geographic proxies in insurance are exactly what regulators scrutinize for proxy discrimination.

Derrig & Francis note explicitly that many insurance databases "do not contain data or variables indicating whether a particular claim is suspected of fraud or abuse," which is why unsupervised methods get used. **[EMPIRICAL]** There is no clean ground truth.

### Evidence 4: A timing trap in the data

Derrig & Francis flag a caveat that is easy to miss and expensive to get wrong: **[EMPIRICAL]**

> "One important caveat of this analysis is that it is based on closed claims, so some of the variables, such as the amount billed by outpatient medical providers, may not be fully known until the claim is nearly closed. When building a model to detect fraud and abuse prospectively, the modeler will be restricted to information available relatively early in the life of a claim."

**[INFERENCE]** This is a target-leakage warning aimed directly at this project. Many powerful-looking indicators — total billed, treatment duration, number of providers, attorney involvement — are only fully observable once the claim is nearly resolved. A system evaluated on closed claims will look far better than one deployed at FNOL. **Any evaluation set built for this project must be timestamped: each signal must declare what information was available at what point in the claim lifecycle, and evaluation must be run at a defined decision point, not against the full closed file.** If this is not designed in from the start it will silently inflate every metric.

### Evidence 5: Base rates make precision hard

With ~2% of BI claims nationally going to SIU, ~50% of Massachusetts SIU referrals producing a favorable outcome, and ~15% of automated referrals being accepted by SIUs, the operating region is low-prevalence. **[EMPIRICAL]** At low base rates, even a well-calibrated classifier produces mostly false positives at any useful recall. **[INFERENCE]**

### What I would conclude

**[INFERENCE]** The commonly cited indicator lists are best understood as *investigative prompts* — things worth looking at — rather than *predictors*. They encode real practitioner experience and they are regulatorily embedded (California requires a written red flag list). But the empirical record does not support treating any individual indicator as strong evidence, and it does not support the assumption that combining them mechanically produces a reliable score.

Two indicators I would specifically flag as commonly cited but weak on their own:

- **"Claimant is knowledgeable about the claims process."** Also true of anyone who has had a prior claim, works in insurance, or read a consumer guide. Near-zero specificity.
- **"Immediate attorney representation."** Strongly confounded — attorney representation correlates with injury severity, socioeconomic status, jurisdiction, and aggressive local advertising. Derrig & Francis include attorney presence as a variable, but presence in a model is not evidence of independent predictive value.

**[INFERENCE]** More broadly, several indicators on the standard lists are proxies for poverty or immigration status — out-of-state/temporary licenses, no landline, mobile-only contact, unfamiliarity with process. A product that surfaces these as "signals" will systematically flag poorer claimants. This is a fairness problem *and* a regulatory problem under the NAIC AI Model Bulletin (Section F.4). It deserves an explicit position before any taxonomy is built.

---

# E. Structured vs. unstructured signals

Answering research questions 8 and 9.

## E.1 Deterministic from structured data — no LLM needed

These are computations. Using an LLM for them would be slower, more expensive, non-reproducible, and less accurate. **[INFERENCE — but a well-supported one; this is consistent with the project's stated principles]**

| Signal | Computation | Inputs |
| --- | --- | --- |
| Policy freshness at loss | `loss_date − policy_inception_date` | Policy system |
| Coverage recency | `loss_date − last_coverage_change_date` | Policy system |
| Reporting delay | `report_date − loss_date` | Claims system |
| Loss near policy expiration | `policy_expiration − loss_date` | Policy system |
| Loss during lapse/reinstatement window | Date range comparison | Policy system |
| Prior claim count | Count over lookback window | Claims system, ISO ClaimSearch |
| Prior claim frequency | Count / exposure period | Claims system |
| Total prior claim amount | Sum | Claims system |
| Similar prior claim type | Categorical match | Claims system |
| Treatment lag | `first_treatment_date − loss_date` | Medical bills |
| Claim amount vs. peer distribution | Percentile against comparable claims | Claims data warehouse |
| Vehicle value vs. claimed damage ratio | Arithmetic | Estimate + valuation |
| Driver not listed on policy | Set membership | Policy system |
| Vehicle not scheduled | Set membership | Policy system |
| Salvage/branded title history | Database lookup | VIN services, NICB |
| Party/provider/attorney recurrence across claims | Graph/join query | ISO ClaimSearch, internal |
| Claimant-to-provider distance | Geospatial calculation | Addresses |
| Provider billing volume anomaly | Aggregation + outlier detection | Claims data warehouse |

**[INFERENCE]** A meaningful share of the "structured" list requires data most demo builds won't have — ISO ClaimSearch access, an internal claims warehouse, provider-level aggregates. A realistic V1 scope question is which of these are computable from a single claim record versus which require cross-claim data. **The cross-claim ones are likely the most predictive and the hardest to obtain.** That tension should be named early rather than discovered late.

## E.2 Requires understanding unstructured text

Where an LLM plausibly adds value:

| Task | Why it needs language understanding |
| --- | --- |
| Extracting structured facts from FNOL narrative | Free text; facts stated in prose, not fields |
| Extracting facts from recorded statement transcripts | Long, disfluent, conversational, non-linear |
| Extracting facts from police report narratives | Prose + varied agency formats |
| Extracting diagnoses/treatment from medical narrative | Clinical prose alongside coded data |
| Summarizing adjuster notes into a claim timeline | Terse, abbreviated, jargon-heavy, chronological but interleaved |
| Detecting internal contradiction within one document | Requires tracking entities and assertions across a long text |
| Detecting contradiction across documents | Requires normalizing facts to a comparable representation first |
| Reconciling narrative against structured record | Cross-modal comparison |
| Identifying unexplained gaps in a narrative | Requires a model of what a complete account looks like |
| Assessing whether described mechanism matches described damage | Physical/causal reasoning over text |
| Assembling supporting evidence with citations | Retrieval + attribution |

## E.3 The genuinely hard cases

**[INFERENCE]** These are the ones that answer the project's central question — what is hard for a human *because* the information is fragmented:

1. **Cross-document contradiction.** The FNOL says the claimant was driving alone; the recorded statement three weeks later mentions a passenger; the medical records list a second person treated from the same accident. No single document is wrong. A human finds this by holding three documents in working memory simultaneously. **This is the strongest candidate for genuine AI value.**

2. **Temporal reconstruction across sources.** Building a single timeline from a loss date in the claims system, a narrative in the FNOL, treatment dates in the medical bills, and dated adjuster notes. Tedious, mechanical, and error-prone for a human. Well-suited to extraction + deterministic assembly.

3. **Entity resolution across documents.** The same person appearing as "Robert Smith," "Bob Smith," and "R. Smith, claimant's brother-in-law" across FNOL, police report, and repair invoice. **[INFERENCE]** But note: entity resolution is a classic hard problem and LLMs are confidently wrong at it. This is a place to be careful, not enthusiastic.

4. **Narrative-vs-physical-evidence mismatch.** The statement describes a rear-end impact at low speed; the estimate shows left-side damage. Requires reading both and reasoning about them. Plausible but **[UNCERTAIN]** — I would want to test whether an LLM does this reliably rather than assume it.

## E.4 A caution about what "detecting inconsistency" means

**[INFERENCE]** This is worth stating before any design work, because it is the most likely failure mode:

People telling the truth about a stressful event are routinely inconsistent. Memory for traumatic events is unreliable; details shift between tellings; people round times, misremember directions, and revise. A recorded statement taken three weeks after a collision *will* differ from an FNOL taken twenty minutes after it. That is normal, not suspicious.

A system that flags every difference between two accounts of the same event will produce enormous false-positive volume and will train adjusters to ignore it. The hard part is not detecting differences — that is easy. The hard part is distinguishing *material* inconsistency (facts that matter to coverage, liability, or damages, and that a truthful account should not get wrong) from *ordinary* variation.

Note that California's § 2698.36 already encodes this distinction: the investigation summary must address **how the misrepresentation was material to the claim.** Materiality is the regulator's own filter. **[REGULATION]** A product that surfaces immaterial inconsistencies is generating work, not saving it.

**[INFERENCE]** I do not know whether current LLMs can judge materiality reliably in this domain. That is an empirical question and should be one of the first things tested — before building anything.

---

# F. Potential AI opportunities

Where a copilot could realistically save time, ordered by my assessment of value-to-risk ratio. **All [INFERENCE]** unless noted — this section is analysis, not sourced fact.

## F.1 Strongest candidates

### 1. Claim file synthesis and timeline construction
**Problem:** An adjuster picking up a claim — new assignment, reassignment, post-vacation, escalation, supervisor review — must reconstruct the state of the file from scattered sources.
**Why AI:** Genuine synthesis across unstructured sources. Directly targets the fragmentation hypothesis.
**Why it's safest:** It surfaces what is already in the file. It makes no judgment about the claimant. A wrong summary is a correctable annoyance, not a regulatory event.
**Time saved:** Plausibly substantial, and it happens on *every* claim rather than the ~2% that are suspicious.

**This is the strongest opportunity in the list, and it is notable that it is not a fraud feature.** Given the base rates in Section C.4, a tool that helps on 100% of claims by 10 minutes each is worth more than one that helps on 2% of claims by an hour each. Worth confronting directly: the fraud framing may be the *less* valuable half of this product.

### 2. Structured fact extraction from documents
**Problem:** Facts exist in prose and must be manually transcribed into the claims system.
**Why AI:** Classic extraction task, well-matched to LLM capability.
**Why it's safe:** Output is verifiable against the source. Attribution is natural — every extracted fact points at a span in a document.
**Enables everything else:** Deterministic rules cannot run on unstructured text. Extraction is what converts documents into things rules can check. **This is the architectural keystone.**

### 3. Evidence assembly and citation
**Problem:** Once something is suspected, assembling the supporting evidence is manual document archaeology.
**Why AI:** Retrieval and attribution.
**Regulatory fit:** Maps directly onto California § 2698.36's required investigation summary — facts suggesting fraud, misrepresentations, who made them, materiality, witnesses, documentation. **[REGULATION]**
**This may be the highest-value fraud-specific feature**, because it helps at the point where the human has already made the judgment. The AI is not deciding; it is doing the clerical work of a decision already made. That sidesteps most of the risk in Section F.4.

## F.2 Plausible but must be proven

### 4. Cross-document inconsistency detection
The headline capability and the hardest to do well. Value depends entirely on the materiality filter (Section E.4). **Prove the materiality judgment works before building anything around this.**

### 5. Deterministic rules over LLM-extracted facts
Hybrid: LLM extracts, code computes. Combines LLM strength (reading) with code strength (arithmetic, reproducibility). Consistent with the project's stated principles and probably the correct core architecture.

## F.3 Weak or premature

### 6. Overall claim risk scoring
Section D.3 says the achievable ceiling is modest (AUROC ~0.67 for SIU outcomes on large data with real features). A single score also collapses evidence into a number, defeating the explainability goal. **[EMPIRICAL basis, inference conclusion]**

### 7. Automated SIU referral
In California this generates a legal obligation (§ 2698.36). Automated referrals already have ~15% SIU acceptance. Building toward this in V1 would be a mistake. **[REGULATION + EMPIRICAL]**

### 8. Anything touching the coverage decision
Straightforwardly the bad-faith exposure zone. Out of scope.

## F.4 The regulatory constraint on any of this

**[REGULATION]** The NAIC adopted the **Model Bulletin on the Use of Artificial Intelligence Systems by Insurers** on December 4, 2023. As of March 2025, ~24 states had adopted it with little or no material change; by mid-2026 more than 20 US jurisdictions had adopted it. It requires a written AI Systems Program with senior-management and board accountability, risk controls, model validation and testing for errors, bias, and unfair discrimination, and oversight of third-party AI — with the insurer remaining responsible for vendor systems.

**[INFERENCE]** "The insurer remains responsible for third-party AI" means a vendor selling into this space must supply the evidence the insurer needs to discharge its own obligation: documented validation, bias testing, explainability. This is not a nice-to-have; it is a procurement gate. The evaluation work in this project's roadmap is not academic diligence — it is the deliverable a buyer will demand.

**[INDUSTRY/UNCERTAIN]** Litigation context: health insurers have been sued over algorithmic claim denials, most prominently Cigna over its PXDX system, with allegations of minimal or no human review. At least one court has allowed discovery into an insurer's use of AI to deny claims. These are health, not auto, and allegations are not findings. But the direction of regulatory and judicial attention is unambiguous, and several states are considering legislation on AI in claims handling. The reputational risk of "AI flags claims as fraudulent" is real regardless of how carefully the product is worded — and note that a *decision-support* tool that adjusters defer to in practice may be treated as a decision tool by a court. Human-in-the-loop is a design claim that has to survive contact with how the tool is actually used.

---

# G. Open questions before building

## G.1 Questions that block product decisions

**1. Which jurisdiction and tort regime is V1 targeting?**
No-fault/PIP vs. full tort changes which signals are meaningful and which regulations bind. California's SIU regulations are the most prescriptive and would be a defensible design target. This needs an answer before the signal taxonomy.

**2. At what point in the claim lifecycle does the analysis run?**
Section D.3, Evidence 4: closed-claim analysis dramatically overstates prospective performance. FNOL, post-statement, and pre-settlement are three different products with three different information sets. **Answer this before building the evaluation set**, because the evaluation set must be timestamped to match.

**3. Is the product aimed at fraud (coherence) or buildup (magnitude)?**
Section D.1: different detection approaches, different data. Buildup is the larger share of loss dollars but needs peer-comparison data. Fraud/coherence is better suited to LLMs over documents. Trying to do both in V1 is probably a mistake.

**4. Is the primary user really the adjuster, or the SIU investigator?**
CLAUDE.md says adjuster, and the CA regulation supports that (adjusters are "integral anti-fraud personnel" with a detection duty). But the § 2698.36 evidence-summary requirement points at the SIU. **These are different products.** The adjuster wants triage; the investigator wants dossier assembly.

**5. Should V1 be a fraud product at all?**
Section F.1: the strongest opportunity — claim synthesis and timeline construction — helps on every claim, while fraud signals are relevant on ~2%. This may be an argument for "Claims Investigation Copilot" being primarily a comprehension tool with fraud signals as one output. Worth deciding deliberately.

## G.2 Empirical questions I could not answer

**6. How do personal auto adjusters actually spend their time?**
I found workers' comp data (58% spend >20% of time on compliance activity) but nothing solid for personal auto. **The project's core hypothesis is currently unvalidated for its target user.** Best resolution: talk to adjusters. Failing that, industry surveys or job postings as weak proxies.

**7. What is the real precision of existing automated fraud screening?**
The 15%-acceptance figure comes from secondary reporting of a non-public survey. It is the incumbent baseline and deserves better sourcing.

**8. Which specific indicators have documented predictive value?**
The Massachusetts AIB work is the best public evidence and it is 1990s data from one state. Variable-importance rankings exist in Derrig & Francis (2006) — worth obtaining.

**9. Can an LLM reliably distinguish material from immaterial inconsistency in claim narratives?**
Section E.4. **This is the highest-value experiment available right now, and it can be run before building anything.** If the answer is no, the inconsistency-detection feature is not viable and the project should pivot toward synthesis.

**10. What is the actual base rate of detectable inconsistency in legitimate claims?**
Needed to set thresholds and to build a realistic synthetic set. If 30% of honest claims contain a narrative discrepancy, an inconsistency detector is useless without materiality filtering.

## G.3 Design questions

**11. How does the product avoid anchoring the adjuster?**
Presenting a signal early may bias the investigation — and the resulting bias is invisible in a demo. Consider whether "no signals found" is presented as a positive assertion (dangerous: absence of evidence) or as silence.

**12. What is the taxonomy's relationship to the insurer's filed red flag list?**
California requires a written, line-specific red flag list (§ 2698.35(b)). An unrelated taxonomy creates reconciliation burden.

**13. How is disagreement captured?**
If the adjuster dismisses a signal, that is the most valuable evaluation data available. Design for it from the start or lose it.

**14. What does the product write into the claim file?**
Claim files are discoverable. Anything the product persists may be read aloud in a deposition. This constrains tone and phrasing far more than the "don't say fraud" guideline suggests.

**15. Which indicators are proxies for protected or socioeconomic characteristics, and what is the policy on them?**
Section D.3. Geographic ranks, provider distance, license type, contact method. Needs an explicit position, not a default.

## G.4 Data questions

**16. Is there any public labeled auto claims fraud dataset with unstructured documents?**
**[UNCERTAIN — likely no.]** The Massachusetts AIB data is not public. IRC data is proprietary. Kaggle "insurance fraud" datasets are structured-only and mostly synthetic with unclear provenance. **If there is no public dataset with documents, synthetic data is not a shortcut — it is the only option**, and the evaluation set's realism becomes the project's biggest validity risk. This needs a dedicated investigation (roadmap item 3) and the answer should not be assumed.

**17. What ground truth is even available?**
Section D.3, Evidence 3: published work predicts *suspicion*, *referral*, or *favorable outcome* — never adjudicated fraud. The project must decide what "correct" means in its evaluation set, and be honest that a synthetic set with authored ground truth measures whether the system finds what we planted, not whether it would find real fraud.

---

## Summary of the most important findings

1. **Claims handling runs on a regulatory clock, and a fraud signal legitimately extends it** (CA: 40 → 80 days) — but only with a documented reasonable basis. False positives are regulatory exposure, not just wasted effort.
2. **California codifies "red flags," requires SIUs to act on automated referrals, and requires documented declinations.** Wrong signals manufacture legal workload.
3. **§ 2698.36's investigation-summary requirements are effectively a free output specification** for what evidence assembly should produce.
4. **The empirical ceiling on structured-indicator fraud models is modest** (AUROC ~0.67 for SIU outcomes on 162,761 claims). Sophisticated models did not beat logistic regression. Better modeling of the same indicators is not the opportunity; new information from unstructured text might be.
5. **Every published "fraud rate" is a suspicion rate.** There is no clean public ground truth.
6. **Automated referrals are already largely distrusted** (~15% SIU acceptance). Adoption is a trust problem before an accuracy problem.
7. **Closed-claim evaluation will overstate prospective performance.** Timestamp the evaluation set.
8. **Buildup ≠ fraud**, needs different methods, and is the larger share of loss dollars.
9. **Detecting inconsistency is easy; judging materiality is the hard part** — and materiality is the regulator's own standard.
10. **The strongest opportunity may not be a fraud feature at all** — claim synthesis helps on 100% of claims; fraud signals matter on ~2%.
