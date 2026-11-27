import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("app.telemetry")

MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {
        "input_per_million": 2.50,
        "output_per_million": 10.00,
    },
    "gpt-4o-mini": {
        "input_per_million": 0.15,
        "output_per_million": 0.60,
    },
    "text-embedding-3-small": {
        "input_per_million": 0.02,
        "output_per_million": 0.00,
    },
    "whisper-1": {
        "per_minute": 0.006,
        "input_per_million": 0.0,
        "output_per_million": 0.0,
    },
}

DEFAULT_MODEL_PRICING: Dict[str, float] = {
    "input_per_million": 2.50,
    "output_per_million": 10.00,
}


def calculate_model_cost(
    model_name: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    audio_seconds: float = 0.0,
) -> float:
    """Calculates deterministic USD cost rounded to 6 decimal places."""
    norm_name = (model_name or "gpt-4o").lower().strip()
    pricing = MODEL_PRICING.get(norm_name, DEFAULT_MODEL_PRICING)
    input_rate = pricing.get("input_per_million", DEFAULT_MODEL_PRICING["input_per_million"])
    output_rate = pricing.get("output_per_million", DEFAULT_MODEL_PRICING["output_per_million"])
    per_minute_rate = pricing.get("per_minute", 0.0)

    input_cost = (prompt_tokens / 1_000_000.0) * input_rate
    output_cost = (completion_tokens / 1_000_000.0) * output_rate
    audio_cost = (audio_seconds / 60.0) * per_minute_rate

    return round(input_cost + output_cost + audio_cost, 6)


