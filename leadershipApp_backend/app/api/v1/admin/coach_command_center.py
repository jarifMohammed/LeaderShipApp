from datetime import datetime, timezone
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin
from app.core.events import DomainEvent, get_event_bus
from app.core.outbox import OutboxRelay
from app.db.session import get_db
from app.models.client_goal import ClientGoal
from app.models.client_memory_event import ClientMemoryEvent
from app.models.client_memory_profile import ClientMemoryProfile
from app.models.coach_session import CoachSession
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.coach_command import (
    AdminConversationSummaryResponse,
    AdminDossierUpdateRequest,
    AdminMessageResponse,
    ClientDossierResponse,
    ClientGoalResponse,
    ClientMemoryEventResponse,
    ClientMemoryProfileResponse,
    CoachSessionResponse,
    GoalCreateRequest,
    GoalUpdateRequest,
)

router = APIRouter(prefix="/admin", tags=["Coach Command Center"])
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 1. 360° Client Dossier Endpoints
# -----------------------------------------------------------------------------
@router.get("/users/{user_id}/dossier", response_model=ClientDossierResponse)
async def get_client_dossier(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full 360° executive coaching dossier for a specific client."""
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch profile
    prof_stmt = select(ClientMemoryProfile).where(ClientMemoryProfile.user_id == user_id)
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()

    if not profile:
        profile_data = ClientMemoryProfileResponse(
            user_id=user_id,
            executive_summary="Profile in early exploration stage.",
            leadership_style_and_patterns={},
            stakeholder_map={},
            coach_private_notes="",
            version=1,
            updated_at=datetime.now(timezone.utc),
        )
    else:
        profile_data = ClientMemoryProfileResponse(
            user_id=profile.user_id,
            executive_summary=profile.executive_summary,
            leadership_style_and_patterns=profile.leadership_style_and_patterns or {},
            stakeholder_map=profile.stakeholder_map or {},
            coach_private_notes=profile.coach_private_notes,
            version=profile.version,
            updated_at=profile.updated_at,
        )

    # Fetch goals
    goals_stmt = (
        select(ClientGoal)
        .where(ClientGoal.user_id == user_id)
        .order_by(ClientGoal.updated_at.desc())
    )
    goals_res = await db.execute(goals_stmt)
    goals = goals_res.scalars().all()
    goals_data = [
        ClientGoalResponse(
            id=str(g.id),
            user_id=g.user_id,
            title=g.title,
            description=g.description,
            status=g.status,
            readiness_stage=g.readiness_stage,
            source_type=g.source_type,
            source_id=g.source_id,
            evidence_log=g.evidence_log or [],
            created_at=g.created_at,
            updated_at=g.updated_at,
        )
        for g in goals
    ]

    # Fetch recent memory audit events
    events_stmt = (
        select(ClientMemoryEvent)
        .where(ClientMemoryEvent.user_id == user_id)
        .order_by(ClientMemoryEvent.created_at.desc())
        .limit(20)
    )
    events_res = await db.execute(events_stmt)
    events = events_res.scalars().all()
    events_data = [
        ClientMemoryEventResponse(
            id=str(e.id),
            user_id=e.user_id,
            source_type=e.source_type,
            source_id=e.source_id,
            diff_summary=e.diff_summary,
            payload_diff=e.payload_diff or {},
            created_at=e.created_at,
        )
        for e in events
    ]

    # Compute high-level stats
    conv_count_stmt = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    conv_count_res = await db.execute(conv_count_stmt)
    ai_sessions_count = conv_count_res.scalar_one() or 0

    coach_count_stmt = select(func.count(CoachSession.id)).where(CoachSession.user_id == user_id)
    coach_count_res = await db.execute(coach_count_stmt)
    human_sessions_count = coach_count_res.scalar_one() or 0

    stats = {
        "ai_conversations_count": ai_sessions_count,
        "human_coach_sessions_count": human_sessions_count,
        "active_goals_count": len([g for g in goals if g.status in ("exploring", "committed", "in_progress")]),
        "completed_goals_count": len([g for g in goals if g.status == "completed"]),
    }

    return ClientDossierResponse(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        profile=profile_data,
        goals=goals_data,
        recent_events=events_data,
        stats=stats,
    )


@router.patch("/users/{user_id}/dossier", response_model=ClientDossierResponse)
async def update_client_dossier(
    user_id: int,
    request: AdminDossierUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Allow an Admin (Coach) to refine client executive summary, stakeholder map, or private notes."""
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prof_stmt = select(ClientMemoryProfile).where(ClientMemoryProfile.user_id == user_id)
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()

    diffs = {}
    if not profile:
        profile = ClientMemoryProfile(
            id=uuid.uuid4(),
            user_id=user_id,
            executive_summary=request.executive_summary or "",
            leadership_style_and_patterns=request.leadership_style_and_patterns or {},
            stakeholder_map=request.stakeholder_map or {},
            coach_private_notes=request.coach_private_notes or "",
            version=1,
        )
        db.add(profile)
        diffs["created"] = True
    else:
        if request.executive_summary is not None:
            diffs["executive_summary"] = "updated"
            profile.executive_summary = request.executive_summary
        if request.leadership_style_and_patterns is not None:
            diffs["leadership_patterns"] = "updated"
            profile.leadership_style_and_patterns = request.leadership_style_and_patterns
        if request.stakeholder_map is not None:
            diffs["stakeholder_map"] = "updated"
            profile.stakeholder_map = request.stakeholder_map
        if request.coach_private_notes is not None:
            diffs["coach_private_notes"] = "updated"
            profile.coach_private_notes = request.coach_private_notes
        profile.version = (profile.version or 1) + 1

    # Record memory event
    if diffs:
        mem_event = ClientMemoryEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            source_type="admin_manual",
            source_id=f"admin_{current_admin.id}",
            diff_summary=f"Coach {current_admin.full_name} manually refined dossier ({', '.join(diffs.keys())})",
            payload_diff=diffs,
        )
        db.add(mem_event)

    await db.commit()
    return await get_client_dossier(user_id=user_id, current_admin=current_admin, db=db)


