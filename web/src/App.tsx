import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchClaimView } from "./api";
import type { ClaimView, Neighborhood } from "./types";
import { AddEvidence } from "./components/AddEvidence";
import { EvidenceMap } from "./components/EvidenceMap";
import { EvidenceInspector } from "./components/EvidenceInspector";
import { SourcesPanel } from "./components/SourcesPanel";
import { TimelinePanel } from "./components/TimelinePanel";
import { useClaimStream } from "./useClaimStream";

export default function App() {
  const [view, setView] = useState<ClaimView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [selectedAssertion, setSelectedAssertion] = useState<string | null>(null);
  const [selectedNeighborhood, setSelectedNeighborhood] = useState<string | null>(null);
  const [showSingletons, setShowSingletons] = useState(false);
  const [focusNeighborhood, setFocusNeighborhood] = useState<string | null>(null);

  const reload = useCallback(() => {
    fetchClaimView("claim_001").then(setView).catch((e) => setError(String(e)));
  }, []);
  useEffect(() => { reload(); }, [reload]);

  // The stream tells us WHEN state changed; the view endpoint remains the single
  // source of claim state, so the screen can never drift from the server.
  const { session, connected, reset, beginUpload } = useClaimStream("claim_001", reload);

  const nbById = useMemo(() => {
    const m: Record<string, Neighborhood> = {};
    view?.neighborhoods.forEach((n) => { m[n.neighborhood_id] = n; });
    return m;
  }, [view]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    if (view) Object.values(view.assertions).forEach((a) => {
      c[a.source_id] = (c[a.source_id] ?? 0) + 1;
    });
    return c;
  }, [view]);

  const tally = useMemo(() => {
    const t = { CORROBORATING: 0, COMPATIBLE: 0, CONTRADICTORY: 0, single: 0 };
    view?.neighborhoods.forEach((n) => {
      if (n.singleton || !n.relationship) t.single += 1;
      else t[n.relationship] += 1;
    });
    return t;
  }, [view]);

  if (error) return <div className="fatal">Could not load the claim view: {error}</div>;
  if (!view) return <div className="loading">Loading claim…</div>;

  const nb = selectedNeighborhood ? nbById[selectedNeighborhood] : null;
  const members = nb ? nb.assertion_ids.map((id) => view.assertions[id]).filter(Boolean) : [];
  const assertion = selectedAssertion ? view.assertions[selectedAssertion] ?? null : null;

  const closeInspector = () => { setSelectedAssertion(null); setSelectedNeighborhood(null); };

  return (
    <div className={`app${assertion || nb ? " has-inspector" : ""}`}>
      <header className="topbar">
        <div className="topbar-main">
          <h1>{view.claim.claim_number ?? view.claim.claim_id}</h1>
          <span className="crumb">{view.claim.loss_date}</span>
          <span className="crumb">{view.claim.loss_location}</span>
          <span className="chip">checkpoint {view.claim.checkpoint}</span>
          <span className="chip">{view.claim.status?.replace(/_/g, " ")}</span>
        </div>
        <div className="tally" role="group" aria-label="Relationship summary">
          <span className="tally-item rel-contradictory"><b>{tally.CONTRADICTORY}</b> contradictory</span>
          <span className="tally-item rel-compatible"><b>{tally.COMPATIBLE}</b> compatible</span>
          <span className="tally-item rel-corroborating"><b>{tally.CORROBORATING}</b> corroborating</span>
          <span className="tally-item rel-single"><b>{tally.single}</b> single source</span>
        </div>
      </header>

      <p className="disclaimer">
        <strong>Verified means traced, not true.</strong> {view.claim.verified_means}
      </p>

      <div className="layout">
        <div className="col-left">
          <AddEvidence
            claimId="claim_001"
            session={session}
            connected={connected}
            onBegin={beginUpload}
            onFocusNeighborhood={(id) => { setFocusNeighborhood(id); setSelectedNeighborhood(id); }}
            onReset={reset}
          />
          <SourcesPanel
            sources={view.sources}
            selected={sourceFilter}
            onSelect={setSourceFilter}
            assertionCountsBySource={counts}
            sessionId={session.sessionId}
          />
          <section className="panel small">
            <div className="panel-head"><h2>Not assessed</h2></div>
            <ul className="plain-list">
              {view.not_assessed.map((n, i) => <li key={i}>{n}</li>)}
            </ul>
          </section>
          <section className="panel small">
            <div className="panel-head"><h2>Ungrouped ({view.ungrouped.length})</h2></div>
            <p className="panel-sub">
              No entity or property in this claim's vocabulary. Reported rather than forced
              into a bucket.
            </p>
            <ul className="plain-list">
              {view.ungrouped.slice(0, 6).map((u) => (
                <li key={u.assertion_id}><span className="mono">{u.reason}</span> — {u.text}</li>
              ))}
            </ul>
          </section>
        </div>

        <div className="col-main">
          <div className="map-controls">
            <label className="toggle">
              <input
                type="checkbox"
                checked={showSingletons}
                onChange={(e) => setShowSingletons(e.target.checked)}
              />
              Show single-source properties ({tally.single})
            </label>
          </div>
          <EvidenceMap
            entities={view.entities}
            neighborhoods={nbById}
            assertions={view.assertions}
            sourceFilter={sourceFilter}
            selectedAssertion={selectedAssertion}
            onSelectAssertion={(id) => { setSelectedAssertion(id); setSelectedNeighborhood(null); }}
            onSelectNeighborhood={(id) => { setSelectedNeighborhood(id); setSelectedAssertion(null); }}
            showSingletons={showSingletons}
            newAssertionIds={session.newAssertionIds}
            changedNeighborhoodIds={new Set(session.relationshipChanges.map((c) => c.neighborhood_id))}
            focusNeighborhood={focusNeighborhood}
          />
          <TimelinePanel occurred={view.timeline.occurred} becameKnown={view.timeline.became_known} />
        </div>
      </div>

      <EvidenceInspector
        assertion={assertion}
        neighborhood={nb}
        members={members}
        onClose={closeInspector}
      />

      <footer className="footer">
        <span>{view.view_version}</span>
        <span>model {view.claim.model_id}</span>
        <span>prompts {view.claim.prompt_version}</span>
        <span className="footer-disc">{view.claim.provenance_disclaimer}</span>
      </footer>
    </div>
  );
}
