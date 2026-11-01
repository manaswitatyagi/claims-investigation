"""Claim view server. Standard library only.

    ./.venv/bin/python -m src.presentation.server

Serves the presentation DTO at /api/claim/<id>/view and, when the frontend has
been built, the static app from src/presentation/static.

Deliberately not a framework. There is no auth, no database, no session, no
multi-claim workflow and no write path — the milestone is a read-only view over
artifacts that already exist.

DESIGNED FOR THE STREAMING MILESTONE, NOT IMPLEMENTING IT
--------------------------------------------------------
The view is normalised and id-addressable, so live ingestion becomes an
additional endpoint emitting patches against the same `assertion_id` /
`neighborhood_id` keys, rather than a redesign of the screen. `/api/health`
already reports `streaming: false` so a client can branch on it later.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from src.presentation.view_model import ROOT, build_claim_view

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

#: claim id -> (E2 run directory, fixture directory)
CLAIMS: Dict[str, Dict[str, str]] = {
    "claim_001": {
        "run_dir": os.path.join(ROOT, "data", "generated", "e2_ontology", "run_1"),
        "fixture_dir": os.path.join(ROOT, "data", "fixtures", "claim_001"),
    },
}

_CACHE: Dict[str, Any] = {}


def _llm():
    """The same OpenRouter client the E2 runs used. Configured by env."""
    import os as _os
    model = _os.environ.get("E1_OPENROUTER_MODEL", "google/gemini-3.8-flash")
    from src.llm.openrouter_client import OpenRouterClient
    return OpenRouterClient(model=model)

_MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json",
         ".svg": "image/svg+xml", ".ico": "image/x-icon", ".map": "application/json"}


def claim_view(claim_id: str, refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Always read from runtime state, so an uploaded document is reflected."""
    if claim_id not in CLAIMS:
        return None
    from src.runtime.claim_state import ClaimState
    return ClaimState.load(claim_id).view


class Handler(BaseHTTPRequestHandler):
    server_version = "ClaimView/0.1"

    def log_message(self, fmt, *args):        # quieter console during a demo
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def do_POST(self):                         # noqa: N802
        path = self.path.split("?", 1)[0]
        parts = path.strip("/").split("/")
        # /api/claim/<id>/documents  and  /api/claim/<id>/reset
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "claim":
            claim_id, action = parts[2], parts[3]
            if claim_id not in CLAIMS:
                return self._json({"error": "unknown claim"}, 404)
            if action == "reset":
                from src.runtime.claim_state import ClaimState
                ClaimState.reset(claim_id)
                return self._json({"ok": True, "claim_id": claim_id,
                                   "note": "Runtime state reset to the E2 baseline."})
            if action == "documents":
                return self._upload(claim_id)
        return self._json({"error": "not found"}, 404)

    def _upload(self, claim_id: str) -> None:
        import threading, uuid
        from src.runtime import ingest
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        filename = self.headers.get("X-Filename") or "uploaded.md"
        try:
            stored = ingest.store_document(claim_id, filename, body)
        except ingest.UnsupportedDocument as exc:
            return self._json({"error": str(exc)}, 400)

        session_id = uuid.uuid4().hex[:8]

        def work():
            try:
                ingest.process_document(claim_id, stored, _llm(), session_id)
            except Exception:                      # already emitted as processing_failed
                pass

        threading.Thread(target=work, daemon=True).start()
        return self._json({"accepted": True, "claim_id": claim_id,
                           "document_id": stored["document_id"],
                           "session_id": session_id,
                           "stream": "/api/claim/%s/stream" % claim_id}, 202)

    def do_GET(self):                          # noqa: N802
        path = self.path.split("?", 1)[0]

        if path == "/api/health":
            return self._json({"ok": True, "claims": sorted(CLAIMS),
                               "streaming": True, "transport": "sse",
                               "upload_formats": [".md", ".txt"],
                               "note": "Read-write demo over runtime claim state."})

        if path.startswith("/api/claim/") and path.endswith("/stream"):
            return self._sse(path[len("/api/claim/"):-len("/stream")])

        if path == "/api/claims":
            return self._json([{"claim_id": c} for c in sorted(CLAIMS)])

        if path.startswith("/api/claim/") and path.endswith("/view"):
            claim_id = path[len("/api/claim/"):-len("/view")]
            view = claim_view(claim_id, refresh="refresh=1" in self.path)
            if view is None:
                return self._json({"error": "unknown claim %r" % claim_id}, 404)
            return self._json(view)

        if path.startswith("/api/"):
            return self._json({"error": "not found"}, 404)

        return self._static(path)

    def _sse(self, claim_id: str) -> None:
        """Server-Sent Events. Chosen over WebSockets because every message in
        this milestone flows server -> client; the browser sends nothing back
        over the channel, so a duplex protocol would be unused complexity."""
        import queue as _q
        from src.runtime import events as _ev
        if claim_id not in CLAIMS:
            return self._json({"error": "unknown claim"}, 404)
        bus = _ev.bus_for(claim_id)
        q = bus.subscribe()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    event = q.get(timeout=15)
                except _q.Empty:
                    self.wfile.write(b": keepalive\n\n")   # holds the connection open
                    self.wfile.flush()
                    continue
                self.wfile.write(_ev.sse_frame(event))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass                                    # tab closed; normal
        finally:
            bus.unsubscribe(q)

    # -- helpers ---------------------------------------------------------

    def _json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path: str) -> None:
        if not os.path.isdir(STATIC_DIR):
            return self._json({"error": "frontend not built",
                               "hint": "cd web && npm install && npm run build"}, 503)
        rel = posixpath.normpath(path.lstrip("/")) or "index.html"
        target = os.path.join(STATIC_DIR, rel)
        # SPA fallback; also blocks traversal outside the static root.
        if not os.path.isfile(target) or not os.path.abspath(target).startswith(STATIC_DIR):
            target = os.path.join(STATIC_DIR, "index.html")
        with open(target, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type",
                         _MIME.get(os.path.splitext(target)[1], "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    ap = argparse.ArgumentParser(description="Claim view server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    built = os.path.isdir(STATIC_DIR)
    print("Claim view server on http://%s:%d" % (args.host, args.port))
    print("  api    : /api/claim/claim_001/view")
    print("  ui     : %s" % ("served from src/presentation/static" if built
                             else "NOT BUILT — run `cd web && npm run build`"))
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
