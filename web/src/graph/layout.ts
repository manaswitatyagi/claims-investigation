/** Deterministic tripartite layout for the evidence graph.
 *
 *  WHY NOT FORCE-DIRECTED. `EvidenceMap` already records the reason: the claim
 *  has a controlled structure, so the screen shows it rather than discovering it.
 *  A physics simulation would place the same claim differently on every render,
 *  which makes two readings of one claim non-comparable and encodes nothing —
 *  proximity in a force layout is an artefact of initial conditions. Here, x is
 *  the node's kind and y is its position in the DTO's own order. Same input,
 *  same picture, every time.
 *
 *  WHAT THIS LAYER MAY NOT DO. It positions nodes and nothing else. Relationship
 *  state is read from the DTO and never computed — no value comparison lives
 *  here or in the renderer (tests/test_runtime_ingest.py:248 enforces this by
 *  scanning the source). Layout decides where a contradiction appears, never
 *  whether one exists.
 *
 *  E2 CONTEXT. This is a *view* over the DTO, not a graph layer underneath it.
 *  `entities[].neighborhood_ids` and `neighborhoods[].source_ids` are already an
 *  adjacency list, so the edges below are read, not stored. No node registry, no
 *  edge objects with their own lifecycle — those are what E2 recommended against
 *  (docs/experiments/E2.md), and nothing here reverses that.
 */
import type { EntityGroup, Neighborhood, Source } from "../types";

export const COL_X = { entity: 0, property: 1, source: 2 } as const;
export type NodeKind = keyof typeof COL_X;

export interface GraphNode {
  id: string;
  kind: NodeKind;
  label: string;
  sublabel: string | null;
  x: number;
  y: number;
  /** Read from the DTO for property nodes; null for entities and sources. */
  relationship: Neighborhood["relationship"];
  singleton: boolean;
  /** Drives node radius. A count, never a judgement. */
  weight: number;
  flagged: boolean;
  /** A source with no edge in the current view. It is still drawn: a document
   *  that contributed nothing is a fact about the claim, not an empty slot to
   *  omit. Silently dropping it would hide a grounding failure. */
  orphan: boolean;
}

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  /** Inherited from the property node the edge touches, for colour only. */
  relationship: Neighborhood["relationship"];
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width: number;
  height: number;
  /** Adjacency for highlight-on-select. Derived from edges, not stored state. */
  incident: Record<string, string[]>;
}

const ROW = 34;
const PAD_Y = 26;
const COL_W = 300;
const PAD_X = 130;

/** Column order is fixed and meaningful: what the claim is about, what is
 *  asserted about it, who asserted it. Reading left to right is the sentence. */
export function layoutGraph(
  entities: EntityGroup[],
  neighborhoods: Record<string, Neighborhood>,
  sources: Source[],
  opts: { showSingletons: boolean; entityFilter: string | null },
): Graph {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  const visibleEntities = entities.filter(
    (e) => !opts.entityFilter || e.entity_id === opts.entityFilter,
  );

  // Property nodes are emitted grouped by entity, in entity order. That single
  // choice is what keeps the edge bundles readable without any crossing-
  // minimisation pass: an entity's properties are always vertically contiguous.
  let propRow = 0;
  const propRowOf: Record<string, number> = {};
  const entityRowOf: Record<string, number> = {};

  visibleEntities.forEach((entity) => {
    const own = entity.neighborhood_ids
      .map((id) => neighborhoods[id])
      .filter(Boolean)
      .filter((n) => opts.showSingletons || !n.singleton);
    if (own.length === 0) return;

    // Centre the entity against its own block of properties, so the fan reads
    // as one-to-many rather than as an arbitrary diagonal.
    const first = propRow;
    own.forEach((n) => {
      propRowOf[n.neighborhood_id] = propRow;
      propRow += 1;
    });
    entityRowOf[entity.entity_id] = first + (own.length - 1) / 2;

    nodes.push({
      id: entity.entity_id,
      kind: "entity",
      label: entity.label,
      sublabel: entity.type,
      x: PAD_X + COL_X.entity * COL_W,
      y: PAD_Y + entityRowOf[entity.entity_id] * ROW,
      relationship: null,
      singleton: false,
      weight: own.length,
      flagged: entity.contradiction_count > 0,
      orphan: false,
    });

    own.forEach((n) => {
      nodes.push({
        id: n.neighborhood_id,
        kind: "property",
        label: n.predicate_label,
        sublabel: null,
        x: PAD_X + COL_X.property * COL_W,
        y: PAD_Y + propRowOf[n.neighborhood_id] * ROW,
        relationship: n.relationship,
        singleton: n.singleton,
        weight: n.assertion_ids.length,
        flagged: n.relationship === "CONTRADICTORY",
        orphan: false,
      });
      edges.push({
        id: `${entity.entity_id}~${n.neighborhood_id}`,
        from: entity.entity_id,
        to: n.neighborhood_id,
        relationship: n.relationship,
      });
    });
  });

  // EVERY source gets a node, including one that reached no visible property.
  // The first version of this filtered those out, and a document ingested with
  // zero surviving assertions silently vanished from a screen about provenance
  // while the sources panel still listed it. A source contributing nothing is
  // a grounding result worth seeing, so it is drawn and marked, never dropped.
  const propCount = Math.max(propRow, 1);
  const reached = new Set<string>();
  Object.keys(propRowOf).forEach((nbId) => {
    neighborhoods[nbId]?.source_ids.forEach((sid) => reached.add(sid));
  });

  // Spread over the property column's full height so the fan-in is visible;
  // stacking four sources at the top would make every edge near-horizontal.
  sources.forEach((s, i) => {
    const slot = sources.length === 1
      ? (propCount - 1) / 2
      : (i * (propCount - 1)) / (sources.length - 1);
    nodes.push({
      id: s.source_id,
      kind: "source",
      label: s.name,
      sublabel: s.type.replace(/_/g, " "),
      x: PAD_X + COL_X.source * COL_W,
      y: PAD_Y + slot * ROW,
      relationship: null,
      singleton: false,
      weight: s.verified_assertion_count,
      flagged: (s.dropped_assertion_count ?? 0) > 0,
      orphan: !reached.has(s.source_id),
    });
  });

  Object.keys(propRowOf).forEach((nbId) => {
    const n = neighborhoods[nbId];
    if (!n) return;
    n.source_ids.forEach((sid) => {
      edges.push({
        id: `${nbId}~${sid}`,
        from: nbId,
        to: sid,
        relationship: n.relationship,
      });
    });
  });

  const incident: Record<string, string[]> = {};
  edges.forEach((e) => {
    (incident[e.from] ??= []).push(e.id);
    (incident[e.to] ??= []).push(e.id);
  });

  return {
    nodes,
    edges,
    width: PAD_X * 2 + COL_X.source * COL_W,
    height: PAD_Y * 2 + propCount * ROW,
    incident,
  };
}

/** Horizontal cubic bezier. Control points sit at the midpoint so curves leave
 *  and enter their nodes horizontally, which keeps a dense bundle legible. */
export function edgePath(a: GraphNode, b: GraphNode): string {
  const mx = (a.x + b.x) / 2;
  return `M ${a.x} ${a.y} C ${mx} ${a.y}, ${mx} ${b.y}, ${b.x} ${b.y}`;
}

/** Radius from a count, clamped. Area would be more honest for comparing
 *  magnitudes, but these counts span one order of magnitude and legibility at
 *  small sizes matters more than proportionality here. */
export function radius(weight: number): number {
  return Math.min(11, 4 + Math.sqrt(Math.max(weight, 0)) * 1.6);
}
