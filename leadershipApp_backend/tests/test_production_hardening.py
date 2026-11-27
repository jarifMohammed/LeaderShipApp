import asyncio
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.api.v1.user.chat import chat, ChatRequest
from app.core.locks import ConversationLock
from app.models.user import User
from app.prompts import get_prompt_loader
from app.workflows.chat_workflow import WorkflowNodes


class ProductionHardeningTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(
            id=42,
            email="leader@example.com",
            full_name="Leader Executive",
            role="user",
            is_active=True,
        )

    # -------------------------------------------------------------------------
    # 1. Per-Conversation Concurrency Lock
    # -------------------------------------------------------------------------
    async def test_conversation_lock_mutual_exclusion(self):
        conv_id = str(uuid.uuid4())
        lock1 = ConversationLock(conv_id, ttl=30)
        lock2 = ConversationLock(conv_id, ttl=30)

        # First lock acquires
        self.assertTrue(await lock1.acquire())

        # Second concurrent lock for same conversation must fail
        self.assertFalse(await lock2.acquire())

        # Once first lock is released, second lock can acquire
        await lock1.release()
        self.assertTrue(await lock2.acquire())
        await lock2.release()

    async def test_chat_endpoint_returns_409_on_concurrent_request(self):
        conv_id = str(uuid.uuid4())
        # Pre-lock the conversation
        existing_lock = ConversationLock(conv_id, ttl=30)
        self.assertTrue(await existing_lock.acquire())

        try:
            req = ChatRequest(message="Are you there?", conversation_id=conv_id, stream=False)
            with self.assertRaises(HTTPException) as ctx:
                await chat(request=req, current_user=self.user)

            self.assertEqual(ctx.exception.status_code, 409)
            self.assertIn("Jess is still responding to your previous message", ctx.exception.detail)
        finally:
            await existing_lock.release()

    # -------------------------------------------------------------------------
    # 2. Qdrant 2.5s Timeout Circuit Breaker Fallback
    # -------------------------------------------------------------------------
    async def test_qdrant_timeout_fallback_marks_rag_degraded_without_crashing(self):
        nodes = WorkflowNodes()
        conv_id = str(uuid.uuid4())

        # Simulate a 5-second hung vector store / network freeze
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(5.0)
            return [{"filename": "NeverLoaded.pdf", "similarity": 0.99}]

        nodes._fetch_documents = slow_fetch
        nodes._fetch_history = AsyncMock(return_value=[])
        nodes.chat_history_service.get_or_create_conversation = AsyncMock(return_value=MagicMock())
        nodes.chat_history_service.get_working_state = AsyncMock(return_value=None)
        nodes.query_rewriting = AsyncMock(side_effect=lambda s: {**s, "rewritten_query": s["message"]})
        nodes._fetch_client_dossier_context = AsyncMock(return_value="Dossier Context")

        state = {
            "user_id": "42",
            "message": "How do I delegate effectively to VP of Engineering?",
            "conversation_id": conv_id,
            "metadata": {},
        }

        # retrieve_data should wrap the call with a 2.5s timeout, catch it, and continue with degraded RAG
        result_state = await nodes.retrieve_data(state)

        self.assertTrue(result_state["metadata"]["rag_degraded"])
        self.assertEqual(result_state["retrieved_docs"], [])
        self.assertEqual(result_state["dossier_context"], "Dossier Context")

    # -------------------------------------------------------------------------
    # 3. Speaker Attribution on Coaching Transcripts
    # -------------------------------------------------------------------------
    def test_coach_session_extraction_prompt_speaker_attribution(self):
        loader = get_prompt_loader()
        rendered = loader.render(
            "coach_session_extraction.jinja2",
            title="Q3 Executive Review",
            transcript="[Coach]: What is holding you back? [Client]: I hesitate to delegate.",
        )

        self.assertIn("CRITICAL SPEAKER ATTRIBUTION RULES", rendered)
        self.assertIn("[Coach] prompts, metaphors, hypothetical scenarios", rendered)
        self.assertIn("Extract ONLY client-owned statements", rendered)
        self.assertIn("Q3 Executive Review", rendered)

    # -------------------------------------------------------------------------
    # 4. Jinja2 Prompt Loader
    # -------------------------------------------------------------------------
    def test_prompt_loader_renders_socratic_coach_system_template(self):
        loader = get_prompt_loader()
        system_prompt = loader.render("socratic_coach_system.jinja2")

        self.assertIn("You are Jess", system_prompt)
        self.assertIn("NON-DIRECTIVE SOCRATIC CONTRACT", system_prompt)
        self.assertIn("GROW (Goal, Reality, Options, Will)", system_prompt)


if __name__ == "__main__":
    unittest.main()
