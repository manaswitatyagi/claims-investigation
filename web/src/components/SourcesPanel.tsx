import type { Source } from "../types";

const STATUS_LABEL: Record<string, string> = {
  uploaded: "Uploaded", processing: "Processing…", processed: "Evidence verified",
  processed_with_dropped_assertions: "Verified, some dropped",
  failed: "Failed", verified: "Evidence verified",
};

export function SourcesPanel({
  sources, selected, onSelect, assertionCountsBySource, sessionId,
}: {
  sources: Source[];
  selected: string | null;
  onSelect: (id: string | null) => void;
  assertionCountsBySource: Record<string, number>;
  sessionId: string | null;
}) {
  return (
    <section className="panel sources" aria-labelledby="sources-h">
      <div className="panel-head">
        <h2 id="sources-h">Sources</h2>
        {selected && (
          <button className="link-btn" onClick={() => onSelect(null)}>clear filter</button>
        )}
      </div>
      <p className="panel-sub">
        Select a source to highlight the assertions it contributed.
      </p>
      <ul className="source-list">
        {sources.map((s) => {
          const active = selected === s.source_id;
          return (
            <li key={s.source_id}>
              <button
                className={`source-card${active ? " is-active" : ""}`}
                aria-pressed={active}
                onClick={() => onSelect(active ? null : s.source_id)}
              >
                <div className="source-top">
                  <span className="source-name">{s.name}</span>
                  <span className="count-chip">
                    {assertionCountsBySource[s.source_id] ?? s.verified_assertion_count}
                  </span>
                </div>
                <div className="source-meta">
                  <span className="tag">{s.type.replace(/_/g, " ")}</span>
                  <span
                    className={`status-dot status-${s.verification_status}`}
                    aria-hidden="true"
                  />
                  <span className={`source-status st-${s.verification_status}`}>
                    {STATUS_LABEL[s.verification_status] ?? s.verification_status}
                  </span>
                  {s.added_in_session === sessionId && sessionId && (
                    <span className="new-chip">new</span>
                  )}
                </div>
                {!!s.dropped_assertion_count && (
                  <div className="source-dropped">
                    {s.dropped_assertion_count} assertion
                    {s.dropped_assertion_count === 1 ? "" : "s"} dropped — evidence
                    could not be resolved
                  </div>
                )}
                {s.error && <div className="source-dropped">{s.error}</div>}
                <div className="source-processing">{s.processing}</div>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
