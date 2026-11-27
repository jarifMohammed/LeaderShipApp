export interface ClientMemoryProfile {
  user_id: number;
  executive_summary?: string | null;
  leadership_style_and_patterns: Record<string, unknown>;
  stakeholder_map: Record<string, unknown>;
  coach_private_notes?: string | null;
  version: number;
  updated_at?: string | null;
}

export type GoalStatus = "exploring" | "committed" | "in_progress" | "completed" | "stalled";

export type ReadinessStage =
  | "precontemplation"
  | "contemplation"
  | "preparation"
  | "action"
  | "maintenance"
  | "relapse";

export interface EvidenceLogItem {
  timestamp?: string;
  source?: string;
  quote?: string;
  observation?: string;
}

export interface ClientGoal {
  id: string;
  user_id: number;
  title: string;
  description?: string | null;
  status: GoalStatus;
  readiness_stage?: ReadinessStage | string | null;
  source_type: "ai_chat" | "coach_session" | "admin_manual" | string;
  source_id?: string | null;
  evidence_log: EvidenceLogItem[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ClientMemoryEvent {
  id: string;
  user_id: number;
  source_type: "ai_chat" | "coach_session" | "admin_manual" | string;
  source_id?: string | null;
  diff_summary: string;
  payload_diff: Record<string, unknown>;
  created_at?: string | null;
}

export interface ClientDossier {
  user_id: number;
  full_name: string;
  email: string;
  profile: ClientMemoryProfile;
  goals: ClientGoal[];
  recent_events: ClientMemoryEvent[];
  stats: {
    total_goals?: number;
    active_goals?: number;
    completed_goals?: number;
    total_events?: number;
    total_sessions?: number;
    [key: string]: unknown;
  };
}

export interface UpdateDossierPayload {
  executive_summary?: string | null;
  leadership_style_and_patterns?: Record<string, unknown>;
  stakeholder_map?: Record<string, unknown>;
  coach_private_notes?: string | null;
}

export interface CreateGoalPayload {
  title: string;
  description?: string;
  status?: GoalStatus;
  readiness_stage?: ReadinessStage | string;
}

export interface UpdateGoalPayload {
  title?: string;
  description?: string;
  status?: GoalStatus;
  readiness_stage?: ReadinessStage | string;
  evidence_quote?: string;
}

export type SessionProcessingStatus =
  | "queued"
  | "transcribing"
  | "extracting"
  | "indexing"
  | "completed"
  | "failed";

export interface CoachSession {
  id: string;
  user_id: number;
  uploaded_by_admin_id?: number | null;
  title: string;
  session_date?: string | null;
  file_type: string;
  raw_transcript?: string | null;
  extracted_summary?: string | null;
  extracted_facts: Record<string, unknown>;
  processing_status: SessionProcessingStatus;
  error_message?: string | null;
  created_at?: string | null;
}

export interface AdminConversationSummary {
  id: string;
  title: string;
  message_count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TurnDiagnostics {
  progress_assessment?: Record<string, unknown> | null;
  support_assessment?: Record<string, unknown> | null;
  action_context?: Array<Record<string, unknown>> | null;
  socratic_stage?: "Goal" | "Reality" | "Options" | "Will" | string | null;
  seeks_direct_solution?: boolean;
  proposed_stage?: string | null;
  enforced_stage?: string | null;
  enforced_move?: string | null;
  policy_reasons?: string[];
  rag_sources?: Array<{
    title?: string;
    scope?: string;
    similarity?: number;
  }>;
  telemetry?: Record<string, unknown> | null;
}

export interface AdminMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string | null;
  metadata?: Record<string, unknown> | null;
  turn_diagnostics?: TurnDiagnostics | null;
}

