"""OpenRouter adapter.

NOT part of the frozen set. Added alongside `LiveClient` rather than replacing
it, so `src/llm/client.py` keeps its frozen digest.

WHAT THIS CHANGES ABOUT THE EXPERIMENT
--------------------------------------
The original freeze pinned `claude-opus-5` on the Anthropic API with adaptive
thinking. Routing through OpenRouter to a different model changes two variables
at once — provider and model — so a run made with this client is **not** the
Anthropic baseline and must never be reported as one. It is a valid experiment
asking the same question of a different machine.

What is deliberately held constant: both system prompts, both JSON schemas, the
passage text, the fact set handed to the difference stage, the pipeline, and the
gold answer. Prompts are sent byte-identical — no per-model rewording, which
would make the two runs incomparable for the reason the freeze exists.

WHAT IT SENDS
-------------
OpenRouter's surface is OpenAI-compatible, so three mappings are unavoidable:

  Anthropic                          OpenRouter / OpenAI
  system="..."                  ->   messages[0] = {"role": "system", ...}
  output_config.format          ->   response_format.json_schema (strict)
  thinking={"type":"adaptive"}  ->   reasoning={"enabled": true}

The third is an analogue, not an equivalent. The frozen configuration had
reasoning on, so it is enabled here to stay closest to that intent — but the
full request body is recorded on every call, so nothing rests on this note being
remembered.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from src.llm.client import MAX_TOKENS, PROMPT_VERSION, LLMClient

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

#: Transport-level only: 429 and 5xx and timeouts. NOT correctness retries — a
#: response is never re-requested because its content was judged wrong, and no
#: voting or best-of selection happens anywhere. Every retry is counted and
#: reported so the distinction is auditable rather than asserted.
TRANSPORT_RETRIES = 2
RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504}


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient(LLMClient):
    prompt_version = PROMPT_VERSION      # prompts are unchanged; only the model differs

    def __init__(self, model: str, api_key: Optional[str] = None,
                 reasoning: bool = True, timeout: float = 180.0) -> None:
        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not set. Export it or put it in .env "
                "(gitignored) — it is never written into source.")
        self._key = key
        self.model_id = model
        self._reasoning = reasoning
        self._timeout = timeout
        self.calls: List[Dict[str, Any]] = []
        self.transport_retries = 0
        self.parse_failures: List[Dict[str, Any]] = []

    # -- request shaping ----------------------------------------------------

    def _body(self, system: str, user: str, schema: Dict[str, Any],
              tag: str) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": self.model_id,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": _schema_name(tag), "strict": True,
                                "schema": schema},
            },
        }
        if self._reasoning:
            body["reasoning"] = {"enabled": True}
        return body

    def complete_json(self, system: str, user: str, schema: Dict[str, Any],
                      tag: str = "") -> Dict[str, Any]:
        body = self._body(system, user, schema, tag)
        raw_text, usage, meta = self._post(body, tag)

        record = {"tag": tag, "system": system, "user": user,
                  "request_body": body, "raw_text": raw_text,
                  "usage": usage, "provider_meta": meta}
        self.calls.append(record)

        try:
            parsed = json.loads(raw_text)
        except (json.JSONDecodeError, TypeError) as exc:
            # Do NOT repair the output. Unparseable JSON under a strict schema is
            # a finding about the model, and silently patching it would erase the
            # finding. The empty dict flows on as "no facts", and the failure is
            # recorded here for the report.
            self.parse_failures.append({"tag": tag, "error": str(exc),
                                        "raw_text": raw_text})
            record["parse_error"] = str(exc)
            return {}
        record["parsed"] = parsed
        return parsed

    # -- transport ----------------------------------------------------------

    def _post(self, body: Dict[str, Any], tag: str):
        last = None
        for attempt in range(TRANSPORT_RETRIES + 1):
            req = urllib.request.Request(
                ENDPOINT, data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": "Bearer %s" % self._key,
                         "Content-Type": "application/json",
                         "X-Title": "Claims Handoff Copilot E1"})
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    payload = json.load(resp)
                break
            except urllib.error.HTTPError as exc:
                last = "HTTP %s: %s" % (exc.code, exc.read().decode("utf-8")[:400])
                if exc.code not in RETRY_STATUS or attempt == TRANSPORT_RETRIES:
                    raise OpenRouterError("%s failed — %s" % (tag, last))
            except Exception as exc:                      # noqa: BLE001 - transport
                last = "%s: %s" % (type(exc).__name__, exc)
                if attempt == TRANSPORT_RETRIES:
                    raise OpenRouterError("%s failed — %s" % (tag, last))
            self.transport_retries += 1
            time.sleep(2 ** attempt)

        if payload.get("error"):
            raise OpenRouterError("%s returned an error: %s" % (tag, payload["error"]))
        choices = payload.get("choices") or []
        if not choices:
            raise OpenRouterError("%s returned no choices: %s" % (tag, str(payload)[:300]))
        message = choices[0].get("message") or {}
        meta = {"provider": payload.get("provider"), "id": payload.get("id"),
                "model": payload.get("model"),
                "finish_reason": choices[0].get("finish_reason"),
                "native_finish_reason": choices[0].get("native_finish_reason")}
        return message.get("content"), payload.get("usage"), meta


def _schema_name(tag: str) -> str:
    return "difference_proposal" if tag == "differences" else "fact_extraction"
