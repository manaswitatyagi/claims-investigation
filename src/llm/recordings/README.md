# Recorded LLM responses

These are **hand-constructed** responses, not captured model output. They exist
so the test suite and the `--client recorded` path are deterministic and never
touch the network.

`claim_000_smoke` is deliberately imperfect. It contains:

  * a **fabricated span** — quoted text that does not appear in the passage.
    The drop rule must remove it, and it must never reach the output.
  * an **offset drift** — correct quoted text with wrong character offsets.
    Also dropped, but diagnosed differently, because a model that can nearly
    cite is a different problem from one that invents.
  * a **misattribution** — a witness's statement credited to the claimant.
    This one is *not* caught by the drop rule (the span resolves fine), which
    is exactly why asserter accuracy is scored separately. It is the error most
    likely to be invisible in evaluation and damaging in a deposition.

Because these are authored, **metrics produced with `--client recorded` measure
the plumbing, not a model.** Only `--client live` produces an E1 result.
