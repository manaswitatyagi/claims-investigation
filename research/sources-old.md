# Sources

Sources used for `research/claims-workflow.md`. Retrieved 2026-08-07.

Each entry states why the source is useful and, where relevant, what its limitations are. Sources are graded:

- **A — Primary/authoritative.** Statute, regulation, or a study with a stated methodology from a body without a direct commercial interest in the answer.
- **B — Reputable secondary.** Industry body, trade press, or occupational data; reliable but derivative.
- **C — Interested party.** Vendor, advocacy organization, or law firm. Useful for practitioner vocabulary and framing; treat all numbers with suspicion.

---

## Regulation and law

**NAIC Unfair Claims Settlement Practices Act (Model #900)** — Grade A
https://content.naic.org/sites/default/files/model-law-900.pdf
The model statute that most states' claims handling rules derive from; Section 4's enumerated unfair practices define the legal boundary any claims-adjacent product operates inside. Note Section 3's qualifier that violations require flagrancy or a general business practice — single errors are not automatically violations. Full text extracted directly from the PDF.

**California Code of Regulations, Title 10, § 2695.7 (Fair Claims Settlement Practices Regulations)** — Grade A
https://www.law.cornell.edu/regulations/california/10-CCR-2695.7
Gives the concrete claims-handling deadlines (40-day accept/deny, 30-day status updates, 30-day payment) and — the key finding — the extension to 80 days where there is a reasonable basis to believe a claim is fraudulent, conditional on demonstrated diligent investigation. This is what makes a fraud signal operationally consequential rather than advisory.

**California Code of Regulations, Title 10, § 2698.35 (Detecting Suspected Insurance Fraud)** — Grade A
https://www.law.cornell.edu/regulations/california/10-CCR-2698.35
Establishes that "red flags" are a regulated artifact: insurers must maintain a written, line-of-business-specific red flag list and compare every insurance transaction against it. Directly constrains how a product's signal taxonomy should relate to a customer's existing filed list.

**California Code of Regulations, Title 10, § 2698.36 (Investigating Suspected Insurance Fraud)** — Grade A
https://www.law.cornell.edu/regulations/california/10-CCR-2698.36
The single most product-relevant regulation found: SIUs must investigate every credible referral *including automated referrals*, a referral containing a red flag is credible by definition, declinations must be documented with reasons, and the required investigation summary (facts, misrepresentations, who made them, materiality, witnesses, documentation) reads as an output specification for evidence assembly.

**California Code of Regulations, Title 10, § 2698.37 (Referral of Suspected Insurance Fraud)** — Grade A
https://www.law.cornell.edu/regulations/california/10-CCR-2698.37
Gives the legal threshold for referral — "facts and circumstances create a reasonable belief that a person or entity may have committed or is committing insurance fraud" — which is deliberately set below proof and is the correct standard for a product to align its language to.

**California Code of Regulations, Title 10, Chapter 5, Subchapter 9, Article 2 (SIU regulations, index)** — Grade A
https://www.law.cornell.edu/regulations/california/title-10/chapter-5/subchapter-9/article-2
Full section listing for the California SIU regime (§§ 2698.30–2698.45), used to map the regulatory structure — definitions, staffing, contracting, detection, investigation, referral, training, annual reporting, penalties.

**California Code of Regulations § 2698.33 (SIU and Integral Anti-Fraud Personnel Contracted Responsibilities)** — Grade A
https://www.law.cornell.edu/regulations/california/10-CCR-2698.33
Relevant to any vendor: contracts for SIU functions may not contain provisions creating disincentives to referral or investigation, and cannot relieve the insurer of its obligations. Constrains how a third-party AI tool can be contracted for.

**New York DFS — FAQ: Fraud Prevention Plans and Special Investigations Units** — Grade A
https://www.dfs.ny.gov/apps_and_licensing/insurance_companies/faqs_fraud_siu
Regulator's own guidance on NY Insurance Law § 409 and Regulation 95: the SIU must be organizationally separate from claims and underwriting, with its own budget line and personnel who do not perform claims functions. Establishes that SIUs are a legal mandate, not a business choice, and shows a second state's approach for contrast with California.

**California Department of Insurance — SIU Compliance Office** — Grade A
https://www.insurance.ca.gov/0300-fraud/0100-fraud-division-overview/12-siu/
Regulator's overview of the SIU requirement and its statutory basis (Cal. Ins. Code §§ 1875.20–24). Used to confirm the statutory citations behind the regulations above.

**NAIC — Model Bulletin on the Use of Artificial Intelligence Systems by Insurers (adoption tracker)** — Grade A
https://content.naic.org/sites/default/files/cmte-h-big-data-artificial-intelligence-wg-map-ai-model-bulletin.pdf
Official record of which states have adopted the AI model bulletin. Establishes that AI governance requirements — written AI Systems Program, bias and error testing, board accountability, and insurer responsibility for third-party AI — are live obligations in a majority of relevant jurisdictions, making evaluation evidence a procurement gate rather than an academic exercise.

**NAIC — announcement of Model Bulletin adoption** — Grade A
https://content.naic.org/article/naic-members-approve-model-bulletin-use-ai-insurers
Confirms the adoption date (December 4, 2023) and the bulletin's scope.

---

## Empirical research

**Derrig, R. A., and L. Francis — "Distinguishing the Forest from the TREES: A Comparison of Tree-Based Data Mining Methods," *Variance* (Casualty Actuarial Society)** — Grade A
https://www.casact.org/sites/default/files/2021-07/Distinguishing-Forest-Derrig-Francis.pdf
The most valuable single source in this research. Uses the Massachusetts Automobile Insurers Bureau Detail Claim Database (162,761 third-party bodily injury liability claims, accident years 1995–1997) and reports held-out AUROC for eight model/software combinations against four targets. Supplies the hard numbers that undercut the assumption that red flags are strongly predictive: best SIU-decision AUROC 0.667, best SIU-favorable AUROC 0.678. Also supplies the SIU/IME base rates (7% and 8% in Massachusetts; ~2% and ~4% nationally per IRC), the ~50% favorable-outcome rate on SIU referrals, IME cost figures, the observation that most insurance databases contain no fraud label at all, and — critically — the explicit warning that closed-claim analysis overstates prospective performance because variables like total billed are not known until the claim is nearly closed. Full text extracted from the PDF directly. Caveat: 1990s data, one state, and a no-fault state with atypically high claim frequency.

**Viaene, S., Derrig, R. A., Baesens, B., and Dedene, G. — "A Comparison of State-of-the-Art Classification Techniques for Expert Automobile Insurance Claim Fraud Detection," *Journal of Risk and Insurance* (2002)** — Grade A, **accessed only via secondary citation**
https://www.semanticscholar.org/paper/c3a54de403073b57c01d7bc6953e30c603f566ac
The source of the finding that simple logistic regression performed as well as neural networks and support vector machines at predicting expert opinion on fraud suspicion — strong evidence that the red flag features, not the model class, are the binding constraint. Used ~1,400 Massachusetts PIP claims from 1993 accidents with mostly binary red flag predictors. **I did not access the full text**; all statements about this paper are as summarized by Derrig & Francis, who cite it directly. Treat as second-hand.

**Insurance Research Council — "Fraud and Buildup Add 13 to 18 Percent in Excess Payments to Auto Injury Claims" (press release)** — Grade A/B
https://insurance-research.org/news/fraud-and-buildup-add-13-18-percent-excess-payments-auto-injury-claims
The best available public prevalence data: 21% of BI and 18% of PIP claims closed with payment showed the appearance of fraud and/or buildup in 2012; $5.6–7.7bn in excess payments; buildup the most common form. Based on 35,000+ closed claims from twelve insurers representing 52% of the US market. **Key limitation: "appearance of fraud" is a claims professional's subjective assessment, not an adjudicated finding** — this is a suspicion rate. Graded A for methodology but B for access: only the press release is public; the full report is paywalled.

**Insurance Research Council — "Fraud and Buildup in Auto Injury Insurance Claims" (report landing page)** — Grade A (paywalled)
https://www.insurance-research.org/insurance-fraud/fraud-and-buildup-auto-injury-insurance-claims
Confirms the report's existence, scope, and 2015 publication date. Content is behind membership/purchase; recorded here so the citation is honest about what was and was not read.

**Insurance Journal — "Experts Puzzled by Decline in Insurance Fraud Tips via Technology" (2020)** — Grade B
https://www.insurancejournal.com/news/national/2020/08/25/580280.htm
Reports on the Coalition Against Insurance Fraud's biennial SIU benchmarking survey. Source of the most operationally important number found: SIU acceptance of referrals from automated systems fell to 15% from 22%. This is the incumbent baseline any AI signal will be judged against. Grade B because the underlying survey is not public and the figure could not be verified at source.

---

## Industry practice and reference

**O*NET OnLine — Claims Adjusters, Examiners, and Investigators (13-1031.00)** — Grade A
https://www.onetonline.org/link/summary/13-1031.00
US Department of Labor occupational data: the authoritative, non-commercial account of what adjusters actually do and which systems they use. Its technology list (claims platform + estimating software + document management + external databases + Excel + email) is the clearest evidence that the adjuster is the integration layer across fragmented systems — the factual basis for the project's core hypothesis. Used instead of the BLS Occupational Outlook Handbook, which returned 403.

**Insurance Information Institute — Background on Insurance Fraud** — Grade B
https://www.iii.org/article/background-on-insurance-fraud
Industry-body overview: SIU prevalence, state fraud bureaus, immunity reporting laws, and the description of ISO ClaimSearch as "the world's largest comprehensive database of claims information." Useful for establishing what third-party data sources exist. III is insurer-funded, so treat its framing of fraud magnitude as advocacy-adjacent.

**Verisk — ISO ClaimSearch** — Grade C
https://www.verisk.com/products/claimsearch/
Vendor page for the dominant cross-carrier claims database. Useful only for understanding what the system contains and how insurers query it — relevant because several of the most predictive structured signals (prior claims across carriers, recurring parties/providers/attorneys) require this data and are therefore unavailable to a project without it.

**National Insurance Crime Bureau — Investigative Assistance** — Grade B
https://www.nicb.org/law-enforcement/investigative-assistance
Describes NICB's role as an insurer-funded nonprofit receiving questionable-claim referrals and supporting law enforcement. Establishes a third-party data source in the adjuster's environment. Source of the questionable-claim referral-reason categories (faked/exaggerated injury, questionable theft, prior damage, fictitious loss) and the note that staged/caused accident is the reason most often paired with organized group activity.

**IRMI — The Examination Under Oath** — Grade B
https://www.irmi.com/articles/expert-commentary/the-examination-under-oath
Risk-management reference explaining the EUO: a sworn, transcribed examination the policy permits the insurer to compel, distinct from an unsworn recorded statement, with refusal potentially grounds for denial. Establishes that EUO is a serious legal escalation, not a routine investigative step — relevant to whether a product should ever recommend one.

**Coalition Against Insurance Fraud — "The Impact of Insurance Fraud on the U.S. Economy" (2022)** — Grade C
https://insurancefraud.org/wp-content/uploads/The-Impact-of-Insurance-Fraud-on-the-U.S.-Economy-Report-2022-8.26.2022.pdf
Source of the ubiquitous $308.6 billion figure, prepared by the Colorado State University Global White Collar Crime Task Force. Recorded because it is the number everyone cites, and flagged Grade C deliberately: the Coalition is an advocacy organization substantially funded by insurers, this was the first update in 27 years, and the methodology changed. Useful for market sizing; not evidence about any individual claim.

**PropertyCasualty360 — "10 red flags that could signal a fraudulent auto claim"** — Grade C
https://www.propertycasualty360.com/2016/03/16/10-red-flags-that-could-signal-a-fraudulent-auto-c/
Trade press compilation of practitioner red flags. Used only to assemble the commonly-cited indicator list in Section D.2 and to capture practitioner vocabulary. No empirical validation offered for any indicator.

**Zalma, B. — "Red Flags of Insurance Fraud"** — Grade C
https://barryzalma.substack.com/p/red-flags-of-insurance-fraud
Widely-cited insurance coverage attorney's red flag compilation. Source of the "three or more red flags" referral heuristic, which is repeated throughout practitioner training material but which I could find no empirical validation for — recorded as folklore with face validity, not as a validated rule.

---

## Sources consulted but not usable

Recorded for transparency and to avoid re-treading.

- **BLS Occupational Outlook Handbook, Claims Adjusters** (`bls.gov/ooh/...`) — returned HTTP 403. Substituted O*NET, which is the same underlying DOL occupational data.
- **California DOI SIU regulations PDF** (`insurance.ca.gov/0300-fraud/upload/revised_siu_regs.pdf`) — AES-encrypted, text not extractable. Substituted Cornell LII section-by-section text, which is equivalent and arguably more current.
- **Derrig, "The Economics of Insurance Fraud Investigation: Evidence of a Nash Equilibrium"** (NBER and actuaries.ie mirrors) — both returned 403. Would likely have added detail on investigation cost/benefit. Worth another attempt.
- **Derrig & Francis (2006)**, the companion paper containing variable-importance rankings for the 21 AIB predictors — not retrieved. **Directly relevant to open question 8** (which indicators actually carry predictive weight) and worth pursuing.
- **Derrig & Weisberg, "AIB PIP Claim Screening Experiment Final Report" (1998)** — the foundational study behind the Massachusetts red flag work, cited by Derrig & Francis. Not publicly available; would be the best source for the actual indicator taxonomy.
- **Insurance Research Council full reports** — paywalled; only press releases accessible.
- **Coalition Against Insurance Fraud SIU benchmarking survey** — not public; the 15% automated-referral acceptance figure is available only via trade press reporting.
- **Viaene et al. (2002) full text** — paywalled (Wiley); relied on Derrig & Francis's summary.
- **NAIC SIU Model Regulation (secondary sources cite it as "Model #901")** — the model number is asserted by vendor blogs and was not independently verified against NAIC's own model law index. Cited as unconfirmed in the research document.
