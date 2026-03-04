export interface ProviderInfo {
  name: string;
  id: string;
  configured: boolean;
  model: string | null;
  web_search_supported: boolean;
  web_search_default: boolean;
  deep_research_supported: boolean;
  deep_research_default: boolean;
}

export interface SearchResult {
  title: string;
  link: string;
  snippet: string;
}

export interface AnalysisData {
  timestamp?: string;
  query?: string;
  provider?: string;
  companies_mentioned: string[];
  mention_reasons: Record<string, string>;
  authority_signals: string[];
  key_features: string[];
  sources_cited: string[];
  ranking_factors: string | string[];
  sentiment: string;
  optimization_insights: string | string[];
  extracted_urls?: string[];
  url_statistics?: Record<string, unknown>;
  domain_statistics?: Record<string, unknown>;
  domain_classifications?: Array<{ domain: string; type: string }>;
  negative_signals?: Record<string, unknown>;
  negative_score?: number;
  entity_sentiment?: Record<string, unknown>;
  competitor_mentions?: Array<{ name: string; context?: string }>;
  accuracy_issues?: string[];
  corrections_needed?: string[];
}

export interface ProviderResult {
  provider: string;
  response?: string | SearchResult[];
  model?: string;
  success: boolean;
  error?: string;
  analysis?: AnalysisData;
  response_time?: number;
  response_length?: number;
  web_search?: boolean;
  deep_research?: boolean;
  thinking?: string;
  streaming?: boolean;
  streamingThinking?: boolean;
  statusMessage?: string;
}

export interface QueryResultData {
  query: string;
  timestamp: string;
  date: string;
  time: string;
  results: ProviderResult[];
}

export interface ResultListItem {
  filename: string;
  query: string;
  timestamp: string | null;
  is_batch: boolean;
  provider_count: number;
  has_analysis: boolean;
}

export interface SSEEvent {
  event: string;
  data: {
    provider?: string;
    result?: ProviderResult;
    analysis?: AnalysisData;
    error?: string;
    query_id?: string;
    filename?: string;
    attempt?: number;
    text?: string;
    message?: string;
    conversation_id?: string;
  };
}

export interface ProviderHealth {
  provider: string;
  status: "ok" | "error" | "not_configured";
  latency?: number;
  error?: string;
}

export interface Claim {
  claim: string;
  category: string;
  providers: Record<string, "agrees" | "disagrees" | "not_mentioned" | "partially">;
  details: Record<string, string>;
}

export interface ProviderRanking {
  completeness: number;
  accuracy_signals: number;
  sourcing: number;
  unique_value: string;
}

export interface ComparisonResult {
  summary: string;
  claims: Claim[];
  provider_rankings: Record<string, ProviderRanking>;
  generated_at: string;
  model_used: string;
}

export interface SavedSearch {
  id: string;
  query: string;
  result_filename: string;
  tags: string[];
  pinned: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}
