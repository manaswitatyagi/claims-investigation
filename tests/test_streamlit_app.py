"""The Streamlit app is held to the same rules as the React one.

It is a second presentation layer over one pipeline, and a second presentation
layer is where the rules quietly diverge: it renders in Python, next to the
domain code, so comparing two assertion values is one line away rather than
across an HTTP boundary. These tests close that gap.

`streamlit` is an optional dependency for the experiments, so everything that
needs the runtime skips without it rather than failing a clone that never
intends to host anything.
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "streamlit_app.py")


def _src():
    with open(APP, encoding="utf-8") as fh:
        return fh.read()


def test_the_app_exists_where_streamlit_cloud_looks_for_it():
    assert os.path.isfile(APP), "Streamlit Community Cloud defaults to streamlit_app.py"


def test_the_app_never_derives_a_relationship():
    """Same rule as test_react_never_derives_a_relationship.

    Relationship meaning stays in the domain layer. Reading `relationship` and
    branching on it for display is fine; computing one by comparing values is
    not — and in Python, unlike in React, the temptation is a single line away.
    """
    src = _src()
    for pattern in ("computeRelationship", "classify(", "build_neighborhoods(",
                    'a["value"] ==', 'a["value"] !=', "value_normalised =="):
        assert pattern not in src, (
            "%r in streamlit_app.py looks like the view deciding a relationship" % pattern)
    assert "REL_COLOUR" in src and "relationship" in src, (
        "it must still READ the backend's verdict")


def test_the_app_asserts_no_materiality_or_credibility():
    src = _src().lower()
    for banned in ("materiality", "credibility", "liability", "fraud",
                   "suspicion", "is lying", "at fault"):
        assert banned not in src, "%r must not appear in the hosted view" % banned


def test_verified_means_traced_is_shown_not_paraphrased():
    src = _src()
    assert "Verified means traced, not true" in src
    assert 'claim["verified_means"]' in src, (
        "the disclaimer must come from the DTO, not be retyped in the view")


def test_ingestion_is_guarded_against_spending_a_strangers_budget():
    src = _src()
    assert "DEMO_MAX_BYTES" in src and "40_000" in src
    assert "MAX_UPLOADS_PER_SESSION" in src
    assert "api_key()" in src, "ingestion must be disabled when no key is configured"


def test_each_session_is_isolated():
    """Per-session claim id is the whole isolation mechanism.

    Streamlit Cloud runs every session in one container with one filesystem, so
    a shared claim id would publish one visitor's upload to every other viewer.
    """
    src = _src()
    assert "session_claim_id" in src
    assert "cs.SEED[cid] = cs.SEED[BASE_CLAIM]" in src, (
        "the per-session claim id must be registered against the same seed")
    assert re.search(r'uuid\.uuid4\(\)\.hex', src), "the session id must be unique"


def test_the_key_is_never_rendered():
    src = _src()
    assert "st.write(api_key" not in src
    assert "st.code(api_key" not in src
    assert 'st.secrets.get("OPENROUTER_API_KEY")' in src
    # The key reaches the client as an argument, never through source.
    assert "sk-or-v1-" not in src, "no key material in the app source"


def test_secrets_file_is_gitignored():
    with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as fh:
        assert ".streamlit/secrets.toml" in fh.read()


def test_requirements_pin_streamlit_for_the_cloud_build():
    with open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8") as fh:
        assert re.search(r"^streamlit==", fh.read(), re.M), (
            "Streamlit Cloud installs from requirements.txt")


# ---------------------------------------------------------------------------
# Behaviour, when streamlit is installed.
# ---------------------------------------------------------------------------

streamlit = pytest.importorskip("streamlit", reason="streamlit is optional")


@pytest.fixture(scope="module")
def rendered():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    return at


def test_the_page_renders_without_an_exception(rendered):
    assert list(rendered.exception) == [], [e.value for e in rendered.exception]


def test_the_page_reports_the_frozen_e2_figures(rendered):
    labels = {m.label: m.value for m in rendered.metric}
    assert labels["Checkpoint"] == "C3"
    # One planted contradiction, found by E1b in 3 of 3 runs. If this changes,
    # either the seed moved or the classifier did, and both deserve attention.
    assert labels["Contradictory properties"] == "1"


def test_ingestion_is_off_without_a_key(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    assert list(at.exception) == []
    assert len(at.get("file_uploader")) == 0, "no uploader without a key"
    assert any("OPENROUTER_API_KEY" in w.value for w in at.warning), (
        "the reason must be stated, not left as a missing control")


def test_the_graph_matches_the_react_layout_counts():
    """Both graphs must show the same structure.

    The React layout and this DOT builder are separate code, so they can drift.
    The node and edge counts are the cheapest check that they still describe one
    claim; the React figures come from running its layout against the same seed.
    """
    import importlib.util

    from src.presentation.view_model import build_claim_view

    spec = importlib.util.spec_from_file_location("_st_app_graph", APP)
    assert spec and spec.loader
    # Executing the module runs the page body too, which is harmless in bare
    # mode (Streamlit warns about a missing context and renders nothing).
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    view = build_claim_view(
        os.path.join(ROOT, "data", "generated", "e2_ontology", "run_1"),
        os.path.join(ROOT, "data", "fixtures", "claim_001"))

    for show_singletons, nodes, edges in ((False, 19, 36), (True, 40, 78)):
        dot = mod.graph_dot(view, show_singletons)
        assert dot.count("{") == dot.count("}"), "malformed DOT fails silently"
        assert dot.count("rank=same") == 3, "three columns, pinned"
        got_nodes = len(re.findall(r'^\s+"[^"]+" \[', dot, re.M))
        got_edges = dot.count(" -> ")
        assert (got_nodes, got_edges) == (nodes, edges), (
            "DOT graph has %d nodes / %d edges; the React layout has %d / %d"
            % (got_nodes, got_edges, nodes, edges))


def test_prune_removes_only_session_directories(tmp_path, monkeypatch):
    """Housekeeping must never touch the real claim's state.

    The local demo keeps its state in data/runtime/claim_001. A prune that
    matched too broadly would delete it between runs, and the loss would look
    like a mysterious reset rather than a bug.
    """
    import importlib.util
    import time

    spec = importlib.util.spec_from_file_location("_st_app_prune", APP)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    runtime = tmp_path / "runtime"
    old_session = runtime / "claim_001_sdeadbeef01"
    new_session = runtime / "claim_001_sfeedface02"
    real = runtime / "claim_001"
    other = runtime / "claim_002"
    for d in (old_session, new_session, real, other):
        d.mkdir(parents=True)
    stale = time.time() - 48 * 3600
    os.utime(old_session, (stale, stale))
    os.utime(real, (stale, stale))        # old, but must survive
    os.utime(other, (stale, stale))       # old, but must survive

    monkeypatch.setattr(mod.cs, "RUNTIME_DIR", str(runtime))
    removed = mod.prune_old_sessions(max_age_hours=6.0)

    assert removed == 1
    assert not old_session.exists(), "a stale session directory should go"
    assert new_session.exists(), "a fresh session must be left alone"
    assert real.exists(), "the real claim_001 state must never be pruned"
    assert other.exists(), "another claim's state must never be pruned"
