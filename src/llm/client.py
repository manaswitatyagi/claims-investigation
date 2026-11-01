"""The LLM seam.

Exactly two call sites exist in this project (`extraction/llm_extract.py` and
`differences/llm_propose.py`), and both go through this interface. Three
implementations:

  LiveClient     — calls Claude.
  RecordedClient — replays JSON from disk. Every unit test uses this; no test
                   ever touches the network.
  NullClient     — returns empty results, which proves the deterministic path
                   stands on its own. PRD §11 assigns seven of nine stages to
                   code, and a NullClient run is how we check that claim.

Model: claude-opus-5 with adaptive thinking. Structured output is constrained
with `output_config.format`, so the response is guaranteed-parseable JSON
rather than prose we have to scrape.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

MODEL_ID = "claude-opus-5"
#: Bumped when either prompt changes. Stamped on every SynthesisResult so a
#: result can never be attributed to the wrong contract.
PROMPT_VERSION = "e1-v2"
MAX_TOKENS = 16000


class LLMClient:
    """Interface. `model_id` is recorded on every SynthesisResult (D-020 P6)."""

    model_id: Optional[str] = None
    prompt_version: Optional[str] = None

    def complete_json(self, system: str, user: str, schema: Dict[str, Any],
                      tag: str = "") -> Dict[str, Any]:
        """`tag` identifies the call site, so recorded fixtures can key off it."""
        raise NotImplementedError


class NullClient(LLMClient):
    """No model. Used to demonstrate the deterministic path in isolation."""

    model_id = None
    prompt_version = None

    def complete_json(self, system: str, user: str, schema: Dict[str, Any],
                      tag: str = "") -> Dict[str, Any]:
        return {}


class RecordedClient(LLMClient):
    """Replay recorded responses, keyed by a caller-supplied tag.

    Deterministic by construction, which is what makes the test suite mean
    anything. Recording new fixtures is a deliberate act, not a side effect of
    running tests.
    """

    model_id = "recorded"
    prompt_version = PROMPT_VERSION

    def __init__(self, recordings: Dict[str, Any]) -> None:
        self._recordings = recordings
        self.calls: List[Dict[str, Any]] = []

    @classmethod
    def from_dir(cls, path: str) -> "RecordedClient":
        recordings: Dict[str, Any] = {}
        if os.path.isdir(path):
            for fn in sorted(os.listdir(path)):
                if fn.endswith(".json"):
                    with open(os.path.join(path, fn), "r", encoding="utf-8") as fh:
                        recordings[fn[:-5]] = json.load(fh)
        return cls(recordings)

    def complete_json(self, system: str, user: str,
                      schema: Dict[str, Any], tag: str = "") -> Dict[str, Any]:
        # The recorded payload is retained so tests can assert what was sent —
        # specifically that no raw passage text reaches the difference call.
        self.calls.append({"tag": tag, "system": system, "user": user})
        if tag not in self._recordings:
            return {}
        return self._recordings[tag]


class LiveClient(LLMClient):
    model_id = MODEL_ID
    prompt_version = PROMPT_VERSION

    def __init__(self, model: str = MODEL_ID, temperature_note: None = None) -> None:
        import anthropic  # imported lazily so the deterministic path needs no SDK
        self._anthropic = anthropic
        self._client = anthropic.Anthropic()
        self.model_id = model
        self.calls: List[Dict[str, Any]] = []

    def complete_json(self, system: str, user: str,
                      schema: Dict[str, Any], tag: str = "") -> Dict[str, Any]:
        self.calls.append({"tag": tag, "system": system, "user": user})
        response = self._client.messages.create(
            model=self.model_id,
            max_tokens=MAX_TOKENS,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": user}],
        )
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)
