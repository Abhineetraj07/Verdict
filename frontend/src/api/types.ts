export interface JudgeConfig {
  name: string;
  dimension: string;
  rubric: string;
  scoring_scale: number;
  weight: number;
}

export interface AggregationConfig {
  method: string;
  pass_threshold?: number;
  critical_dimensions?: string[];
  critical_threshold?: number;
}

export interface EvalSuiteCreate {
  name: string;
  description?: string;
  judges: JudgeConfig[];
  aggregation?: AggregationConfig;
}

export interface EvalSuiteResponse {
  id: string;
  name: string;
  description: string;
  judges: JudgeConfig[];
  aggregation: AggregationConfig;
  created_at: string;
}

export interface DatasetEntry {
  input: string;
  output: string;
  expected_output?: string;
}

export interface DatasetCreate {
  name: string;
  entries: DatasetEntry[];
}

export interface DatasetResponse {
  id: string;
  name: string;
  entry_count: number;
  created_at: string;
}

export interface JudgeScore {
  judge_name: string;
  dimension: string;
  score: number;
  reasoning: string;
}

export interface EntryResult {
  entry_index: number;
  input: string;
  output: string;
  judge_scores: JudgeScore[];
  aggregated_score: number;
}

export interface RunStats {
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  q25: number;
  q75: number;
}

export interface DimensionBreakdown {
  dimension: string;
  mean_score: number;
  min_score: number;
  max_score: number;
}

export interface EvalRunResponse {
  id: string;
  suite_id: string;
  dataset_id: string;
  status: string;
  overall_score: number | null;
  entry_results: EntryResult[] | null;
  stats: RunStats | null;
  dimension_breakdown: DimensionBreakdown[] | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface EvalRunSummary {
  id: string;
  suite_name: string;
  dataset_name: string;
  status: string;
  overall_score: number | null;
  created_at: string;
}

export interface CompareResponse {
  runs: EvalRunResponse[];
  score_deltas: number[] | null;
}
