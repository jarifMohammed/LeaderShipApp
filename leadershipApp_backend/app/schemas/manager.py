from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OutboxHealth(BaseModel):
    pending: int = 0
    published: int = 0
    failed: int = 0
    processed_events: int = 0


class UserCostBreakdown(BaseModel):
    user_id: int
    user_email: str
    user_name: str
    turn_count: int
    total_tokens: int
    total_cost_usd: float


class ModelUsageBreakdown(BaseModel):
    model_name: str
    turn_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost_usd: float


class ManagerObservabilitySummaryResponse(BaseModel):
    total_cost_usd: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_turns: int
    avg_cost_per_turn_usd: float
    p50_ttft_ms: float
    p95_ttft_ms: float
    p95_context_retrieval_ms: float
    outbox_health: OutboxHealth
    models: List[ModelUsageBreakdown] = Field(default_factory=list)
    per_user_cost: List[UserCostBreakdown] = Field(default_factory=list)


class ManagerTraceItem(BaseModel):
    message_id: str
    conversation_id: str
    user_id: int
    user_email: Optional[str] = None
    created_at: Optional[datetime] = None
    trace_id: Optional[str] = None
    traceparent: Optional[str] = None
    model_name: Optional[str] = None
    tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    ttft_ms: Optional[float] = None
    total_turn_latency_ms: Optional[float] = None
    spans: List[Dict[str, Any]] = Field(default_factory=list)
    turn_diagnostics: Optional[Dict[str, Any]] = None


class ManagerTracesResponse(BaseModel):
    total_count: int
    items: List[ManagerTraceItem]

