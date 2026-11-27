export interface OutboxHealth {
  pending: number;
  published: number;
  failed: number;
  processed_events: number;
}

export interface UserCostBreakdown {
  user_id: number;
  user_email: string;
  user_name: string;
  turn_count: number;
  total_tokens: number;
  total_cost_usd: number;
}

export interface ModelUsageBreakdown {
  model_name: string;
  turn_count: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
}

export interface ManagerObservabilitySummary {
  total_cost_usd: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_turns: number;
  avg_cost_per_turn_usd: number;
  p50_ttft_ms: number;
  p95_ttft_ms: number;
  p95_context_retrieval_ms: number;
  outbox_health: OutboxHealth;
  models: ModelUsageBreakdown[];
  per_user_cost: UserCostBreakdown[];
}

export interface ManagerTraceItem {
  message_id: string;
  conversation_id: string;
  user_id: number;
  user_email?: string | null;
  created_at?: string | null;
  trace_id?: string | null;
  traceparent?: string | null;
  model_name?: string | null;
  tokens?: number | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  cost_usd?: number | null;
  ttft_ms?: number | null;
  total_turn_latency_ms?: number | null;
  spans: Array<{
    name: string;
    duration_ms: number;
    status: string;
    attributes?: Record<string, unknown>;
  }>;
  turn_diagnostics?: Record<string, unknown> | null;
}

export interface ManagerTracesResponse {
  total_count: number;
  items: ManagerTraceItem[];
}