# -----------------------------------------------------------------------------
# 2. Longitudinal Client Goals Endpoints
# -----------------------------------------------------------------------------
@router.post("/users/{user_id}/goals", response_model=ClientGoalResponse)
async def create_client_goal(
    user_id: int,
    request: GoalCreateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new longitudinal goal for a client."""
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    if not user_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    new_goal = ClientGoal(
        id=uuid.uuid4(),
        user_id=user_id,
        title=request.title,
        description=request.description,
        status=request.status,
        readiness_stage=request.readiness_stage,
        source_type="admin_manual",
        source_id=f"admin_{current_admin.id}",
        evidence_log=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "admin_name": current_admin.full_name,
            "quote": "Goal established during coaching review.",
        }],
    )
    db.add(new_goal)

    mem_event = ClientMemoryEvent(
        id=uuid.uuid4(),
        user_id=user_id,
        source_type="admin_manual",
        source_id=str(new_goal.id),
        diff_summary=f"Coach established goal: '{new_goal.title}' ({new_goal.status})",
        payload_diff={"goal_id": str(new_goal.id), "title": new_goal.title},
    )
    db.add(mem_event)

    await db.commit()
    await db.refresh(new_goal)

    return ClientGoalResponse(
        id=str(new_goal.id),
        user_id=new_goal.user_id,
        title=new_goal.title,
        description=new_goal.description,
        status=new_goal.status,
        readiness_stage=new_goal.readiness_stage,
        source_type=new_goal.source_type,
        source_id=new_goal.source_id,
        evidence_log=new_goal.evidence_log or [],
        created_at=new_goal.created_at,
        updated_at=new_goal.updated_at,
    )


@router.patch("/users/{user_id}/goals/{goal_id}", response_model=ClientGoalResponse)
async def update_client_goal(
    user_id: int,
    goal_id: str,
    request: GoalUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update goal status, title, description, readiness, or evidence."""
    try:
        parsed_id = uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal UUID")

    stmt = select(ClientGoal).where(ClientGoal.id == parsed_id, ClientGoal.user_id == user_id)
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if request.title is not None:
        goal.title = request.title
    if request.description is not None:
        goal.description = request.description
    if request.status is not None:
        goal.status = request.status
    if request.readiness_stage is not None:
        goal.readiness_stage = request.readiness_stage
    if request.evidence_quote:
        ev_log = list(goal.evidence_log or [])
        ev_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "admin_name": current_admin.full_name,
            "quote": request.evidence_quote,
        })
        goal.evidence_log = ev_log

    goal.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(goal)

    return ClientGoalResponse(
        id=str(goal.id),
        user_id=goal.user_id,
        title=goal.title,
        description=goal.description,
        status=goal.status,
        readiness_stage=goal.readiness_stage,
        source_type=goal.source_type,
        source_id=goal.source_id,
        evidence_log=goal.evidence_log or [],
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


# -----------------------------------------------------------------------------
# 3. Human Coaching Session Upload & Inspection
# -----------------------------------------------------------------------------
@router.post("/users/{user_id}/coach-sessions", response_model=CoachSessionResponse)
async def upload_coach_session(
    user_id: int,
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=255),
    session_date: Optional[str] = Form(default=None),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload audio or transcript document from a human coaching session."""
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    if not user_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    filename = file.filename or "session_recording"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    allowed = ["mp3", "wav", "m4a", "ogg", "pdf", "docx", "txt", "vtt"]
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {', '.join(allowed)}",
        )

    # Save to disk
    upload_dir = os.path.join("uploads", "coach_sessions", str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    saved_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(upload_dir, saved_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_type = "audio" if ext in ["mp3", "wav", "m4a", "ogg"] else "document"
    parsed_date = None
    if session_date:
        try:
            parsed_date = datetime.fromisoformat(session_date.replace("Z", "+00:00"))
        except Exception:
            parsed_date = datetime.now(timezone.utc)

    session_id = uuid.uuid4()
    coach_session = CoachSession(
        id=session_id,
        user_id=user_id,
        uploaded_by_admin_id=current_admin.id,
        title=title,
        session_date=parsed_date or datetime.now(timezone.utc),
        file_type=file_type,
        file_path_or_url=file_path,
        raw_transcript=None,
        extracted_summary=None,
        extracted_facts={},
        processing_status="queued",
    )
    db.add(coach_session)

    # Transactional outbox event enqueue
    await OutboxRelay.enqueue(
        db=db,
        event_type="coach.session.uploaded",
        tenant_user_id=user_id,
        payload={
            "session_id": str(session_id),
            "user_id": user_id,
            "file_path": file_path,
            "file_type": file_type,
            "title": title,
        },
    )

    await db.commit()
    await db.refresh(coach_session)

    # Trigger outbox relay publish
    asyncio.create_task(OutboxRelay.publish_pending(db))

    return CoachSessionResponse(
        id=str(coach_session.id),
        user_id=coach_session.user_id,
        uploaded_by_admin_id=coach_session.uploaded_by_admin_id,
        title=coach_session.title,
        session_date=coach_session.session_date,
        file_type=coach_session.file_type,
        raw_transcript=coach_session.raw_transcript,
        extracted_summary=coach_session.extracted_summary,
        extracted_facts=coach_session.extracted_facts or {},
        processing_status=coach_session.processing_status,
        error_message=coach_session.error_message,
        created_at=coach_session.created_at,
    )


@router.get("/users/{user_id}/coach-sessions", response_model=List[CoachSessionResponse])
async def list_coach_sessions(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all human coaching sessions uploaded for this client."""
    stmt = (
        select(CoachSession)
        .where(CoachSession.user_id == user_id)
        .order_by(CoachSession.created_at.desc())
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    return [
        CoachSessionResponse(
            id=str(s.id),
            user_id=s.user_id,
            uploaded_by_admin_id=s.uploaded_by_admin_id,
            title=s.title,
            session_date=s.session_date,
            file_type=s.file_type,
            raw_transcript=s.raw_transcript,
            extracted_summary=s.extracted_summary,
            extracted_facts=s.extracted_facts or {},
            processing_status=s.processing_status,
            error_message=s.error_message,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.get("/users/{user_id}/coach-sessions/{session_id}", response_model=CoachSessionResponse)
async def get_coach_session_detail(
    user_id: int,
    session_id: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full transcript and extracted insights for a specific session."""
    try:
        parsed_id = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session UUID")

    stmt = select(CoachSession).where(CoachSession.id == parsed_id, CoachSession.user_id == user_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Coach session not found")

    return CoachSessionResponse(
        id=str(session.id),
        user_id=session.user_id,
        uploaded_by_admin_id=session.uploaded_by_admin_id,
        title=session.title,
        session_date=session.session_date,
        file_type=session.file_type,
        raw_transcript=session.raw_transcript,
        extracted_summary=session.extracted_summary,
        extracted_facts=session.extracted_facts or {},
        processing_status=session.processing_status,
        error_message=session.error_message,
        created_at=session.created_at,
    )


# -----------------------------------------------------------------------------
# 4. Unfiltered Chat History & Coach X-Ray Diagnostics
# -----------------------------------------------------------------------------
@router.get("/users/{user_id}/conversations", response_model=List[AdminConversationSummaryResponse])
async def list_user_conversations_for_admin(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all AI coaching conversations for a specific client."""
    stmt = (
        select(
            Conversation.id,
            Conversation.title,
            Conversation.created_at,
            Conversation.updated_at,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
        AdminConversationSummaryResponse(
            id=str(r.id),
            title=r.title or "Coaching Session",
            message_count=r.message_count or 0,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


def sanitize_turn_diagnostics_for_coach(diag: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitizes turn_diagnostics for Coach (ADMIN) view by stripping engineering
    telemetry, token burn, USD costs, and raw span millisecond timings.
    Returns only coaching-relevant diagnostic assessments (Socratic stage, readiness, RAG sources, guardrails).
    """
    if not diag or not isinstance(diag, dict):
        return {}
    sanitized = dict(diag)
    sanitized.pop("telemetry", None)
    return sanitized


@router.get("/conversations/{conversation_id}/messages", response_model=List[AdminMessageResponse])
async def get_conversation_messages_with_diagnostics(
    conversation_id: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the complete, unfiltered User + AI chat transcript for a session,
    including the Calibration Cycle 3/4/5 turn_diagnostics X-ray payload per message.
    Coaches (ADMIN) receive coaching insights with raw telemetry/USD cost stripped.
    Platform Owners (MANAGER) receive full unfiltered turn_diagnostics.
    """
    try:
        parsed_conv_id = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation UUID")

    conv_stmt = select(Conversation).where(Conversation.id == parsed_conv_id)
    conv_res = await db.execute(conv_stmt)
    if not conv_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_stmt = (
        select(Message)
        .where(Message.conversation_id == parsed_conv_id)
        .order_by(Message.created_at.asc())
    )
    msg_res = await db.execute(msg_stmt)
    messages = msg_res.scalars().all()

    is_manager = current_admin.role.lower() == "manager"

    result = []
    for m in messages:
        diag = getattr(m, "turn_diagnostics", None) or {}
        if not is_manager:
            diag = sanitize_turn_diagnostics_for_coach(diag)
        result.append(
            AdminMessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                created_at=m.created_at,
                metadata=m.doc_metadata or {},
                turn_diagnostics=diag,
            )
        )
    return result

