from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ClientMemoryProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    executive_summary: Optional[str] = None
    leadership_style_and_patterns: Dict[str, Any] = Field(default_factory=dict)
    stakeholder_map: Dict[str, Any] = Field(default_factory=dict)
    coach_private_notes: Optional[str] = None
    version: int = 1
    updated_at: Optional[datetime] = None


class ClientGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    title: str
    description: Optional[str] = None
    status: str
    readiness_stage: Optional[str] = None
    source_type: str
    source_id: Optional[str] = None
    evidence_log: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GoalCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="committed")
    readiness_stage: str = Field(default="preparing")


class GoalUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    readiness_stage: Optional[str] = None
    evidence_quote: Optional[str] = None


class ClientMemoryEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    source_type: str
    source_id: Optional[str] = None
    diff_summary: str
    payload_diff: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class ClientDossierResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    profile: ClientMemoryProfileResponse
    goals: List[ClientGoalResponse]
    recent_events: List[ClientMemoryEventResponse]
    stats: Dict[str, Any] = Field(default_factory=dict)


class AdminDossierUpdateRequest(BaseModel):
    executive_summary: Optional[str] = None
    leadership_style_and_patterns: Optional[Dict[str, Any]] = None
    stakeholder_map: Optional[Dict[str, Any]] = None
    coach_private_notes: Optional[str] = None


class CoachSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    uploaded_by_admin_id: Optional[int] = None
    title: str
    session_date: Optional[datetime] = None
    file_type: str
    raw_transcript: Optional[str] = None
    extracted_summary: Optional[str] = None
    extracted_facts: Dict[str, Any] = Field(default_factory=dict)
    processing_status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class AdminConversationSummaryResponse(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    turn_diagnostics: Optional[Dict[str, Any]] = None

