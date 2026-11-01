import { useRef, useState } from "react";
import { STATIC_MODE } from "../api";
import type { IngestionSession } from "../useClaimStream";
import { RelationshipBadge } from "./RelationshipBadge";

const ACCEPT = ".md,.txt";

export function AddEvidence({
  claimId, session, connected, onBegin, onFocusNeighborhood, onReset,
}: {
  claimId: string;
  session: IngestionSession;
  connected: boolean;
  onBegin: (name: string) => void;
  onFocusNeighborhood: (id: string) => void;
  onReset: () => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function upload(file: File) {
    setError(null);
    onBegin(file.name);
    const res = await fetch(`/api/claim/${claimId}/documents`, {
      method: "POST",
      headers: { "X-Filename": file.name, "Content-Type": "text/plain" },
      body: await file.text(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      setError(body.error ?? "upload failed");
    }
  }

  const busy = session.status === "uploading" || session.status === "processing";

  // On a static host there is no extraction pipeline to run. Saying so is the
  // only honest option: a mocked ingestion that invented plausible assertions
  // without locating a single quote would be a demonstration of nothing, on a
  // page whose entire claim is that every assertion is traced to a span.
  if (STATIC_MODE) {
    return (
      <section className="panel add-evidence" aria-labelledby="add-h">
        <div className="panel-head">
          <h2 id="add-h">Add evidence</h2>
          <span className="live-dot">read-only</span>
        </div>
        <p className="panel-sub">
          Disabled on the hosted demo. Ingesting a document runs the real extraction
          and quote-location pipeline, which needs the Python backend — and mocking it
          would mean showing assertions whose spans were never resolved.
        </p>
        <p className="static-note">
          Everything else is live against the same data contract the server returns.
          To add a document, clone the repo and run the server locally.
        </p>
      </section>
    );
  }

  return (
    <section className="panel add-evidence" aria-labelledby="add-h">
      <div className="panel-head">
        <h2 id="add-h">Add evidence</h2>
        <span className={`live-dot${connected ? " is-live" : ""}`}>
          {connected ? "live" : "offline"}
        </span>
      </div>

      <div
        className={`dropzone${dragging ? " is-dragging" : ""}${busy ? " is-busy" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault(); setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f && !busy) upload(f);
        }}
      >
        <p className="dz-main">Drop a <code>.md</code> or <code>.txt</code> document</p>
        <button className="dz-btn" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "Processing…" : "Choose file"}
        </button>
        <input
          ref={input} type="file" accept={ACCEPT} hidden
          onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ""; }}
        />
        <p className="dz-note">
          Runs the same pipeline as the existing sources. Assertions whose evidence
          cannot be located are dropped, not admitted.
        </p>
      </div>

      {error && <p className="err">{error}</p>}

      {session.status !== "idle" && (
        <div className="progress">
          <div className="progress-head">
            <span className="prog-name">{session.documentName}</span>
            <span className={`prog-status prog-${session.status}`}>
              {session.status === "processing" ? "Processing…" : session.status}
            </span>
          </div>

          {session.status === "failed" && (
            <p className="err">Processing failed during extraction. {session.error}</p>
          )}

          <ul className="prog-list">
            <li><b>{session.extracted}</b> assertions extracted</li>
            <li className={session.verified ? "ok" : ""}>
              <b>{session.verified}</b> evidence spans verified
            </li>
            {session.dropped > 0 && (
              <li className="warn">
                <b>{session.dropped}</b> dropped because evidence could not be resolved
              </li>
            )}
            <li><b>{session.mapped}</b> mapped to claim properties</li>
            {session.unresolved > 0 && (
              <li className="warn"><b>{session.unresolved}</b> verified but unresolved</li>
            )}
          </ul>

          {session.relationshipChanges.length > 0 && (
            <div className="changes">
              <h3>Relationship changed</h3>
              {session.relationshipChanges.map((c) => (
                <button
                  key={c.neighborhood_id}
                  className="change-row"
                  onClick={() => onFocusNeighborhood(c.neighborhood_id)}
                >
                  <span className="change-pred">⚠ {c.predicate_label}</span>
                  <span className="change-arrow">
                    <RelationshipBadge relationship={c.from} singleton={!c.from} compact />
                    <span aria-hidden="true">→</span>
                    <RelationshipBadge relationship={c.to} compact />
                  </span>
                </button>
              ))}
              <p className="changes-note">
                Describes the relationship among assertions only. It does not mean any
                source is right or wrong.
              </p>
            </div>
          )}

          {session.status === "complete" && (
            <button className="link-btn reset-btn" onClick={async () => {
              await fetch(`/api/claim/${claimId}/reset`, { method: "POST" });
              onReset(); window.location.reload();
            }}>
              Reset demo to baseline
            </button>
          )}
        </div>
      )}
    </section>
  );
}
