import asyncio
import re
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.telemetry import Span, TraceContext
from app.workflows.chat_workflow import ChatWorkflow, WorkflowNodes, ChatState


class TestSpanTelemetry(unittest.TestCase):
    def setUp(self):
        self.trace = TraceContext(trace_id="a1b2c3d4e5f60718293a4b5c6d7e8f90")

    def test_trace_initialization_and_traceparent(self):
        """Verify standard W3C TraceContext traceparent generation: 00-{trace_id}-{span_id}-01"""
        traceparent = self.trace.create_traceparent()
        self.assertTrue(
            re.match(r"^00-[0-9a-f]{32}-[0-9a-f]{16}-01$", traceparent),
            f"Traceparent '{traceparent}' does not match standard W3C regex format",
        )
        self.assertEqual(self.trace.trace_id, "a1b2c3d4e5f60718293a4b5c6d7e8f90")

    def test_record_context_retrieval(self):
        """Verify span.context_retrieval captures latency, query length, doc counts, and scores."""
        retrieved_docs = [
            {"filename": "playbook.pdf", "scope": "global_playbook", "similarity": 0.82},
            {"filename": "session_1.txt", "scope": "client_episodic", "similarity": 0.94},
        ]
        span = self.trace.record_context_retrieval(
            query="how to resolve conflict with product manager",
            retrieved_docs=retrieved_docs,
            latency_ms=38.45,
        )

        self.assertEqual(span.name, "span.context_retrieval")
        self.assertEqual(span.duration_ms, 38.45)
        self.assertEqual(span.attributes["query_length"], 44)
        self.assertEqual(span.attributes["docs_retrieved"], 2)
        self.assertEqual(span.attributes["max_similarity_score"], 0.94)
        self.assertAlmostEqual(span.attributes["avg_similarity_score"], 0.88, places=2)
        self.assertCountEqual(span.attributes["scopes"], ["global_playbook", "client_episodic"])

    def test_record_socratic_guard(self):
        """Verify span.socratic_guard records classification latency, GROW stage, and direct solution flag."""
        span = self.trace.record_socratic_guard(
            user_message="What should I do in this meeting?",
            seeks_direct_solution=True,
            socratic_stage="Goal",
            latency_ms=1.82,
        )

        self.assertEqual(span.name, "span.socratic_guard")
        self.assertEqual(span.duration_ms, 1.82)
        self.assertTrue(span.attributes["seeks_direct_solution"])
        self.assertEqual(span.attributes["detected_grow_stage"], "Goal")

    def test_record_ttft_and_generation_stream(self):
        """Verify TTFT and streaming throughput metrics."""
        ttft = self.trace.record_ttft()
        self.assertIsNotNone(ttft)
        self.assertTrue(self.trace.ttft_recorded)

        # Calling record_ttft again should preserve the initial TTFT
        second_call = self.trace.record_ttft()
        self.assertEqual(second_call, ttft)

        # Record generation stream throughput
        stream_span = self.trace.record_generation_stream(
            duration_ms=500.0,
            tokens_generated=50,
        )
        self.assertEqual(stream_span.name, "span.generation_stream")
        self.assertEqual(stream_span.attributes["tokens_generated"], 50)
        self.assertEqual(stream_span.attributes["tokens_per_second"], 100.0)

    def test_async_span_context_manager(self):
        """Verify async span context manager captures status OK and ERROR."""
        async def run_spans():
            trace = TraceContext()
            async with trace.span("span.custom_ok", attributes={"step": 1}) as s:
                await asyncio.sleep(0.01)

            self.assertEqual(len(trace.spans), 1)
            self.assertEqual(trace.spans[0].status, "OK")
            self.assertGreater(trace.spans[0].duration_ms, 0)
            self.assertEqual(trace.spans[0].attributes["step"], 1)

            with self.assertRaises(ValueError):
                async with trace.span("span.custom_error"):
                    raise ValueError("Simulated fault")

            self.assertEqual(len(trace.spans), 2)
            self.assertEqual(trace.spans[1].status, "ERROR")
            self.assertIn("Simulated fault", trace.spans[1].error_message)

        asyncio.run(run_spans())

    def test_to_diagnostics_dict_payload(self):
        """Verify to_diagnostics_dict produces a compliant JSON dictionary."""
        self.trace.record_context_retrieval(
            query="leadership",
            retrieved_docs=[],
            latency_ms=12.0,
        )
        self.trace.record_socratic_guard(
            user_message="test message",
            seeks_direct_solution=False,
            socratic_stage="Reality",
            latency_ms=0.5,
        )
        self.trace.record_ttft()
        self.trace.record_generation_stream(
            duration_ms=250.0,
            tokens_generated=30,
        )

        diag = self.trace.to_diagnostics_dict()
        self.assertIn("trace_id", diag)
        self.assertIn("traceparent", diag)
        self.assertIn("total_turn_latency_ms", diag)
        self.assertIn("ttft_ms", diag)
        self.assertEqual(diag["tokens_per_second"], 120.0)
        self.assertEqual(len(diag["spans"]), 4)

        span_names = [s["name"] for s in diag["spans"]]
        self.assertIn("span.context_retrieval", span_names)
        self.assertIn("span.socratic_guard", span_names)
        self.assertIn("span.ttft", span_names)
        self.assertIn("span.generation_stream", span_names)

    def test_workflow_populates_turn_diagnostics_telemetry(self):
        """Verify WorkflowNodes.save_conversation embeds telemetry inside turn_diagnostics."""
        async def run_workflow_turn():
            nodes = WorkflowNodes()
            trace = TraceContext()
            trace.record_context_retrieval(
                query="conflict",
                retrieved_docs=[{"scope": "global_playbook", "similarity": 0.85}],
                latency_ms=20.0,
            )
            trace.record_socratic_guard(
                user_message="Help me with conflict",
                seeks_direct_solution=False,
                socratic_stage="Reality",
                latency_ms=1.0,
            )
            trace.record_ttft()
            trace.record_generation_stream(duration_ms=300.0, tokens_generated=45)

            state: ChatState = {
                "user_id": "1",
                "message": "Help me with conflict",
                "conversation_id": None,
                "user_history": [],
                "rewritten_query": "conflict",
                "retrieved_docs": [{"filename": "doc.pdf", "scope": "global_playbook", "similarity": 0.85}],
                "context": "Context",
                "coaching_context": "",
                "dossier_context": "",
                "seeks_direct_solution": False,
                "socratic_coaching_stage": "Reality",
                "retained_summaries": [],
                "working_state": {},
                "source_turn_count": 1,
                "response": "What is the core disagreement?",
                "metadata": {},
                "decision_trace": {},
                "trace": trace,
            }

            # Mock ChatHistoryService.save_conversation_turn
            mock_save = AsyncMock(return_value={
                "id": "msg-123",
                "conversation_id": "conv-456",
                "user_message_id": "umsg-1",
                "assistant_message_id": "amsg-2",
            })
            nodes.chat_history_service.save_conversation_turn = mock_save

            saved_state = await nodes.save_conversation(state)
            self.assertTrue(mock_save.called)

            saved_metadata = mock_save.call_args.kwargs["metadata"]
            turn_diagnostics = saved_metadata.get("turn_diagnostics", {})

            self.assertIn("telemetry", turn_diagnostics)
            telemetry = turn_diagnostics["telemetry"]
            self.assertEqual(telemetry["trace_id"], trace.trace_id)
            self.assertIsNotNone(telemetry["ttft_ms"])
            self.assertEqual(len(telemetry["spans"]), 4)

        asyncio.run(run_workflow_turn())


if __name__ == "__main__":
    unittest.main()

