import type { Relationship, RelationshipMethod } from "../types";

/** Relationship state is never signalled by colour alone: each carries a glyph
 *  and a word. Colour is reinforcement, not the channel. */
const SPEC: Record<string, { glyph: string; label: string; cls: string }> = {
  CORROBORATING: { glyph: "=", label: "Corroborating", cls: "rel-corroborating" },
  COMPATIBLE: { glyph: "≈", label: "Compatible", cls: "rel-compatible" },
  CONTRADICTORY: { glyph: "≠", label: "Contradictory", cls: "rel-contradictory" },
  SINGLE: { glyph: "·", label: "Single source", cls: "rel-single" },
};

export function RelationshipBadge({
  relationship, method, singleton, compact = false,
}: {
  relationship: Relationship;
  method?: RelationshipMethod;
  singleton?: boolean;
  compact?: boolean;
}) {
  const spec = SPEC[singleton || !relationship ? "SINGLE" : relationship];
  return (
    <span className={`badge ${spec.cls}`}>
      <span className="badge-glyph" aria-hidden="true">{spec.glyph}</span>
      <span>{spec.label}</span>
      {!compact && method === "deterministic" && (
        <span className="badge-method" title="Values matched by lookup table; no model call">
          computed
        </span>
      )}
      {!compact && method === "llm" && (
        <span className="badge-method" title="Compared by a language model within this neighbourhood">
          compared
        </span>
      )}
    </span>
  );
}
