import { useEffect, useRef, useState } from "react";
import type { Assertion, EntityGroup, Neighborhood } from "../types";
import { RelationshipBadge } from "./RelationshipBadge";

/** The primary experience. Organised by entity -> property, never a force-directed
 *  hairball: the claim already has a controlled structure, so the screen shows it. */
export function EvidenceMap({
  entities, neighborhoods, assertions, sourceFilter,
  selectedAssertion, onSelectAssertion, onSelectNeighborhood, showSingletons,
  newAssertionIds, changedNeighborhoodIds, focusNeighborhood,
}: {
  entities: EntityGroup[];
  neighborhoods: Record<string, Neighborhood>;
  assertions: Record<string, Assertion>;
  sourceFilter: string | null;
  selectedAssertion: string | null;
  onSelectAssertion: (id: string) => void;
  onSelectNeighborhood: (id: string) => void;
  showSingletons: boolean;
  newAssertionIds: Set<string>;
  changedNeighborhoodIds: Set<string>;
  focusNeighborhood: string | null;
}) {
  return (
    <section className="panel map" aria-labelledby="map-h">
      <div className="panel-head"><h2 id="map-h">Evidence map</h2></div>
      <p className="panel-sub">
        Assertions grouped by entity, event, and property. Sources appear side by side so
        you can see who is talking about the same thing — and whether they agree.
      </p>
      {entities.map((entity) => {
        const nbs = entity.neighborhood_ids
          .map((id) => neighborhoods[id])
          .filter((n) => showSingletons || !n.singleton)
          .filter((n) => !sourceFilter || n.source_ids.includes(sourceFilter));
        if (nbs.length === 0) return null;
        return (
          <div className="entity" key={entity.entity_id}>
            <div className="entity-head">
              <h3>{entity.label}</h3>
              <span className="entity-type">{entity.type}</span>
              {entity.contradiction_count > 0 && (
                <span className="entity-flag">
                  {entity.contradiction_count} contradictory
                </span>
              )}
            </div>
            <div className="nb-grid">
              {nbs.map((n) => (
                <NeighborhoodCard
                  key={n.neighborhood_id}
                  nb={n}
                  assertions={assertions}
                  sourceFilter={sourceFilter}
                  selectedAssertion={selectedAssertion}
                  onSelectAssertion={onSelectAssertion}
                  onSelectNeighborhood={onSelectNeighborhood}
                  newAssertionIds={newAssertionIds}
                  changed={changedNeighborhoodIds.has(n.neighborhood_id)}
                  focused={focusNeighborhood === n.neighborhood_id}
                />
              ))}
            </div>
          </div>
        );
      })}
    </section>
  );
}

function NeighborhoodCard({
  nb, assertions, sourceFilter, selectedAssertion,
  onSelectAssertion, onSelectNeighborhood, newAssertionIds, changed, focused,
}: {
  nb: Neighborhood;
  assertions: Record<string, Assertion>;
  sourceFilter: string | null;
  selectedAssertion: string | null;
  onSelectAssertion: (id: string) => void;
  onSelectNeighborhood: (id: string) => void;
  newAssertionIds: Set<string>;
  changed: boolean;
  focused: boolean;
}) {
  const [open, setOpen] = useState(nb.relationship === "CONTRADICTORY");
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    if (changed) setOpen(true);
  }, [changed]);
  useEffect(() => {
    if (focused && ref.current) {
      setOpen(true);
      ref.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [focused]);
  const rows = nb.assertion_ids.map((id) => assertions[id]).filter(Boolean);

  return (
    <article
      ref={ref}
      className={`nb nb-${(nb.relationship ?? "single").toLowerCase()}`
        + (changed ? " is-changed" : "") + (focused ? " is-focused" : "")}
    >
      {changed && (
        <div className="nb-changed-flag">⚠ relationship changed this session</div>
      )}
      <button className="nb-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="nb-caret" aria-hidden="true">{open ? "▾" : "▸"}</span>
        <span className="nb-title">{nb.predicate_label}</span>
        <RelationshipBadge
          relationship={nb.relationship}
          method={nb.relationship_method}
          singleton={nb.singleton}
        />
      </button>

      {open && (
        <div className="nb-body">
          <ul className="assertion-list">
            {rows.map((a) => {
              const dimmed = sourceFilter !== null && a.source_id !== sourceFilter;
              const active = selectedAssertion === a.assertion_id;
              return (
                <li key={a.assertion_id}>
                  <button
                    className={`assertion${dimmed ? " is-dimmed" : ""}${active ? " is-active" : ""}`
                      + (newAssertionIds.has(a.assertion_id) ? " is-new" : "")}
                    onClick={() => onSelectAssertion(a.assertion_id)}
                  >
                    <span className="a-source">
                      {newAssertionIds.has(a.assertion_id) && (
                        <span className="new-dot" title="Added in this session">+</span>
                      )}
                      {a.source_name}
                    </span>
                    <span className="a-arrow" aria-hidden="true">→</span>
                    <span className="a-value">{a.value ?? <em>see assertion</em>}</span>
                    <span className="a-asserter">{a.asserter_kind.replace(/_/g, " ")}</span>
                  </button>
                </li>
              );
            })}
          </ul>
          {!nb.singleton && (
            <div className="nb-foot">
              <p className="nb-rationale">{nb.rationale}</p>
              <button className="link-btn" onClick={() => onSelectNeighborhood(nb.neighborhood_id)}>
                Compare evidence side by side
              </button>
            </div>
          )}
          {nb.singleton && (
            <p className="nb-rationale nb-single-note">
              Only one source addresses this. Silence from other sources is not a
              relationship.
            </p>
          )}
        </div>
      )}
    </article>
  );
}
