import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.events import DomainEvent, get_event_bus
from app.core.llm import LLMService
from app.core.vector_store import VectorStore
from app.core.idempotency import idempotent_event
from app.db.database import AsyncSessionLocal
from app.models.client_goal import ClientGoal
from app.models.client_memory_event import ClientMemoryEvent
from app.models.client_memory_profile import ClientMemoryProfile
from app.models.coach_session import CoachSession
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.prompts import get_prompt_loader

logger = logging.getLogger(__name__)


class CoachingEventConsumers:
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        document_service: Optional[DocumentService] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.document_service = document_service or DocumentService()

    async def register_handlers(self, event_bus=None):
        bus = event_bus or get_event_bus()
        await bus.subscribe("chat.turn.completed", self.handle_chat_turn_completed)
        await bus.subscribe("coach.session.uploaded", self.handle_coach_session_uploaded)
        await bus.subscribe("coach.session.transcribed", self.handle_coach_session_transcribed)
        await bus.subscribe("document.global.uploaded", self.handle_document_global_uploaded)
        logger.info("CoachingEventConsumers successfully registered all domain handlers.")

    # -------------------------------------------------------------------------
    # 1. Event: chat.turn.completed
    # -------------------------------------------------------------------------
    @idempotent_event(handler_name="handle_chat_turn_completed")
    async def handle_chat_turn_completed(self, event: DomainEvent) -> None:
        """
        Idempotent background handler for chat.turn.completed:
        - Consolidates episodic discoveries into client_memory_profiles
        - Aligns action context & commitments into client_goals
        - Emits client_memory_events audit record
        - Embeds and indexes episodic turn summary into Qdrant (scope='client_episodic')
        """
        payload = event.payload
        user_id_raw = payload.get("user_id") or event.tenant_user_id
        if not user_id_raw:
            logger.warning("chat.turn.completed event missing user_id: %s", event.event_id)
            return

        user_id = int(user_id_raw)
        conversation_id = payload.get("conversation_id", "")
        user_message = payload.get("user_message", "")
        assistant_response = payload.get("assistant_response", "")
        working_state = payload.get("working_state", {})
        turn_diagnostics = payload.get("turn_diagnostics", {})

        async with AsyncSessionLocal() as db:
            try:
                # 1. Fetch or create ClientMemoryProfile
                stmt = select(ClientMemoryProfile).where(ClientMemoryProfile.user_id == user_id)
                res = await db.execute(stmt)
                profile = res.scalar_one_or_none()

                if not profile:
                    profile = ClientMemoryProfile(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        executive_summary="Executive coaching profile initiated.",
                        leadership_style_and_patterns={},
                        stakeholder_map={},
                        version=1,
                    )
                    db.add(profile)
                    await db.flush()

                # 2. Extract key themes from working state if present
                presenting_focus = working_state.get("presenting_focus") or ""
                primary_discovery = working_state.get("primary_discovery") or ""
                commitment = working_state.get("commitment") or ""
                next_experiment = working_state.get("next_experiment") or ""

                diffs = {}
                # Update patterns if new discovery exists
                if primary_discovery:
                    patterns = dict(profile.leadership_style_and_patterns or {})
                    recent_discoveries = patterns.get("recent_discoveries", [])
                    if primary_discovery not in recent_discoveries:
                        recent_discoveries.append(primary_discovery)
                        patterns["recent_discoveries"] = recent_discoveries[-10:]
                        profile.leadership_style_and_patterns = patterns
                        diffs["new_discovery"] = primary_discovery

                # 3. Handle Goal Alignment (Cycles 4 & 5 readiness)
                action_context = working_state.get("action_context") or turn_diagnostics.get("action_context") or []
                if isinstance(action_context, list):
                    for act in action_context:
                        action_title = act.get("underlying_action") or act.get("title") or ""
                        if not action_title:
                            continue
                        act_status = act.get("status", "exploring")
                        act_readiness = act.get("readiness", "unready")

                        # Check existing goal
                        goal_stmt = select(ClientGoal).where(
                            ClientGoal.user_id == user_id,
                            ClientGoal.title == action_title[:255],
                        )
                        goal_res = await db.execute(goal_stmt)
                        existing_goal = goal_res.scalar_one_or_none()

                        if existing_goal:
                            existing_goal.status = act_status
                            existing_goal.readiness_stage = act_readiness
                            ev_log = list(existing_goal.evidence_log or [])
                            ev_log.append({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "conversation_id": conversation_id,
                                "status": act_status,
                                "readiness": act_readiness,
                                "quote": user_message[:300],
                            })
                            existing_goal.evidence_log = ev_log[-20:]
                        else:
                            new_goal = ClientGoal(
                                id=uuid.uuid4(),
                                user_id=user_id,
                                title=action_title[:255],
                                description=f"Goal identified in coaching conversation {conversation_id}",
                                status=act_status,
                                readiness_stage=act_readiness,
                                source_type="ai_chat",
                                source_id=conversation_id,
                                evidence_log=[{
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "conversation_id": conversation_id,
                                    "status": act_status,
                                    "readiness": act_readiness,
                                    "quote": user_message[:300],
                                }],
                            )
                            db.add(new_goal)
                        diffs["goal_aligned"] = action_title

                # 4. Record audit memory event if diffs occurred
                if diffs:
                    profile.version = (profile.version or 1) + 1
                    mem_event = ClientMemoryEvent(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        source_type="ai_chat",
                        source_id=conversation_id,
                        diff_summary=f"Turn updated client profile insights: {', '.join(diffs.keys())}",
                        payload_diff=diffs,
                    )
                    db.add(mem_event)

                await db.commit()

                # 5. Episodic Vector Indexing into Qdrant (scope: client_episodic)
                if primary_discovery or commitment or next_experiment:
                    episodic_snippet = (
                        f"Coaching Turn Takeaway for user {user_id}:\n"
                        f"Focus: {presenting_focus}\n"
                        f"Discovery: {primary_discovery}\n"
                        f"Commitment: {commitment}\n"
                        f"Experiment: {next_experiment}"
                    ).strip()

                    vector = await self.embedding_service.embed(episodic_snippet)
                    await self.vector_store.add_vectors(
                        vectors=[vector],
                        metadata=[{
                            "document_id": str(uuid.uuid4()),
                            "scope": "client_episodic",
                            "user_id": str(user_id),
                            "conversation_id": conversation_id,
                            "text": episodic_snippet,
                            "source": "ai_chat_turn",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }],
                    )
                    logger.info("Indexed episodic memory point for user %s into Qdrant", user_id)

            except Exception as e:
                logger.exception("Failed processing chat.turn.completed for user %s: %s", user_id, e)

    # -------------------------------------------------------------------------
    # 2. Event: coach.session.uploaded
    # -------------------------------------------------------------------------
    @idempotent_event(handler_name="handle_coach_session_uploaded")
    async def handle_coach_session_uploaded(self, event: DomainEvent) -> None:
        """
        Transcribes audio or extracts text from document, updating coach_sessions.
        Then emits coach.session.transcribed.
        """
        payload = event.payload
        session_id_str = payload.get("session_id")
        user_id = payload.get("user_id")
        file_path = payload.get("file_path", "")
        file_type = payload.get("file_type", "")

        if not session_id_str:
            return

        session_id = uuid.UUID(str(session_id_str))

        async with AsyncSessionLocal() as db:
            stmt = select(CoachSession).where(CoachSession.id == session_id)
            res = await db.execute(stmt)
            session = res.scalar_one_or_none()
            if not session:
                logger.warning("CoachSession %s not found", session_id)
                return

            try:
                session.processing_status = "transcribing"
                await db.commit()

                transcript = ""
                # Audio transcription path
                if file_type == "audio" or file_path.lower().endswith((".mp3", ".wav", ".m4a", ".ogg")):
                    if settings.OPENAI_API_KEY and os.path.exists(file_path):
                        try:
                            from openai import AsyncOpenAI
                            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                            with open(file_path, "rb") as audio_file:
                                transcript_resp = await client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                )
                                transcript = transcript_resp.text
                        except Exception as transcribe_err:
                            logger.warning("OpenAI whisper transcription failed: %s; using fallback note", transcribe_err)
                            transcript = f"Audio transcription pending: {session.title}"
                    else:
                        transcript = f"[Simulated Audio Transcription for {session.title}]"
                else:
                    # Document parsing path (pdf, docx, txt, md, vtt)
                    if os.path.exists(file_path):
                        ext = file_path.rsplit(".", 1)[-1].lower()
                        with open(file_path, "rb") as f:
                            content = f.read()
                        if ext == "pdf":
                            transcript = self.document_service._extract_pdf(content)
                        elif ext == "docx":
                            transcript = self.document_service._extract_docx(content)
                        else:
                            transcript = content.decode("utf-8", errors="ignore")
                    else:
                        transcript = session.raw_transcript or f"[Content from {session.title}]"

                session.raw_transcript = transcript
                session.processing_status = "extracting"
                await db.commit()

                # Dispatch next event
                bus = get_event_bus()
                await bus.publish(
                    DomainEvent(
                        event_type="coach.session.transcribed",
                        tenant_user_id=user_id,
                        payload={
                            "session_id": str(session.id),
                            "user_id": user_id,
                            "transcript": transcript,
                            "title": session.title,
                        },
                    )
                )

            except Exception as e:
                logger.exception("Failed in coach.session.uploaded for session %s: %s", session_id, e)
                session.processing_status = "failed"
                session.error_message = str(e)
                await db.commit()

    # -------------------------------------------------------------------------
    # 3. Event: coach.session.transcribed
    # -------------------------------------------------------------------------
    @idempotent_event(handler_name="handle_coach_session_transcribed")
    async def handle_coach_session_transcribed(self, event: DomainEvent) -> None:
        """
        Runs structured LLM extraction on transcript:
        - Executive summary
        - Stakeholder map updates
        - Leadership patterns & blind spots
        - Identified longitudinal goals
        - Indexes full transcript chunks into Qdrant (scope='client_episodic', user_id=...)
        """
        payload = event.payload
        session_id_str = payload.get("session_id")
        user_id = payload.get("user_id")
        transcript = payload.get("transcript", "")
        title = payload.get("title", "Coaching Session")

        if not session_id_str or not user_id:
            return

        session_id = uuid.UUID(str(session_id_str))

        # Pre-LLM / Vector Ingestion PII Sanitization
        from app.core.pii_sanitizer import PIISanitizer
        sanitized_res = PIISanitizer.sanitize(transcript)
        clean_transcript = sanitized_res.sanitized_text

        async with AsyncSessionLocal() as db:
            stmt = select(CoachSession).where(CoachSession.id == session_id)
            res = await db.execute(stmt)
            session = res.scalar_one_or_none()
            if not session:
                return

            try:
                try:
                    extraction_prompt = get_prompt_loader().render(
                        "coach_session_extraction.jinja2",
                        title=title,
                        transcript=clean_transcript[:8000],
                    )
                except Exception:
                    extraction_prompt = f"""You are an executive coaching analyst. Analyze the following human coaching session transcript between a leadership coach and an executive client.

CRITICAL SPEAKER ATTRIBUTION RULES:
- Explicitly differentiate between [Coach] dialogue and [Client] dialogue in the transcript.
- [Coach] prompts, metaphors, hypothetical scenarios, suggestions, or probing questions must NEVER be misattributed to the client as their personal goals, behavioral patterns, or stakeholder views.
- Extract ONLY client-owned statements:
  * Longitudinal goals must represent commitments formulated, embraced, and owned by the [Client].
  * Leadership patterns must reflect the [Client]'s demonstrated behaviors and self-identified challenges/strengths.
  * Stakeholder dynamics must reflect the [Client]'s actual lived relationships and reporting structures.

Extract structured insights in strict JSON format matching:
{{
  "executive_summary": "2-3 concise paragraphs summarizing client themes, challenges, and shifts",
  "stakeholders": [
    {{"name_or_role": "string", "relationship": "manager|peer|direct_report|board", "dynamics": "string"}}
  ],
  "leadership_patterns": [
    {{"pattern": "string", "strength_or_blindspot": "strength|blindspot", "evidence": "string"}}
  ],
  "longitudinal_goals": [
    {{"title": "string", "description": "string", "readiness_stage": "exploring|preparing|ready|practicing"}}
  ]
}}

Session Title: {title}
Transcript snippet:
{clean_transcript[:8000]}

Output ONLY valid JSON:"""

                extracted_json: Dict[str, Any] = {}
                try:
                    llm_output = await self.llm_service.generate(
                        system_prompt="You are an expert executive coach evaluator. Output valid JSON only.",
                        user_message=extraction_prompt,
                    )
                    cleaned = llm_output.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:].rstrip("`").strip()
                    elif cleaned.startswith("```"):
                        cleaned = cleaned[3:].rstrip("`").strip()
                    extracted_json = json.loads(cleaned)
                except Exception as llm_err:
                    logger.warning("LLM extraction error for session %s: %s; using heuristic fallback", session_id, llm_err)
                    extracted_json = {
                        "executive_summary": f"Coaching session focused on {title}.",
                        "stakeholders": [],
                        "leadership_patterns": [],
                        "longitudinal_goals": [],
                    }

                # Update CoachSession record
                session.extracted_summary = extracted_json.get("executive_summary", "")
                session.extracted_facts = extracted_json
                session.processing_status = "indexing"
                await db.commit()

                # Update ClientMemoryProfile
                prof_stmt = select(ClientMemoryProfile).where(ClientMemoryProfile.user_id == user_id)
                prof_res = await db.execute(prof_stmt)
                profile = prof_res.scalar_one_or_none()
                if not profile:
                    profile = ClientMemoryProfile(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        executive_summary=session.extracted_summary,
                        leadership_style_and_patterns={},
                        stakeholder_map={},
                        version=1,
                    )
                    db.add(profile)
                    await db.flush()

                # Merge stakeholders
                existing_stakeholders = dict(profile.stakeholder_map or {})
                for sh in extracted_json.get("stakeholders", []):
                    key = sh.get("name_or_role", "unknown")
                    existing_stakeholders[key] = sh
                profile.stakeholder_map = existing_stakeholders

                # Merge patterns
                existing_patterns = dict(profile.leadership_style_and_patterns or {})
                session_patterns = existing_patterns.get("patterns", [])
                session_patterns.extend(extracted_json.get("leadership_patterns", []))
                existing_patterns["patterns"] = session_patterns[-15:]
                profile.leadership_style_and_patterns = existing_patterns
                profile.version = (profile.version or 1) + 1

                # Synchronize Goals
                for g in extracted_json.get("longitudinal_goals", []):
                    g_title = g.get("title", "")[:255]
                    if not g_title:
                        continue
                    new_goal = ClientGoal(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        title=g_title,
                        description=g.get("description", ""),
                        status="committed",
                        readiness_stage=g.get("readiness_stage", "preparing"),
                        source_type="coach_session",
                        source_id=str(session.id),
                        evidence_log=[{
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "session_id": str(session.id),
                            "quote": f"Identified in coach session '{title}'",
                        }],
                    )
                    db.add(new_goal)

                # Record Memory Event
                mem_event = ClientMemoryEvent(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    source_type="coach_session",
                    source_id=str(session.id),
                    diff_summary=f"Human coaching session '{title}' integrated into dossier with {len(extracted_json.get('longitudinal_goals', []))} goals.",
                    payload_diff=extracted_json,
                )
                db.add(mem_event)
                await db.commit()

                # Chunk and index sanitized transcript into Qdrant (scope='client_episodic', user_id=...)
                chunks = self.document_service._chunk_text(clean_transcript)
                if chunks:
                    vectors = await self.embedding_service.embed_batch(chunks)
                    metadata_list = [
                        {
                            "document_id": str(session.id),
                            "chunk_id": str(uuid.uuid4()),
                            "scope": "client_episodic",
                            "user_id": str(user_id),
                            "session_id": str(session.id),
                            "title": title,
                            "text": chunk,
                            "source": "coach_session_transcript",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                        for chunk in chunks
                    ]
                    await self.vector_store.add_vectors(vectors, metadata_list)

                session.processing_status = "completed"
                await db.commit()
                logger.info("Successfully completed processing for CoachSession %s", session_id)

            except Exception as e:
                logger.exception("Failed in coach.session.transcribed for session %s: %s", session_id, e)
                session.processing_status = "failed"
                session.error_message = str(e)
                await db.commit()

    # -------------------------------------------------------------------------
    # 4. Event: document.global.uploaded
    # -------------------------------------------------------------------------
    @idempotent_event(handler_name="handle_document_global_uploaded")
    async def handle_document_global_uploaded(self, event: DomainEvent) -> None:
        """
        Asynchronously chunks, embeds, and indexes admin global documents into Qdrant (scope='global_playbook').
        """
        payload = event.payload
        document_id_str = payload.get("document_id")
        file_path = payload.get("file_path")
        file_type = payload.get("file_type")

        if not document_id_str:
            return

        document_id = uuid.UUID(str(document_id_str))

        async with AsyncSessionLocal() as db:
            stmt = select(Document).where(Document.id == document_id)
            res = await db.execute(stmt)
            doc = res.scalar_one_or_none()
            if not doc:
                return

            try:
                doc.status = "processing"
                await db.commit()

                # Extract text
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")

                with open(file_path, "rb") as f:
                    content = f.read()

                if file_type == "pdf":
                    text = self.document_service._extract_pdf(content)
                elif file_type == "docx":
                    text = self.document_service._extract_docx(content)
                else:
                    text = content.decode("utf-8", errors="ignore")

                # Chunk
                chunks = self.document_service._chunk_text(text)
                if not chunks:
                    doc.status = "completed"
                    doc.chunk_count = 0
                    await db.commit()
                    return

                # Embed
                vectors = await self.embedding_service.embed_batch(chunks)

                # Persist DocumentChunk rows in DB
                metadata_list = []
                for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    chunk_id = uuid.uuid4()
                    db_chunk = DocumentChunk(
                        id=chunk_id,
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk,
                        vector_id=str(chunk_id),
                    )
                    db.add(db_chunk)
                    metadata_list.append({
                        "document_id": str(doc.id),
                        "chunk_id": str(chunk_id),
                        "scope": "global_playbook",
                        "title": doc.title,
                        "category": getattr(doc, "category", "general"),
                        "text": chunk,
                        "source": "global_knowledge_base",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })

                # Index in Qdrant with scope: global_playbook
                await self.vector_store.add_vectors(vectors, metadata_list)

                doc.status = "completed"
                doc.chunk_count = len(chunks)
                await db.commit()
                logger.info("Successfully indexed global document %s (%d chunks)", doc.id, len(chunks))

            except Exception as e:
                logger.exception("Async document processing failed for %s: %s", document_id, e)
                doc.status = "failed"
                doc.error_message = str(e)
                await db.commit()

