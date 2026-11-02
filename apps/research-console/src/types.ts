export interface ResearchRecord {
  id: string;
  project_id: string;
  logical_id: string;
  version: number;
  kind: string;
  label: string;
  payload: Record<string, any>;
  actor: string;
  created: number;
  content_hash: string;
  history?: ResearchRecord[];
  incoming?: Edge[];
  outgoing?: Edge[];
}
export interface Edge {
  id: string;
  source_id: string;
  target_id: string;
  relation: string;
  assessment: string;
  rationale: string;
  actor: string;
}
export interface Result {
  id: string;
  case_id: string;
  repeat: number;
  family: string;
  prediction: {
    answer: string | null;
    evidence_ids: string[];
    confidence: number | null;
  };
  scores: {
    correct: boolean;
    error: string | null;
    pairs: Record<string, [number, number]>;
  };
  latency_ms: number;
  output_id: string;
  claim_id: string;
}
export interface Metric {
  value: number | null;
  numerator?: number;
  denominator?: number;
  n?: number;
  definition?: string;
  reason?: string;
  unit?: string;
}
export interface Run {
  id: string;
  project_id: string;
  execution_id: string;
  benchmark_id: string;
  config_id: string;
  target: string;
  split: string;
  scope: string;
  status: string;
  created: number;
  completed: number | null;
  semantic_digest: string;
  error: string | null;
  request: { repeats: number; parent_run_id?: string };
  results: Result[];
  summary: {
    unique_cases: number;
    executions: number;
    metrics: Record<string, Metric>;
    groups: Record<string, { accuracy: number; cases: number }>;
    uncertainty: { reason: string };
    resources: {
      rss_before_bytes: number;
      rss_after_bytes: number;
      wall_seconds: number;
      scope: string;
    };
  };
}
export interface Correction extends ResearchRecord {
  review_status: "accepted" | "rejected" | "pending" | "disputed";
  reviews: ResearchRecord[];
  basis: string;
}
export interface Comparison {
  before_id: string;
  after_id: string;
  paired_cases: number;
  before_accuracy: number;
  after_accuracy: number;
  accuracy_delta: number;
  improved: number;
  regressed: number;
  unchanged: number;
  regression_detected: boolean;
  partial_overlap: boolean;
  method: string;
  pairs: { case_id: string; before: number; after: number; delta: number }[];
}
export interface Graph {
  nodes: ResearchRecord[];
  edges: Edge[];
  truncated: boolean;
}
export interface Case {
  id: string;
  family: string;
  split: string;
  question: string;
  input: {
    query_key: string;
    evidence: {
      id: string;
      key: string;
      value: string;
      revision: number;
      trusted: boolean;
      source: string;
    }[];
  };
  expected_answer: string | null;
  expected_evidence_ids: string[];
}
export interface Benchmark {
  record: ResearchRecord;
  benchmark: { name: string; seed: number; synthetic: true; cases: Case[] };
}
export interface SavedLayout {
  id: string;
  name: string;
  configuration: {
    view: "overview" | "evaluations" | "evidence" | "datasets" | "reviews";
    inspector_width: number;
    run_id: string | null;
    family: string;
  };
}
