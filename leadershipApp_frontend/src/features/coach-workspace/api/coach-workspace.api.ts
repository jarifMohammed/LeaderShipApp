import { api } from "@/lib/api";
import type {
  AdminConversationSummary,
  AdminMessage,
  ClientDossier,
  CoachSession,
  CreateGoalPayload,
  ClientGoal,
  UpdateDossierPayload,
  UpdateGoalPayload,
} from "../types";

export async function getClientDossier(userId: string | number): Promise<ClientDossier> {
  const response = await api.get(`/admin/users/${userId}/dossier`);
  return response.data;
}

export async function updateClientDossier(
  userId: string | number,
  data: UpdateDossierPayload,
): Promise<ClientDossier> {
  const response = await api.patch(`/admin/users/${userId}/dossier`, data);
  return response.data;
}

export async function createClientGoal(
  userId: string | number,
  data: CreateGoalPayload,
): Promise<ClientGoal> {
  const response = await api.post(`/admin/users/${userId}/goals`, data);
  return response.data;
}

export async function updateClientGoal(
  userId: string | number,
  goalId: string,
  data: UpdateGoalPayload,
): Promise<ClientGoal> {
  const response = await api.patch(`/admin/users/${userId}/goals/${goalId}`, data);
  return response.data;
}

export async function uploadCoachSession(
  userId: string | number,
  file: File,
  title: string,
  sessionDate?: string,
): Promise<CoachSession> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);
  if (sessionDate) {
    formData.append("session_date", sessionDate);
  }

  const response = await api.post(`/admin/users/${userId}/coach-sessions`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export async function getCoachSessions(userId: string | number): Promise<CoachSession[]> {
  const response = await api.get(`/admin/users/${userId}/coach-sessions`);
  return response.data;
}

export async function getCoachSession(
  userId: string | number,
  sessionId: string,
): Promise<CoachSession> {
  const response = await api.get(`/admin/users/${userId}/coach-sessions/${sessionId}`);
  return response.data;
}

export async function getClientConversations(
  userId: string | number,
): Promise<AdminConversationSummary[]> {
  const response = await api.get(`/admin/users/${userId}/conversations`);
  return response.data;
}

export async function getConversationMessages(
  conversationId: string,
): Promise<AdminMessage[]> {
  const response = await api.get(`/admin/conversations/${conversationId}/messages`);
  return response.data;
}

