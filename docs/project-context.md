# Project context brief

**Derived summary. Generated 2026-09-10. It will go stale.**

Written to bring an outsider — another model, a collaborator, or me after three
months away — up to speed in one read. It restates facts that live elsewhere, so
where it disagrees with an authoritative source, the source wins:

| Authoritative for | Source |
| --- | --- |
| Product definition | `product/v1-prd.md` |
| Output contract and domain model | `data/schema.md` |
| Every decision and its reasoning | `docs/decision_log.md` |
| Research findings and their grading | `research/claims-synthesis-research.md` |
| Experiment results | `docs/experiments/E1.md`, `E1b.md`, `E2.md` |
| Working agreement | `CLAUDE.md` |

**Usage.** Paste the whole thing below the line into an external model, then add
your question at the end. It deliberately reports the experiment that *failed to
help* (E2 arm B) and ends with the untested assumptions — a version that omitted
either would invite confident advice on a premise nobody has checked.

**Refresh it** whenever a numbered decision is added, an experiment runs, or the
practitioner study finally happens. Regenerating is cheap; a stale brief that
reads as current is not.

---

Read all of this before responding. At the end there is a question.

## WHAT IT IS

**Claims Handoff Copilot** — a learning project about product management, insurance claims workflows, LLM application architecture, evaluation, and responsible AI. Not a startup, not going to production.

**The product hypothesis:** An adjuster *inheriting* a contested, long-lived personal auto claim can reach a defensible account of it faster when given an evidence-backed, span-cited representation of what each source asserts, where sources disagree, and what remains unresolved — WITHOUT the system asserting which disagreements matter, which account is true, or what the claim is worth.

Promise: "Inherit a claim without inheriting the guesswork."

The directory is still called `Claim Fraud Signal Flagger` — historical. It started as a fraud flagger and pivoted away on evidence.

## HOW IT GOT HERE (this order matters)

**Phase 1–2, research.** ~2,000 lines of graded research (sources rated A/B/C, every claim tagged REGULATION / INDUSTRY / EMPIRICAL / INFERENCE / UNCERTAIN). Findings that shaped everything:

- The fraud framing was dropped. Best published models on auto-fraud indicators reach AUROC ~0.667. Every published "fraud rate" is a *suspicion* rate; there is no adjudicated public ground truth.
- **The industry's most-quoted productivity stat is fabricated.** "Adjusters spend 50–70% of time on admin (McKinsey/Accenture)" traces to a vendor blog citing neither. It is *barred* from the project. So the core time premise is UNMEASURED, not proven.
- Incumbents already ship claim summarization (CLARA, Verisk Discovery Navigator + XactAI, Guidewire inside ClaimCenter, EvolutionIQ). They all do *volume reduction within one corpus* (mostly medical records). None does *cross-document reconciliation*. That gap is the only defensible position.
- Multi-document summarization research: up to 75% hallucinated content; GPT-4o confidently summarizes entirely non-existent topics 44% of the time.

**Verdict recorded: PROMISING BUT UNVALIDATED**, with a scope correction. Synthesis does NOT help on 100% of claims — clear-liability property-damage claims have nothing to synthesize and are being automated away. Value concentrates in long-lived, multi-handler, contested claims.

**Phase 3, domain model.** Entities that survived: Claim, Policy, Document, Passage, Fact, Difference, OpenQuestion, HumanDecision, Synthesis. Entities deliberately CUT: Evidence (became a Citation value object), PriorClaim, TimelineEvent (derived, not stored), Signal, Inference.

## THE THREE TECHNICAL EXPERIMENTS (all run live, all reported)

**E1 — baseline.** Model returns assertion + quote + character offsets. Result: 33 of ~40 extracted facts DROPPED. Every single drop was `offset_drift`; `text_absent_from_passage` was ZERO across all 3 runs. The model quoted correctly every time and miscounted positions, error accumulating through the passage (0, −4, −4, −4, −9, −8, −13). Fact recall 0.52–0.69. Planted contradiction found in 1 of 3 runs.

**E1b — the fix.** Model returns the quote only; **deterministic code locates it** and computes offsets. One line of the prompt changed. Result: fact recall **1.000 across all 3 runs**, zero drops, extracted facts surviving went 2/6/1 → 17/18/17, planted contradiction found 3 of 3, cost down 62%. Grounding stopped being the bottleneck.

**E2 — ontology vs graph.** Added `(subject_entity_id, predicate, value, event_id)` to each fact plus a controlled vocabulary, then A/B'd two difference-detection strategies over the SAME fact set:
- Arm A: all 57 facts → 1 model call
- Arm B: deterministic `groupby(entity, event, predicate)` → 8–9 narrow calls

