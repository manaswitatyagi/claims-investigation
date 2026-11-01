"""Bake the claim view into a JSON file the static demo can fetch.

WHY A SNAPSHOT WORKS AT ALL. The UI consumes exactly one contract — the
`claim-view/1` DTO — and that DTO is already computed server-side from a frozen
E2 run. Sources, the evidence map, the inspector, the timeline and the graph are
all projections of it, so a file serves them as well as a process does. Only the
upload path needs Python, because ingestion runs the real extraction pipeline.

WHAT THE STATIC DEMO THEREFORE CANNOT DO. Add a document. That is disabled in
the UI with the reason stated, rather than mocked: a fake ingestion that
produced plausible assertions without running the locator would be a
demonstration of nothing, on a page whose whole claim is that every assertion is
traced to a span.

The snapshot is generated from the SEED, not from `data/runtime/`. Runtime state
carries whatever was ingested on the machine that last ran the demo, which is
not a thing to publish — the published page should show the frozen E2 run that
the experiments document, so a visitor sees the same numbers E2 reports.

Usage:
    ./.venv/bin/python tools/build_static_snapshot.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.presentation.view_model import build_claim_view  # noqa: E402

OUT = os.path.join(ROOT, "web", "public", "claim-view.json")
RUN_DIR = os.path.join(ROOT, "data", "generated", "e2_ontology", "run_1")
FIXTURE_DIR = os.path.join(ROOT, "data", "fixtures", "claim_001")


def main() -> int:
    view = build_claim_view(RUN_DIR, FIXTURE_DIR)

    # The DTO must reach the page unaltered. A snapshot that quietly differed
    # from what the server serves would make the hosted demo a different product
    # from the one the experiments measured.
    assert view["view_version"] == "claim-view/1", view["view_version"]
    assert view["claim"]["verified_means"], "the verified-means disclaimer must survive"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(view, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")

    size = os.path.getsize(OUT)
    print("wrote %s (%.1f KB)" % (os.path.relpath(OUT, ROOT), size / 1024.0))
    print("  sources        %d" % len(view["sources"]))
    print("  entities       %d" % len(view["entities"]))
    print("  neighbourhoods %d" % len(view["neighborhoods"]))
    print("  assertions     %d" % len(view["assertions"]))
    print("  seeded_from    %s" % view.get("seeded_from"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
