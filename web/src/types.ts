/** Mirrors the `claim-view/1` DTO. The UI knows nothing about Fact, Difference,
 *  or the evaluation layer — only this contract. */

export type Relationship = "CORROBORATING" | "COMPATIBLE" | "CONTRADICTORY" | null;
export type RelationshipMethod = "deterministic" | "llm" | "not_compared" | "llm_invalid";

export interface Evidence {
  quote: string | null;
  /** Traced to exact source text and checked in code. NOT a claim about truth. */
  verified: boolean;
  resolution_note: string | null;
  document_id: string | null;
  document_version: string | null;
  locator_kind: string | null;
  passage_id: string | null;
  char_start: number | null;
  char_end: number | null;
  passage_label: string | null;
  passage_text: string | null;
  field_record: string | null;
  field_path: string | null;
}

export interface Assertion {
  assertion_id: string;
  entity_id: string;
  event_id: string | null;
  predicate: string;
  predicate_label: string;
  value: string | null;
  value_normalised: unknown;
  text: string;
  asserter_kind: string;
  asserter_name: string | null;
  provenance: "deterministic" | "extracted";
  source_id: string;
  source_name: string;
  added_in_session?: string;
  evidence: Evidence;
}

export interface Neighborhood {
  neighborhood_id: string;
  entity_id: string;
  event_id: string | null;
  predicate: string;
  predicate_label: string;
  relationship: Relationship;
  relationship_method: RelationshipMethod;
  rationale: string;
  singleton: boolean;
  assertion_ids: string[];
  source_ids: string[];
  distinct_value_count: number;
}

export interface EntityGroup {
  entity_id: string;
  label: string;
  type: string;
  neighborhood_ids: string[];
  contradiction_count: number;
}

export type SourceStatus =
  | "uploaded" | "processing" | "processed"
  | "processed_with_dropped_assertions" | "failed" | "verified";

export interface Source {
  source_id: string;
  name: string;
  type: string;
  verified_assertion_count: number;
  dropped_assertion_count?: number;
  processing: string;
  verification_status: SourceStatus;
  passage_ids: string[];
  added_in_session?: string;
  error?: string;
}

export interface TimelineEvent {
  event_id: string;
  label: string;
  when: string | null;
  precision: string | null;
  raw_expression: string | null;
  ordering_confidence: "exact" | "approximate" | "unorderable";
  source_assertion_ids: string[];
}

export interface ClaimHeader {
  claim_id: string;
  claim_number: string | null;
  checkpoint: string | null;
  status: string | null;
  loss_date: string | null;
  loss_location: string | null;
  generated_at: string | null;
  model_id: string | null;
  prompt_version: string | null;
  provenance_disclaimer: string;
  verified_means: string;
}

/** Server-sent processing events. Structured product state only — never model
 *  reasoning, never a truth or materiality judgement. */
export type ProcessingEventType =
  | "document_received" | "passages_created" | "extraction_started"
  | "assertion_extracted" | "citation_verified" | "assertion_dropped"
  | "assertion_normalized" | "neighborhood_updated" | "relationship_changed"
  | "processing_complete" | "processing_failed";

export interface ProcessingEvent {
  type: ProcessingEventType;
  session_id: string;
  at: string;
  payload: Record<string, any>;
}

export interface RelationshipDelta {
  neighborhood_id: string;
  predicate: string;
  predicate_label: string;
  from: Relationship;
  to: Relationship;
  rationale: string;
}

export interface ClaimView {
  view_version: string;
  claim: ClaimHeader;
  sources: Source[];
  entities: EntityGroup[];
  neighborhoods: Neighborhood[];
  assertions: Record<string, Assertion>;
  timeline: { occurred: TimelineEvent[]; became_known: TimelineEvent[] };
  ungrouped: { assertion_id: string; text: string; provenance: string; reason: string }[];
  not_assessed: string[];
  seeded_from?: string;
}
