"""Claims Handoff Copilot — hosted demo WITH live ingestion.

WHY THIS EXISTS ALONGSIDE THE GITHUB PAGES BUILD. Pages serves the React app
against a baked snapshot, which covers everything except adding a document:
ingestion runs the real extraction and quote-location pipeline, and that is
Python. Streamlit is Python, so here a visitor can drop a `.md` or `.txt` file
and watch the real thing happen — extraction, span resolution, ontology
normalisation, neighbourhood recompute. Assertions whose quote cannot be located
are really dropped, not hidden.

WHAT IT REUSES. Everything. `src/runtime/ingest.process_document` is the same
function the local server calls, with the same `prompts_e2` extractor, the same
`quote_locator`, the same lookup tables and the same classifier. This file is a
view over that pipeline and adds no claim logic of its own — in particular it
never compares two assertion values to decide a relationship, exactly as the
React app is forbidden from doing.

PER-VIEWER ISOLATION. Streamlit Cloud runs every session in one container with
one filesystem, so file-backed claim state would mean one visitor's upload
appearing in everyone else's session — both confusing and a small privacy
problem, since the uploaded text would persist for strangers. Each session
therefore gets its own claim id, which gives it its own runtime directory, its
own lock and its own event bus. Nothing is shared and nothing survives the
container.

VERIFIED DOES NOT MEAN TRUE. The strongest thing this page says about an
assertion is that its quoted text was found at that offset in that document. A
verified citation on a false statement by a claimant is a correct output.
"""
from __future__ import annotations

import os
import sys
import uuid

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.runtime import claim_state as cs           # noqa: E402
from src.runtime import ingest                      # noqa: E402
from src.runtime.claim_state import ClaimState      # noqa: E402

BASE_CLAIM = "claim_001"
MODEL = "google/gemini-3.8-flash"

#: Tighter than ingest.MAX_BYTES (200 KB). A hosted demo pays per token for
#: whatever a stranger uploads, and a claim document that matters is short.
DEMO_MAX_BYTES = 40_000
#: One model-spending action per session. Not a security boundary — a session is
#: a browser tab — but it stops an idle hand from running the bill up.
MAX_UPLOADS_PER_SESSION = 1

REL_COLOUR = {
    "CORROBORATING": "#3fb950",
    "COMPATIBLE": "#58a6ff",
    "CONTRADICTORY": "#f0883e",
    None: "#7d8590",
}
REL_GLYPH = {"CORROBORATING": "=", "COMPATIBLE": "≈", "CONTRADICTORY": "≠", None: "·"}


# ---------------------------------------------------------------------------
# session
# ---------------------------------------------------------------------------

def api_key() -> str | None:
    """Secrets first, then the environment, so the same file runs hosted and
    locally. Never logged, never rendered."""
    try:
        key = st.secrets.get("OPENROUTER_API_KEY")       # type: ignore[union-attr]
        if key:
            return str(key)
    except Exception:                                    # no secrets.toml locally
        pass
    return os.environ.get("OPENROUTER_API_KEY")


def prune_old_sessions(max_age_hours: float = 6.0) -> int:
    """Delete stale per-session runtime directories.

    Per-session isolation trades one problem for another: a container that stays
    up accumulates a directory per visitor, each holding a ~90 KB view plus
    whatever was uploaded. Nothing cleans those up, so this does, on a boundary
    no live session can be using. Only `<base>_s<id>` directories are touched —
    never the real `claim_001`, which is the local demo's state.
    """
    import shutil
    import time

    removed = 0
    if not os.path.isdir(cs.RUNTIME_DIR):
        return 0
    cutoff = time.time() - max_age_hours * 3600
    prefix = BASE_CLAIM + "_s"
    for name in os.listdir(cs.RUNTIME_DIR):
        if not name.startswith(prefix):
            continue
        path = os.path.join(cs.RUNTIME_DIR, name)
        try:
            if os.path.isdir(path) and os.path.getmtime(path) < cutoff:
                shutil.rmtree(path)
                removed += 1
        except OSError:
            pass            # a live session may be writing; leave it alone
    return removed