**Arm B did NOT improve difference detection and cost more.** Both: recall 1.00, zero false positives. What Arm B DID deliver: neighbourhood keys **identical across all 3 runs (32/32)** where the flat arm's grouping key was model-invented and drifted; **corroboration became expressible** (7–9 per run — the flat model has no slot for agreement at all); and three category errors prevented *structurally* rather than by prompt instruction (vehicle speed vs posted speed limit; occupant count vs occupant observation; per-vehicle contact points).

**Conclusion recorded: the ontology is the load-bearing part, the graph topology is not.** No graph database, no GraphRAG, no in-memory graph abstraction was built — everything came from four fields on a dataclass and a `groupby`.

## ARCHITECTURE (deliberate exclusions matter as much as inclusions)

Fixed 9-stage pipeline, executed in order, once. **No agents, no RAG, no vector DB, no graph DB, no orchestration framework.** RAG is excluded on *faithfulness* grounds, not complexity: a C4 claim file fits in context whole, and retrieval would hide documents from the extractor — an omission is invisible where a hallucination is not.

Exactly **two** LLM call sites. Everything else is code: date arithmetic, timeline ordering, counts, structured field reads, policy checks, completeness checklist, citation verification, assembly.

Four invariants, each enforced by a test rather than a convention:
1. **Drop, never soften.** An uncitable assertion is discarded, not hedged. Hedged-but-present content is worse than absent content because it looks verified.
2. **Generation never sees a raw document.** The difference stage takes `List[Fact]` and has no parameter through which a document could reach it. A test asserts the payload equals the rendered fact set exactly.
3. **A structured document cannot reach a model.** An FNOL's ~100 fields are read by code; only its narrative box becomes a passage.
4. **Materiality is never asserted and cannot be scored by accident.** The schema types the field `null`, assembly raises if populated, and the evaluation runner raises on any metric name containing material/importance/severity/suspicion/credibility.

## WHAT'S BUILT

~9,400 lines Python, ~1,250 lines React/TypeScript, ~5,700 lines of docs/research. **211 tests, none touching the network.**

- Full pipeline: ingestion → extraction (LLM) → deterministic quote location → citation verification → ontology normalization → deterministic neighbourhoods → relationship classification → assembly
- Evaluation harness with per-metric reporting (deliberately **no composite score** — one number would hide the failures that matter), plus per-stage failure classification (extraction / grounding / attribution / normalization / difference_proposal / runtime_completion), each failure carrying the evidence that justifies it
- Freeze manifests digesting 22 files so experiments stay reproducible; E1's manifest still verifies after all subsequent work
- 3 synthetic fixtures with authored gold answers, including a **zero-conflict control** (correct output is an empty list)
- React UI: Sources panel, Evidence Map (entity → property, not a force-directed hairball), Evidence Inspector (exact quote highlighted in surrounding passage text, with passage id and offsets), two-axis Timeline
- Live document ingestion: upload a `.md`/`.txt`, watch SSE events stream, see neighbourhoods recompute and relationships change in real time

**26 numbered decision-log entries**, each with Context / Decision / Alternatives / Consequences / Revisit-if.

## RULES I HOLD TO

- **"Verified" means traced to exact source text and checked in code. It does NOT mean true.** The UI says "Evidence verified", never "Fact verified".
- The system never decides which source is correct, which differences matter, whether anyone is credible, liability, or fraud.
- Synthetic fixtures measure *what we planted*, never real-world performance — stated in the artifacts themselves.
- Don't use an LLM where code works. Don't add entities because they look architecturally elegant.
- Failures get reported, not smoothed. Two of my own bugs were found and disclosed rather than quietly fixed.

## THE HONEST STATE

**Zero claims professionals have been consulted.** Every technical experiment succeeded and none of them touched the actual product risk. The three highest-risk assumptions are still exactly as untested as on day one:

1. That the bottleneck is *comprehension* (reading what you have) rather than *acquisition* (chasing what you don't). If it's acquisition, the product inverts and most of the LLM becomes unnecessary.
2. That an adjuster will *rely* on the synthesis rather than re-read behind it. If they verify every citation, time saved is zero or negative — and given claim files are discoverable in litigation, verifying is rational.
3. That "material conflict" is a category two experienced adjusters would agree on. If inter-rater agreement is at chance, there is no ground truth to build or evaluate against, and the conflict feature — the only differentiated part — doesn't exist.

A gate is recorded: no product code past the prototype until a 5–8 practitioner study runs. Its headline metric is inter-rater agreement on materiality. Everything built so far is technically ahead of that gate.

---

**Add your question here when pasting this to an external model.**
