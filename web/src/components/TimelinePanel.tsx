import type { TimelineEvent } from "../types";

function Axis({ title, note, events }: { title: string; note: string; events: TimelineEvent[] }) {
  return (
    <div className="axis">
      <h3>{title}</h3>
      <p className="axis-note">{note}</p>
      {events.length === 0 && <p className="empty">No events on this axis.</p>}
      <ol className="axis-list">
        {events.map((e) => (
          <li key={e.event_id} className={e.ordering_confidence === "unorderable" ? "is-vague" : ""}>
            <span className="axis-when">
              {e.when ?? e.raw_expression ?? "—"}
            </span>
            <span className="axis-label">{e.label}</span>
            {e.ordering_confidence === "unorderable" && (
              <span className="axis-flag" title="The source expression is vague. No timestamp was invented.">
                not orderable
              </span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

export function TimelinePanel({ occurred, becameKnown }: {
  occurred: TimelineEvent[]; becameKnown: TimelineEvent[];
}) {
  return (
    <section className="panel timeline" aria-labelledby="timeline-h">
      <div className="panel-head"><h2 id="timeline-h">Timeline</h2></div>
      <p className="panel-sub">
        Built in code from normalised dates. No model orders these events, and a vague
        expression is carried without being given a position.
      </p>
      <div className="axes">
        <Axis title="Occurred" note="When things happened." events={occurred} />
        <Axis title="Became known" note="When the file learned them." events={becameKnown} />
      </div>
    </section>
  );
}