class Span(BaseModel):
    name: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    start_time_iso: str
    end_time_iso: Optional[str] = None
    duration_ms: float = 0.0
    status: str = "OK"  # "OK" or "ERROR"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class TraceContext:
    def __init__(
        self,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        service_name: str = "leadership-coach-engine",
    ):
        self.trace_id = trace_id or uuid.uuid4().hex
        self.parent_span_id = parent_span_id
        self.service_name = service_name
        self.root_span_id = uuid.uuid4().hex[:16]
        self.spans: List[Span] = []
        self.start_monotonic = time.monotonic()
        self.ttft_recorded = False
        self.ttft_ms: Optional[float] = None
        self.usage: Optional[Dict[str, Any]] = None

    def create_traceparent(self) -> str:
        """Returns standard W3C TraceContext traceparent string: 00-{trace_id}-{span_id}-01"""
        return f"00-{self.trace_id}-{self.root_span_id}-01"

    @asynccontextmanager
    async def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        span_id = uuid.uuid4().hex[:16]
        start_time_iso = datetime.now(timezone.utc).isoformat()
        start_mono = time.monotonic()

        current_span = Span(
            name=name,
            trace_id=self.trace_id,
            span_id=span_id,
            parent_span_id=self.parent_span_id or self.root_span_id,
            start_time_iso=start_time_iso,
            attributes=attributes or {},
        )

        try:
            yield current_span
        except Exception as exc:
            current_span.status = "ERROR"
            current_span.error_message = str(exc)
            raise
        finally:
            end_mono = time.monotonic()
            current_span.end_time_iso = datetime.now(timezone.utc).isoformat()
            current_span.duration_ms = round((end_mono - start_mono) * 1000, 2)
            self.spans.append(current_span)
            logger.debug(
                "Telemetry Span: %s (duration: %.2f ms, status: %s)",
                name,
                current_span.duration_ms,
                current_span.status,
            )

    def record_context_retrieval(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        latency_ms: float,
    ) -> Span:
        span_id = uuid.uuid4().hex[:16]
        scores = [d.get("similarity", d.get("score", 0.0)) for d in retrieved_docs]
        scopes = [d.get("scope", "global_playbook") for d in retrieved_docs]

        span = Span(
            name="span.context_retrieval",
            trace_id=self.trace_id,
            span_id=span_id,
            parent_span_id=self.root_span_id,
            start_time_iso=datetime.now(timezone.utc).isoformat(),
            end_time_iso=datetime.now(timezone.utc).isoformat(),
            duration_ms=round(latency_ms, 2),
            attributes={
                "query_length": len(query),
                "docs_retrieved": len(retrieved_docs),
                "max_similarity_score": max(scores) if scores else 0.0,
                "avg_similarity_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
                "scopes": list(set(scopes)),
            },
        )
        self.spans.append(span)
        return span

    def record_socratic_guard(
        self,
        user_message: str,
        seeks_direct_solution: bool,
        socratic_stage: str,
        latency_ms: float,
    ) -> Span:
        span_id = uuid.uuid4().hex[:16]
        span = Span(
            name="span.socratic_guard",
            trace_id=self.trace_id,
            span_id=span_id,
            parent_span_id=self.root_span_id,
            start_time_iso=datetime.now(timezone.utc).isoformat(),
            end_time_iso=datetime.now(timezone.utc).isoformat(),
            duration_ms=round(latency_ms, 2),
            attributes={
                "message_length": len(user_message),
                "seeks_direct_solution": seeks_direct_solution,
                "detected_grow_stage": socratic_stage,
            },
        )
        self.spans.append(span)
        return span

    def record_ttft(self) -> Optional[float]:
        """Records Time-To-First-Token if not already captured."""
        if not self.ttft_recorded:
            self.ttft_recorded = True
            self.ttft_ms = round((time.monotonic() - self.start_monotonic) * 1000, 2)
            span_id = uuid.uuid4().hex[:16]
            span = Span(
                name="span.ttft",
                trace_id=self.trace_id,
                span_id=span_id,
                parent_span_id=self.root_span_id,
                start_time_iso=datetime.now(timezone.utc).isoformat(),
                end_time_iso=datetime.now(timezone.utc).isoformat(),
                duration_ms=self.ttft_ms,
                attributes={"ttft_ms": self.ttft_ms},
            )
            self.spans.append(span)
            return self.ttft_ms
        return self.ttft_ms

    def record_generation_stream(
        self,
        duration_ms: float,
        tokens_generated: int,
    ) -> Span:
        tokens_per_second = (
            round((tokens_generated / (duration_ms / 1000.0)), 2)
            if duration_ms > 0
            else 0.0
        )
        span_id = uuid.uuid4().hex[:16]
        span = Span(
            name="span.generation_stream",
            trace_id=self.trace_id,
            span_id=span_id,
            parent_span_id=self.root_span_id,
            start_time_iso=datetime.now(timezone.utc).isoformat(),
            end_time_iso=datetime.now(timezone.utc).isoformat(),
            duration_ms=round(duration_ms, 2),
            attributes={
                "tokens_generated": tokens_generated,
                "tokens_per_second": tokens_per_second,
            },
        )
        self.spans.append(span)
        return span

    def record_usage(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        audio_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculates deterministic USD cost and records model token consumption."""
        cost_usd = calculate_model_cost(
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            audio_seconds=audio_seconds,
        )
        total_tokens = prompt_tokens + completion_tokens
        self.usage = {
            "model_name": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
        }
        return self.usage

    def to_diagnostics_dict(self) -> Dict[str, Any]:
        """Compiles trace telemetry into a dictionary for turn_diagnostics."""
        total_duration_ms = round((time.monotonic() - self.start_monotonic) * 1000, 2)
        stream_span = next(
            (s for s in self.spans if s.name == "span.generation_stream"), None
        )

        return {
            "trace_id": self.trace_id,
            "traceparent": self.create_traceparent(),
            "total_turn_latency_ms": total_duration_ms,
            "ttft_ms": self.ttft_ms,
            "tokens_per_second": stream_span.attributes.get("tokens_per_second")
            if stream_span
            else None,
            "usage": self.usage,
            "spans": [s.model_dump() for s in self.spans],
        }

