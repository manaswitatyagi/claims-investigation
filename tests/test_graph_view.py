"""The evidence graph is a VIEW, not a layer.

E2 recommended against building a graph layer (docs/experiments/E2.md): the
neighbourhood arm cost 8-9 model calls against 1 for identical difference
recall, and nothing needed traversal. The graph screen added afterwards renders
the adjacency the DTO already carries. These tests exist so that distinction
cannot erode quietly — the cheapest way to end up with the layer E2 rejected is
for layout state to drift backwards across the DTO boundary one field at a time.

The reversal would look like: x/y positions computed server-side, edge objects
with their own ids and lifecycle, or a node registry in Python. Each is checked
below. None of this constrains ever building the layer deliberately; it
constrains building it by accident.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web", "src")
GRAPH_DIR = os.path.join(WEB, "graph")


def _ts_sources():
    out = {}
    for base, _dirs, files in os.walk(WEB):
        for f in files:
            if f.endswith((".ts", ".tsx")):
                path = os.path.join(base, f)
                out[os.path.relpath(path, WEB)] = open(path, encoding="utf-8").read()
    return out


def test_layout_lives_only_in_the_frontend():
    """No Python module computes graph geometry.

    Positions are a property of a screen size and a reading order, not of a
    claim. A claim's DTO that carried coordinates would be a layout engine
    pretending to be a data contract.
    """
    assert os.path.isdir(GRAPH_DIR), "expected the layout to live in web/src/graph"
    assert not os.path.isdir(os.path.join(ROOT, "src", "graph")), (
        "a Python src/graph/ package is the graph layer E2 recommended against")


def test_the_dto_carries_no_geometry_and_no_edge_objects():
    """The contract the UI consumes is unchanged by the existence of a graph.

    Checked against the real serialised view rather than the schema, because the
    failure mode is a field added to the builder and never to the schema.
    """
    view_path = os.path.join(ROOT, "data", "generated", "claim_001_view.json")
    if not os.path.isfile(view_path):
        import pytest
        pytest.skip("claim_001_view.json not generated")
    view = json.load(open(view_path, encoding="utf-8"))

    geometry = ("x", "y", "cx", "cy", "position", "layout", "width", "height",
                "nodes", "edges", "node_id", "edge_id", "adjacency")
    found = []

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in geometry:
                    found.append("%s.%s" % (path, k))
                walk(v, "%s.%s" % (path, k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:4]):
                walk(v, "%s[%d]" % (path, i))

    walk(view, "view")
    assert found == [], (
        "the DTO grew graph/geometry fields, which moves layout or edge identity "
        "server-side: %s" % found)


def test_edges_are_read_from_existing_adjacency():
    """The two edge sets come from fields that already existed for the cards.

    If a future change introduces an edge list of its own, this test should fail
    and the change should be argued for on its merits.
    """
    layout = open(os.path.join(GRAPH_DIR, "layout.ts"), encoding="utf-8").read()
    assert "entity.neighborhood_ids" in layout
    assert "n.source_ids" in layout or "source_ids.includes" in layout


def test_layout_is_deterministic():
    """Same claim, same picture.

    A force simulation places a claim differently on every render, so two
    readings of one claim are not comparable and proximity means nothing. It
    would also break the premise that this screen shows the claim's controlled
    structure rather than discovering a structure of its own.
    """
    banned = ("Math.random", "d3-force", "forceSimulation", "forceManyBody",
              "requestAnimationFrame", "Date.now()", "performance.now")
    for name, src in _ts_sources().items():
        if not name.startswith("graph" + os.sep) and "EvidenceGraph" not in name:
            continue
        for pattern in banned:
            assert pattern not in src, (
                "%r in %s makes the layout non-deterministic" % (pattern, name))


def test_graph_asserts_no_relationship_of_its_own():
    """Colour on this screen is the backend's verdict, carried not recomputed.

    `test_react_never_derives_a_relationship` covers the whole frontend; this
    narrows to the graph, where the temptation is strongest because an edge is
    exactly where one would be tempted to compute agreement.
    """
    for name in ("graph/layout.ts", "components/EvidenceGraph.tsx"):
        src = open(os.path.join(WEB, name), encoding="utf-8").read()
        for pattern in (".value ===", ".value !==", "value_normalised",
                        "computeRelationship", "agree(", "disagree("):
            assert pattern not in src, "%r in %s derives a relationship" % (pattern, name)
        # It must read the DTO's verdict — otherwise it is colouring by guess.
        assert "relationship" in src


def test_singletons_are_not_silently_shown_as_agreement():
    """A property with one source has no relationship, and the graph says so.

    This is the same rule the cards enforce in prose. On a graph it matters more:
    a node with one edge reads as settled unless the absence is labelled.
    """
    graph = open(os.path.join(WEB, "components", "EvidenceGraph.tsx"),
                 encoding="utf-8").read()
    assert "showSingletons" in graph, "singletons must be filterable, as in the cards"
    assert "single source" in graph, "a one-source property must be named as such"
    assert "absence here is not agreement" in graph, (
        "dropped assertions never reach the graph; the screen must say so")


def test_every_source_is_drawn_even_when_it_contributed_nothing():
    """A source that reached no property must still appear.

    This is a regression test for a real bug in the first version: sources were
    filtered to those reaching a visible property, so a document ingested with
    zero surviving assertions disappeared from the graph while the sources panel
    still listed it. On a screen about provenance, that hid a grounding failure
    — the most important thing a source node can report is that nothing from it
    survived.
    """
    layout = open(os.path.join(GRAPH_DIR, "layout.ts"), encoding="utf-8").read()
    assert "orphan" in layout, "the no-edge case must be modelled, not filtered away"
    assert "sources.filter(" not in layout, (
        "filtering the source list is the bug: a source with no edge must be "
        "drawn and marked, not omitted")
    assert "sources.forEach(" in layout, "every source gets a node"


def test_an_orphan_source_is_not_accused_of_failing_grounding():
    """Two different facts must read differently.

    Zero verified assertions is a grounding outcome. A positive count with no
    edge in the current view is just the active filter. Showing the first
    message for the second case would be a false statement about the document.
    """
    graph = open(os.path.join(WEB, "components", "EvidenceGraph.tsx"),
                 encoding="utf-8").read()
    assert "no assertion survived grounding" in graph
    assert "none about the entities shown" in graph
    assert "n.weight === 0" in graph, "the two cases must be distinguished by count"
