import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from fastapi import HTTPException

from app.api.dependencies.auth import require_admin, require_manager
from app.api.v1.admin.coach_command_center import (
    get_conversation_messages_with_diagnostics,
    sanitize_turn_diagnostics_for_coach,
)
from app.api.v1.admin.dashboard import assign_coach_to_user, get_users, AssignCoachRequest
from app.api.v1.manager.observability import (
    get_observability_summary,
    list_recent_traces,
)
from app.core.telemetry import (
    TraceContext,
    calculate_model_cost,
    MODEL_PRICING,
)
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User


class ManagerObservabilityAndRBACTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.coachee_user = User(
            id=10,
            email="coachee@example.com",
            full_name="Alex Coachee",
            role="user",
            is_active=True,
            assigned_coach_id=1,
            created_at=datetime.now(timezone.utc),
        )
        self.admin_coach = User(
            id=1,
            email="coach@example.com",
            full_name="Jess Coach",
            role="admin",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        self.manager_user = User(
            id=2,
            email="manager@example.com",
            full_name="Morgan Manager",
            role="manager",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

    # -------------------------------------------------------------------------
    # 1. Deterministic Token & USD Cost Calculations
    # -------------------------------------------------------------------------
    def test_calculate_model_cost_deterministic_pricing(self):
        # gpt-4o: $2.50 / 1M in, $10.00 / 1M out
        cost_4o = calculate_model_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
        # (1000 / 1M * 2.50) + (500 / 1M * 10.00) = 0.0025 + 0.0050 = 0.0075
        self.assertEqual(cost_4o, 0.0075)

        # gpt-4o-mini: $0.15 / 1M in, $0.60 / 1M out
        cost_mini = calculate_model_cost("gpt-4o-mini", prompt_tokens=10000, completion_tokens=2000)
        # (10000 / 1M * 0.15) + (2000 / 1M * 0.60) = 0.0015 + 0.0012 = 0.0027
        self.assertEqual(cost_mini, 0.0027)

        # text-embedding-3-small: $0.02 / 1M in
        cost_embed = calculate_model_cost("text-embedding-3-small", prompt_tokens=50000, completion_tokens=0)
        # 50000 / 1M * 0.02 = 0.001
        self.assertEqual(cost_embed, 0.001)

        # whisper-1: $0.006 / min => 120 seconds = 2 min = $0.012
        cost_whisper = calculate_model_cost("whisper-1", audio_seconds=120.0)
        self.assertEqual(cost_whisper, 0.012)

    def test_trace_context_records_usage_and_serializes_to_diagnostics(self):
        trace = TraceContext(trace_id="test-trace-id-123")
        usage = trace.record_usage(
            model_name="gpt-4o",
            prompt_tokens=2000,
            completion_tokens=400,
        )

        self.assertEqual(usage["model_name"], "gpt-4o")
        self.assertEqual(usage["total_tokens"], 2400)
        self.assertAlmostEqual(usage["cost_usd"], 0.009, places=6)

        diag = trace.to_diagnostics_dict()
        self.assertIn("usage", diag)
        self.assertEqual(diag["usage"]["cost_usd"], 0.009)
        self.assertEqual(diag["trace_id"], "test-trace-id-123")

    # -------------------------------------------------------------------------
    # 2. RBAC Access Control Boundaries
    # -------------------------------------------------------------------------
    async def test_require_manager_enforces_strict_manager_role(self):
        # Manager passes
        manager_res = await require_manager(current_user=self.manager_user)
        self.assertEqual(manager_res.id, self.manager_user.id)

        # Admin fails with 403
        with self.assertRaises(HTTPException) as ctx_admin:
            await require_manager(current_user=self.admin_coach)
        self.assertEqual(ctx_admin.exception.status_code, 403)
        self.assertIn("Manager access required", ctx_admin.exception.detail)

        # User fails with 403
        with self.assertRaises(HTTPException) as ctx_user:
            await require_manager(current_user=self.coachee_user)
        self.assertEqual(ctx_user.exception.status_code, 403)

    async def test_require_admin_allows_both_admin_and_manager(self):
        # Admin passes
        admin_res = await require_admin(current_user=self.admin_coach)
        self.assertEqual(admin_res.id, self.admin_coach.id)

        # Manager passes (super-set access)
        manager_res = await require_admin(current_user=self.manager_user)
        self.assertEqual(manager_res.id, self.manager_user.id)

        # Regular user fails with 403
        with self.assertRaises(HTTPException) as ctx_user:
            await require_admin(current_user=self.coachee_user)
        self.assertEqual(ctx_user.exception.status_code, 403)

    # -------------------------------------------------------------------------
    # 3. Coach vs. Manager Chat History Sanitization
    # -------------------------------------------------------------------------
    def test_sanitize_turn_diagnostics_strips_telemetry_for_coach(self):
        raw_diagnostics = {
            "socratic_stage": "Reality",
            "progress_assessment": "Client realized delegation gap",
            "support_assessment": "Reflective question provided",
            "action_context": "Direct report 1:1 meeting",
            "rag_sources": [{"title": "ICF_Core_Competencies.pdf", "similarity": 0.88}],
            "guardrails": {"is_safe": True},
            "telemetry": {
                "trace_id": "abc123",
                "ttft_ms": 320.5,
                "total_turn_latency_ms": 1150.0,
                "usage": {
                    "model_name": "gpt-4o",
                    "prompt_tokens": 1500,
                    "completion_tokens": 300,
                    "total_tokens": 1800,
                    "cost_usd": 0.00675,
                },
                "spans": [{"name": "span.ttft", "duration_ms": 320.5}],
            },
        }

        sanitized = sanitize_turn_diagnostics_for_coach(raw_diagnostics)

        # Engineering telemetry, tokens, and USD costs MUST be stripped from Coach view
        self.assertNotIn("telemetry", sanitized)
        self.assertNotIn("usage", sanitized)
        self.assertNotIn("cost_usd", sanitized)
        self.assertNotIn("prompt_tokens", sanitized)
        self.assertNotIn("ttft_ms", sanitized)

        # Socratic coaching insights MUST be preserved
        self.assertEqual(sanitized["socratic_stage"], "Reality")
        self.assertEqual(sanitized["progress_assessment"], "Client realized delegation gap")
        self.assertEqual(len(sanitized["rag_sources"]), 1)

    async def test_get_conversation_messages_sanitizes_for_admin_but_unfiltered_for_manager(self):
        conv_id = uuid.uuid4()
        conv = Conversation(id=conv_id, user_id=self.coachee_user.id, title="Test")
        raw_diag = {
            "socratic_stage": "Goal",
            "rag_sources": [],
            "telemetry": {
                "usage": {
                    "model_name": "gpt-4o",
                    "tokens": 500,
                    "cost_usd": 0.0035,
                },
                "ttft_ms": 250.0,
            },
        }
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conv_id,
            role="assistant",
            content="What outcome would make this session successful?",
            created_at=datetime.now(timezone.utc),
            doc_metadata={},
            turn_diagnostics=raw_diag,
        )

        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=conv)),  # conv query
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[msg])))),  # msg query
        ]

        # 1. Admin Request -> Telemetry stripped
        admin_response = await get_conversation_messages_with_diagnostics(
            conversation_id=str(conv_id),
            current_admin=self.admin_coach,
            db=mock_db,
        )
        self.assertEqual(len(admin_response), 1)
        self.assertNotIn("telemetry", admin_response[0].turn_diagnostics)
        self.assertEqual(admin_response[0].turn_diagnostics["socratic_stage"], "Goal")

        # 2. Manager Request -> Full unfiltered telemetry preserved
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=conv)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[msg])))),
        ]
        manager_response = await get_conversation_messages_with_diagnostics(
            conversation_id=str(conv_id),
            current_admin=self.manager_user,
            db=mock_db,
        )
        self.assertEqual(len(manager_response), 1)
        self.assertIn("telemetry", manager_response[0].turn_diagnostics)
        self.assertEqual(
            manager_response[0].turn_diagnostics["telemetry"]["usage"]["cost_usd"],
            0.0035,
        )

    # -------------------------------------------------------------------------
    # 4. Manager Observability Endpoints
    # -------------------------------------------------------------------------
    async def test_manager_observability_summary_endpoint(self):
        conv_id = uuid.uuid4()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conv_id,
            role="assistant",
            created_at=datetime.now(timezone.utc),
            turn_diagnostics={
                "telemetry": {
                    "ttft_ms": 220.0,
                    "usage": {
                        "model_name": "gpt-4o",
                        "prompt_tokens": 1000,
                        "completion_tokens": 200,
                        "total_tokens": 1200,
                        "cost_usd": 0.0045,
                    },
                    "spans": [
                        {"name": "span.context_retrieval", "duration_ms": 85.0},
                    ],
                }
            },
        )

        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            # msg rows
            MagicMock(all=MagicMock(return_value=[(msg, 10, "coachee@example.com", "Alex Coachee")])),
            # pending outbox
            MagicMock(scalar=MagicMock(return_value=0)),
            # published outbox
            MagicMock(scalar=MagicMock(return_value=5)),
            # failed outbox
            MagicMock(scalar=MagicMock(return_value=0)),
            # processed events
            MagicMock(scalar=MagicMock(return_value=5)),
        ]

        summary = await get_observability_summary(
            _manager=self.manager_user,
            db=mock_db,
        )

        self.assertEqual(summary.total_turns, 1)
        self.assertEqual(summary.total_tokens, 1200)
        self.assertAlmostEqual(summary.total_cost_usd, 0.0045, places=4)
        self.assertEqual(summary.p50_ttft_ms, 220.0)
        self.assertEqual(summary.p95_context_retrieval_ms, 85.0)
        self.assertEqual(summary.outbox_health.published, 5)
        self.assertEqual(len(summary.models), 1)
        self.assertEqual(summary.models[0].model_name, "gpt-4o")
        self.assertEqual(len(summary.per_user_cost), 1)
        self.assertEqual(summary.per_user_cost[0].user_id, 10)

    # -------------------------------------------------------------------------
    # 5. Coach Client Assignment Endpoint
    # -------------------------------------------------------------------------
    async def test_assign_coach_to_user_endpoint(self):
        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=self.coachee_user)),  # target user
            MagicMock(scalar_one_or_none=MagicMock(return_value=self.admin_coach)),    # target coach
            MagicMock(one_or_none=MagicMock(return_value=(self.coachee_user, None, 1, 0))),  # row
        ]

        res = await assign_coach_to_user(
            user_id=10,
            body=AssignCoachRequest(coach_id=1),
            _admin=self.admin_coach,
            db=mock_db,
        )

        self.assertEqual(self.coachee_user.assigned_coach_id, 1)
        self.assertEqual(res.assigned_coach_id, 1)


if __name__ == "__main__":
    unittest.main()