def session_claim_id() -> str:
    """A claim id unique to this browser session.

    `ClaimState` keys its directory, its lock and its event bus off the claim
    id, so a per-session id is the whole isolation mechanism — no change to the
    runtime was needed to make it safe to host.
    """
    if "claim_id" not in st.session_state:
        prune_old_sessions()
        sid = uuid.uuid4().hex[:10]
        cid = "%s_s%s" % (BASE_CLAIM, sid)
        # Same seed as the real claim: the frozen E2 run.
        cs.SEED[cid] = cs.SEED[BASE_CLAIM]
        st.session_state.claim_id = cid
        st.session_state.uploads_used = 0
        st.session_state.last_summary = None
        st.session_state.error = None
    return st.session_state.claim_id


# ---------------------------------------------------------------------------
# ingestion
# ---------------------------------------------------------------------------

def ingest_upload(cid: str, name: str, raw: bytes) -> None:
    from src.llm.openrouter_client import OpenRouterClient

    st.session_state.error = None
    if len(raw) > DEMO_MAX_BYTES:
        st.session_state.error = (
            "This hosted demo caps uploads at %d KB; that file is %d KB. Run it "
            "locally for larger documents." % (DEMO_MAX_BYTES // 1000, len(raw) // 1000))
        return
    try:
        stored = ingest.store_document(cid, name, raw)
    except ingest.UnsupportedDocument as exc:
        st.session_state.error = str(exc)
        return

    llm = OpenRouterClient(model=MODEL, api_key=api_key())
    with st.spinner("Extracting, locating every quote in the source text, recomputing…"):
        try:
            st.session_state.last_summary = ingest.process_document(cid, stored, llm)
            st.session_state.uploads_used += 1
        except Exception as exc:                     # surfaced, never swallowed
            # The source is already marked failed in claim state by
            # process_document, so the sources list will show it as failed too.
            st.session_state.error = "%s: %s" % (type(exc).__name__, str(exc)[:400])


# ---------------------------------------------------------------------------
# graph
# ---------------------------------------------------------------------------

def graph_dot(view: dict, show_singletons: bool) -> str:
    """Entity -> property -> source as DOT.

    Same three columns as the React graph and the same rule: every colour here
    is the relationship the backend computed, carried not derived. `rank=same`
    pins the columns so the picture is the claim's controlled structure rather
    than whatever a layout engine discovers.
    """
    nbs = {n["neighborhood_id"]: n for n in view["neighborhoods"]}
    lines = [
        "digraph claim {",
        '  rankdir=LR; bgcolor="#161b22"; pad=0.3; nodesep=0.18; ranksep=2.2;',
        '  node [fontname="Helvetica" fontsize=10 style=filled '
        'color="#2a323d" fontcolor="#e6edf3"];',
        '  edge [color="#56606d" arrowsize=0.5 penwidth=0.8];',
    ]

    ent_ids, prop_ids, src_ids = [], [], []
    shown: list[dict] = []

    for e in view["entities"]:
        own = [nbs[i] for i in e["neighborhood_ids"] if i in nbs]
        if not show_singletons:
            own = [n for n in own if not n["singleton"]]
        if not own:
            continue
        ent_ids.append(e["entity_id"])
        flag = " ⚠" if e.get("contradiction_count") else ""
        lines.append('  "%s" [label="%s%s" shape=box fillcolor="#1b222c"];'
                     % (e["entity_id"], e["label"].replace('"', "'"), flag))
        for n in own:
            shown.append(n)
            prop_ids.append(n["neighborhood_id"])
            rel = n["relationship"] if not n["singleton"] else None
            lines.append(
                '  "%s" [label="%s %s" shape=box fillcolor="#1b222c" color="%s" '
                'penwidth=%s];'
                % (n["neighborhood_id"], REL_GLYPH[rel],
                   n["predicate_label"].replace('"', "'"), REL_COLOUR[rel],
                   "2.4" if rel == "CONTRADICTORY" else "1.0"))
            lines.append('  "%s" -> "%s" [color="%s"];'
                         % (e["entity_id"], n["neighborhood_id"], REL_COLOUR[rel]))

    reached = {s for n in shown for s in n["source_ids"]}
    for s in view["sources"]:
        src_ids.append(s["source_id"])
        orphan = s["source_id"] not in reached
        # A source that contributed nothing is still drawn, and says which of
        # the two reasons applies. Omitting it would hide a grounding failure on
        # a screen whose subject is provenance.
        note = ""
        if orphan:
            note = ("\\nno assertion survived grounding"
                    if not s.get("verified_assertion_count")
                    else "\\nnone about the entities shown")
        lines.append('  "%s" [label="%s%s" shape=box fillcolor="#1b222c" color="%s" '
                     'style="filled,%s"];'
                     % (s["source_id"], s["name"].replace('"', "'"), note,
                        "#f0883e" if orphan else "#2a323d",
                        "dashed" if orphan else "solid"))
    for n in shown:
        rel = n["relationship"] if not n["singleton"] else None
        for sid in n["source_ids"]:
            lines.append('  "%s" -> "%s" [color="%s"];'
                         % (n["neighborhood_id"], sid, REL_COLOUR[rel]))

    for group in (ent_ids, prop_ids, src_ids):
        if group:
            lines.append("  { rank=same; %s }"
                         % " ".join('"%s";' % i for i in group))
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Claims Handoff Copilot", page_icon="🗂", layout="wide")

cid = session_claim_id()
state = ClaimState.load(cid)
view = state.view
claim = view["claim"]
key_present = bool(api_key())

st.title(claim.get("claim_number") or claim["claim_id"])
cols = st.columns(4)
cols[0].metric("Loss date", claim.get("loss_date") or "—")
cols[1].metric("Checkpoint", claim.get("checkpoint") or "—")
cols[2].metric("Status", (claim.get("status") or "—").replace("_", " "))
tally = {"CORROBORATING": 0, "COMPATIBLE": 0, "CONTRADICTORY": 0, "single": 0}
for n in view["neighborhoods"]:
    if n["singleton"] or not n["relationship"]:
        tally["single"] += 1
    else:
        tally[n["relationship"]] += 1
cols[3].metric("Contradictory properties", tally["CONTRADICTORY"])

st.error(
    "**Verified means traced, not true.** %s" % claim["verified_means"], icon="⚠️")
st.info(
    "**Synthetic claim.** No real claim, person or crash record is involved. Seeded "
    "from the frozen E2 run, so the figures match `docs/experiments/E2.md`. Your "
    "session is isolated — nothing you upload is visible to anyone else, and it is "
    "discarded when the app restarts.", icon="🧪")

# -- sidebar ---------------------------------------------------------------
with st.sidebar:
    st.header("Sources")
    for s in view["sources"]:
        bad = s.get("verification_status") == "failed"
        drop = s.get("dropped_assertion_count") or 0
        st.markdown(
            "**%s**  \n`%s` · %d verified%s%s"
            % (s["name"], s.get("type", ""), s.get("verified_assertion_count") or 0,
               " · %d dropped" % drop if drop else "",
               " · **failed**" if bad else ""))
        if bad and s.get("error"):
            st.caption(s["error"])

    st.divider()
    st.header("Add evidence")
    left = MAX_UPLOADS_PER_SESSION - st.session_state.uploads_used
    if not key_present:
        st.warning(
            "Ingestion is off: no `OPENROUTER_API_KEY` is configured. Everything "
            "else on this page works. Set the secret to enable it.", icon="🔑")
    elif left <= 0:
        st.info("Upload used for this session. Reset below to start over.", icon="✅")
    else:
        st.caption(
            "A `.md` or `.txt` file, up to %d KB. This runs the real pipeline — "
            "extraction, then quote location in code. Anything whose quote cannot "
            "be found in your text is dropped, not guessed."
            % (DEMO_MAX_BYTES // 1000))
        up = st.file_uploader("Document", type=["md", "txt"],
                              label_visibility="collapsed")
        if up is not None and st.button("Ingest", type="primary"):
            ingest_upload(cid, up.name, up.getvalue())
            st.rerun()

    if st.session_state.error:
        st.error(st.session_state.error, icon="🚫")

    st.divider()
    if st.button("Reset to the E2 baseline"):
        ClaimState.reset(cid)
        st.session_state.uploads_used = 0
        st.session_state.last_summary = None
        st.session_state.error = None
        st.rerun()

    st.divider()
    st.caption("Not assessed by design")
    for n in view.get("not_assessed", []):
        st.caption("· %s" % n)

# -- what the last ingestion did -------------------------------------------
summary = st.session_state.last_summary
if summary:
    st.subheader("What that document changed")
    m = st.columns(5)
    m[0].metric("Extracted", summary["extracted"])
    m[1].metric("Verified", summary["verified"])
    m[2].metric("Dropped", summary["dropped"], help="Quote not locatable in the source")
    m[3].metric("Mapped to ontology", summary["mapped"])
    m[4].metric("Kept unresolved", summary["unresolved"])
    changes = summary.get("relationship_changes") or []
    if changes:
        st.write("**Relationships that changed**")
        for c in changes:
            st.markdown(
                "- **%s**: `%s` → `%s` — %s"
                % (c["predicate_label"], c["from"], c["to"], c["rationale"]))
        st.caption("Describes the relationship among assertions only. It does not "
                   "mean any source is right or wrong.")
    elif summary.get("neighborhoods_updated"):
        st.caption("Positions were added, but no relationship changed.")

# -- tabs ------------------------------------------------------------------
singles = st.toggle("Show single-source properties (%d)" % tally["single"], value=False)
tab_map, tab_graph, tab_time = st.tabs(["Evidence map", "Graph", "Timeline"])

with tab_map:
    nbs = {n["neighborhood_id"]: n for n in view["neighborhoods"]}
    for e in view["entities"]:
        own = [nbs[i] for i in e["neighborhood_ids"] if i in nbs]
        if not singles:
            own = [n for n in own if not n["singleton"]]
        if not own:
            continue
        st.markdown("#### %s  <span style='color:#6e7d8c;font-size:13px'>%s</span>"
                    % (e["label"], e["type"]), unsafe_allow_html=True)
        for n in own:
            rel = n["relationship"] if not n["singleton"] else None
            with st.expander(
                    "%s  %s — %s" % (REL_GLYPH[rel], n["predicate_label"],
                                     "single source" if n["singleton"]
                                     else (n["relationship"] or "not compared")),
                    expanded=(rel == "CONTRADICTORY")):
                for aid in n["assertion_ids"]:
                    a = view["assertions"].get(aid)
                    if not a:
                        continue
                    ev_ = a.get("evidence") or {}
                    st.markdown("**%s** · %s  \n%s"
                                % (a["source_name"],
                                   a["asserter_kind"].replace("_", " "),
                                   a["text"]))
                    if ev_.get("quote"):
                        st.caption("“%s”" % ev_["quote"])
                        where = ev_.get("passage_label") or ev_.get("field_record") or ""
                        span = ("chars %s–%s" % (ev_.get("char_start"), ev_.get("char_end"))
                                if ev_.get("char_start") is not None else "")
                        st.caption("Evidence verified · %s %s" % (where, span))
                    st.divider()
                st.caption(n["rationale"])

with tab_graph:
    st.caption(
        "Entity → property → source. Colour is the relationship the backend computed; "
        "nothing on this page compares two values to decide one. A dashed source "
        "contributed nothing to the properties shown.")
    st.graphviz_chart(graph_dot(view, singles), width="stretch")

with tab_time:
    a, b = st.columns(2)
    with a:
        st.subheader("Occurred")
        for e in view["timeline"]["occurred"]:
            st.markdown("**%s** — %s" % (e.get("when") or "date not established",
                                         e["label"]))
            if e.get("raw_expression") and not e.get("when"):
                st.caption("stated as “%s” · left vague on purpose"
                           % e["raw_expression"])
    with b:
        st.subheader("Became known")
        for e in view["timeline"]["became_known"]:
            st.markdown("**%s** — %s" % (e.get("when") or "—", e["label"]))

st.divider()
st.caption("%s · model %s · prompts %s" % (view["view_version"],
                                           claim.get("model_id"),
                                           claim.get("prompt_version")))
st.caption(claim["provenance_disclaimer"])
