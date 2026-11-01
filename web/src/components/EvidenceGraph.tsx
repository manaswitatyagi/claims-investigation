import { useMemo, useState } from "react";
import type { EntityGroup, Neighborhood, Source } from "../types";
import { edgePath, layoutGraph, radius } from "../graph/layout";
import type { GraphNode } from "../graph/layout";

/** The claim as a tripartite graph: entity -> property -> source.
 *
 *  WHAT THIS SHOWS THAT THE CARD MAP DOES NOT. The cards answer "what is
 *  asserted about this entity." They cannot show fan-in — that one source is
 *  load-bearing across twenty properties while another touches two, or that a
 *  contradiction sits on a property only two sources address. That is a shape
 *  question, and shape is what a graph is for.
 *
 *  WHAT IT DELIBERATELY DOES NOT SHOW. Assertions are edge weight, not nodes.
 *  Putting all 46 on screen produces the hairball the card map was built to
 *  avoid, and the assertion-level view already exists in the inspector, where
 *  the quote and its span can actually be read.
 *
 *  Every relationship colour here is read from the DTO. Nothing on this screen
 *  decides whether two sources disagree.
 */
export function EvidenceGraph({
  entities, neighborhoods, sources, showSingletons,
  onSelectNeighborhood, changedNeighborhoodIds, sourceFilter, onSelectSource,
}: {
  entities: EntityGroup[];
  neighborhoods: Record<string, Neighborhood>;
  sources: Source[];
  showSingletons: boolean;
  onSelectNeighborhood: (id: string) => void;
  changedNeighborhoodIds: Set<string>;
  sourceFilter: string | null;
  onSelectSource: (id: string | null) => void;
}) {
  const [entityFilter, setEntityFilter] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);

  const graph = useMemo(
    () => layoutGraph(entities, neighborhoods, sources, { showSingletons, entityFilter }),
    [entities, neighborhoods, sources, showSingletons, entityFilter],
  );

  const byId = useMemo(() => {
    const m: Record<string, GraphNode> = {};
    graph.nodes.forEach((n) => { m[n.id] = n; });
    return m;
  }, [graph]);

  // Highlight follows hover, then the source filter already in app state, so the
  // graph and the card map stay in agreement about what is selected.
  const focus = hover ?? sourceFilter;
  const lit = useMemo(() => new Set(focus ? graph.incident[focus] ?? [] : []), [focus, graph]);

  const onNode = (n: GraphNode) => {
    if (n.kind === "property") onSelectNeighborhood(n.id);
    else if (n.kind === "entity") setEntityFilter(entityFilter === n.id ? null : n.id);
    else onSelectSource(sourceFilter === n.id ? null : n.id);
  };

  return (
    <section className="panel graph-panel" aria-labelledby="graph-h">
      <div className="panel-head">
        <h2 id="graph-h">Evidence graph</h2>
        {entityFilter && (
          <button className="link-btn" onClick={() => setEntityFilter(null)}>
            Show all entities
          </button>
        )}
      </div>
      <p className="panel-sub">
        Entity → property → source. Node size is a count of assertions; colour is the
        relationship the backend computed. Click a property to compare its evidence, an
        entity to isolate it, a source to filter. Layout is deterministic — the same
        claim always draws the same shape.
      </p>

      <div className="graph-scroll">
        <svg
          className="graph-svg"
          width={graph.width}
          height={graph.height}
          role="img"
          aria-label="Evidence graph: entities, properties and the sources asserting them"
        >
          <g className="graph-cols" aria-hidden="true">
            {(["entity", "property", "source"] as const).map((kind) => {
              const first = graph.nodes.find((n) => n.kind === kind);
              if (!first) return null;
              return (
                <text key={kind} className="graph-col-label" x={first.x} y={14}>
                  {kind === "property" ? "property asserted" : kind}
                </text>
              );
            })}
          </g>

          <g className="graph-edges">
            {graph.edges.map((e) => {
              const a = byId[e.from];
              const b = byId[e.to];
              if (!a || !b) return null;
              const on = lit.has(e.id);
              return (
                <path
                  key={e.id}
                  className={`gedge rel-${(e.relationship ?? "single").toLowerCase()}`
                    + (focus ? (on ? " is-lit" : " is-dim") : "")}
                  d={edgePath(a, b)}
                />
              );
            })}
          </g>

          <g className="graph-nodes">
            {graph.nodes.map((n) => {
              const dim = focus !== null && focus !== n.id
                && !(graph.incident[n.id] ?? []).some((id) => lit.has(id));
              return (
                <g
                  key={n.id}
                  className={`gnode gnode-${n.kind} rel-${(n.relationship ?? "single").toLowerCase()}`
                    + (dim ? " is-dim" : "")
                    + (changedNeighborhoodIds.has(n.id) ? " is-changed" : "")
                    + (sourceFilter === n.id || entityFilter === n.id ? " is-active" : "")}
                  transform={`translate(${n.x},${n.y})`}
                  data-orphan={n.orphan ? "true" : undefined}
                  onMouseEnter={() => setHover(n.id)}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => onNode(n)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(ev) => {
                    if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); onNode(n); }
                  }}
                >
                  <title>
                    {n.label}
                    {n.sublabel ? ` (${n.sublabel})` : ""}
                    {n.kind === "property"
                      ? ` — ${n.weight} assertion${n.weight === 1 ? "" : "s"}, `
                        + (n.singleton ? "single source" : (n.relationship ?? "not compared"))
                      : ""}
                    {n.kind === "source"
                      ? ` — ${n.weight} verified assertions`
                        + (n.orphan
                          ? ", none reaching a property shown here"
                          : "")
                      : ""}
                    {n.kind === "entity" ? ` — ${n.weight} properties` : ""}
                  </title>
                  <circle className="gnode-dot" r={radius(n.weight)} />
                  {n.flagged && <circle className="gnode-ring" r={radius(n.weight) + 3.5} />}
                  <text
                    className="gnode-label"
                    x={n.kind === "source" ? radius(n.weight) + 7 : -(radius(n.weight) + 7)}
                    y={n.orphan ? 0 : 4}
                    textAnchor={n.kind === "source" ? "start" : "end"}
                  >
                    {n.label.length > 34 ? `${n.label.slice(0, 33)}…` : n.label}
                  </text>
                  {n.orphan && (
                    <text
                      className="gnode-orphan"
                      x={radius(n.weight) + 7}
                      y={12}
                      textAnchor="start"
                    >
                      {/* Two different facts, and conflating them would be a
                          false accusation against the document: zero verified
                          assertions is a grounding outcome, whereas a positive
                          count with no edge here is just the current filter. */}
                      {n.weight === 0
                        ? "no assertion survived grounding"
                        : "none about the entities shown"}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      <p className="graph-foot">
        A ring marks an entity with a contradiction, a contradictory property, or a source
        that had assertions dropped. Uncited assertions never reach this graph — they are
        dropped upstream, so absence here is not agreement.
      </p>
    </section>
  );
}
