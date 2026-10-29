export type FindingCategory = 'SECURITY' | 'PERFORMANCE' | 'STYLE' | 'SYNTAX' | 'ERROR';

export type FindingSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type ReviewScope = 'ALL' | 'SECURITY' | 'PERFORMANCE' | 'STYLE';

export type GateStatus = 'PASS' | 'FAIL' | 'INCOMPLETE' | 'ERROR';

export type DetectionSource =
  | 'AST'
  | 'DETERMINISTIC_RULE'
  | 'SECURITY_AGENT'
  | 'PERFORMANCE_AGENT'
  | 'STYLE_AGENT'
  | 'LLM';

export interface Finding {
  id: string;
  rule_id: string;
  category: FindingCategory;
  severity: FindingSeverity;
  title: string;
  explanation: string;
  remediation: string;
  file_path?: string | null;
  line_number?: number | null;
  end_line_number?: number | null;
  source: DetectionSource;
  confidence: number;
  snippet?: string | null;
}

export interface QualityGateRuleConfig {
  block_on_critical: boolean;
  block_on_high: boolean;
  max_medium_allowed: number;
  max_low_allowed: number;
}

export interface QualityGateResult {
  status: GateStatus;
  summary: string;
  blocking_findings: Finding[];
  severity_counts: Record<string, number>;
  category_counts: Record<string, number>;
  explanation: string;
  ai_review_ran: boolean;
  semantic_retrieval_ran: boolean;
  disclaimer: string;
}

export interface ReviewRequest {
  code: string;
  file_path?: string;
  scope?: ReviewScope;
  enable_llm?: boolean;
  quality_gate_config?: QualityGateRuleConfig;
}

export interface ReviewResponse {
  review_id: string;
  timestamp: string;
  file_path?: string | null;
  scope: ReviewScope;
  findings: Finding[];
  quality_gate: QualityGateResult;
  execution_metadata: Record<string, any>;
}

export interface ReviewSummary {
  review_id: string;
  timestamp: string;
  file_path?: string | null;
  scope: ReviewScope;
  status: GateStatus;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface MetricsSummary {
  total_reviews: number;
  passed_gates: number;
  failed_gates: number;
  incomplete_gates: number;
  error_gates: number;
  severity_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  mode: string;
  components: {
    ast_engine: { status: string; rules: string };
    llm_provider: {
      provider: string;
      is_configured: boolean;
      model: string;
      base_url: string;
      api_key_masked: string;
      timeout_seconds: number;
      status_message: string;
    };
    vector_store: {
      is_connected: boolean;
      storage_mode: string;
      collection_name: string;
      total_chunks: number;
      dimension: number;
      embedding_provider: string;
    };
    database: {
      status: string;
      type: string;
      total_records: number;
    };
    github_integration: {
      dry_run_mode: boolean;
      webhook_secret_configured: boolean;
      github_token_configured: boolean;
    };
  };
}

export interface CodeChunkResult {
  chunk_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  content: string;
  score: number;
  language: string;
}

export interface IndexStatusResponse {
  status: string;
  indexed_files: number;
  total_chunks: number;
  collection_name: string;
  storage_mode: string;
  directory: string;
  message: string;
}

export interface CodeSearchResponse {
  query: string;
  results: CodeChunkResult[];
  total_results: number;
  storage_mode: string;
}

export interface GitHubWebhookComment {
  path: string;
  line: number;
  body: string;
}

export interface GitHubPRReviewEventResponse {
  event: string;
  action: string;
  repository: string;
  pr_number: number;
  dry_run: boolean;
  analyzed_files: string[];
  total_findings: number;
  gate_status: string;
  comments_generated: GitHubWebhookComment[];
  published: boolean;
  message: string;
}
