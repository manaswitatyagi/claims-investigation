import type { Assertion, Neighborhood } from "../types";
import { RelationshipBadge } from "./RelationshipBadge";

function Quote({ a }: { a: Assertion }) {
  const ev = a.evidence;
  if (ev.locator_kind === "TextSpan" && ev.passage_text && ev.char_start !== null && ev.char_end !== null) {
    return (
      <div className="quote-block">
        <span className="quote-context">…{ev.passage_text.slice(Math.max(0, ev.char_start - 90), ev.char_start)}</span>
        <mark>{ev.passage_text.slice(ev.char_start, ev.char_end)}</mark>
        <span className="quote-context">{ev.passage_text.slice(ev.char_end, ev.char_end + 90)}…</span>
      </div>
    );
  }
  return <div className="quote-block"><mark>{ev.quote}</mark></div>;
}

function EvidenceRows({ a }: { a: Assertion }) {
  const ev = a.evidence;
  return (
    <dl className="kv">
      <dt>Entity</dt><dd><code>{a.entity_id}</code></dd>
      <dt>Event</dt><dd><code>{a.event_id ?? "not event-scoped"}</code></dd>
      <dt>Predicate</dt><dd><code>{a.predicate}</code></dd>
      <dt>Value</dt><dd>{a.value ?? <em>not normalised</em>}</dd>
      <dt>Asserter</dt><dd>{a.asserter_name ?? a.asserter_kind.replace(/_/g, " ")}</dd>
      <dt>Source</dt><dd>{a.source_name} <code>{a.source_id}</code></dd>
      {ev.passage_id && (<><dt>Passage</dt><dd><code>{ev.passage_id}</code></dd></>)}
      {ev.char_start !== null && (
        <><dt>Offsets</dt><dd><code>[{ev.char_start}:{ev.char_end}]</code></dd></>
      )}
      {ev.field_path && (<><dt>Field</dt><dd><code>{ev.field_record}.{ev.field_path}</code></dd></>)}
      {ev.resolution_note && (<><dt>Located by</dt><dd><code>{ev.resolution_note}</code></dd></>)}
    </dl>
  );
}

export function EvidenceInspector({
  assertion, neighborhood, members, onClose,
}: {
  assertion: Assertion | null;
  neighborhood: Neighborhood | null;
  members: Assertion[];
  onClose: () => void;
}) {
  if (!assertion && !neighborhood) return null;

  return (
    <aside className="inspector" aria-label="Evidence inspector">
      <div className="insp-head">
        <h2>{neighborhood ? "Relationship evidence" : "Evidence"}</h2>
        <button className="close-btn" onClick={onClose} aria-label="Close inspector">✕</button>
      </div>

      <p className="verified-banner">
        <span className="verified-dot" aria-hidden="true" />
        <strong>Evidence verified</strong> — traced to exact source text and checked in code.
        This does not establish that the assertion is true.
      </p>

      {neighborhood && (
        <div className="insp-rel">
          <div className="insp-rel-top">
            <span className="insp-pred">{neighborhood.predicate_label}</span>
            <RelationshipBadge
              relationship={neighborhood.relationship}
              method={neighborhood.relationship_method}
              singleton={neighborhood.singleton}
            />
          </div>
          <p className="nb-rationale">{neighborhood.rationale}</p>
          <p className="compare-why">
            Compared because all of these assert <code>{neighborhood.predicate}</code> about{" "}
            <code>{neighborhood.entity_id}</code>
            {neighborhood.event_id ? <> at <code>{neighborhood.event_id}</code></> : null}.
          </p>
          <div className="compare-grid">
            {members.map((m) => (
              <div className="compare-col" key={m.assertion_id}>
                <div className="compare-head">
                  <span className="a-source">{m.source_name}</span>
                  <span className="a-value">{m.value ?? "—"}</span>
                </div>
                <p className="assertion-text">{m.text}</p>
                <Quote a={m} />
                <EvidenceRows a={m} />
              </div>
            ))}
          </div>
        </div>
      )}

      {assertion && !neighborhood && (
        <div className="insp-one">
          <p className="assertion-text">{assertion.text}</p>
          <Quote a={assertion} />
          <EvidenceRows a={assertion} />
        </div>
      )}
    </aside>
  );
}
