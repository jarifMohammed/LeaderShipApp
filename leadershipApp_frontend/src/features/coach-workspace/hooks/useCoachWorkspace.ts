"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getClientConversations,
  getClientDossier,
  getCoachSessions,
  getConversationMessages,
  createClientGoal,
  updateClientDossier,
  updateClientGoal,
  uploadCoachSession,
} from "../api/coach-workspace.api";
import type {
  CreateGoalPayload,
  UpdateDossierPayload,
  UpdateGoalPayload,
} from "../types";

export const coachWorkspaceKeys = {
  dossier: (userId: string | number) => ["coach-workspace", "dossier", String(userId)] as const,
  sessions: (userId: string | number) => ["coach-workspace", "sessions", String(userId)] as const,
  conversations: (userId: string | number) =>
    ["coach-workspace", "conversations", String(userId)] as const,
  messages: (conversationId: string) =>
    ["coach-workspace", "messages", conversationId] as const,
};

export function useClientDossier(userId: string | number) {
  return useQuery({
    queryKey: coachWorkspaceKeys.dossier(userId),
    queryFn: () => getClientDossier(userId),
    enabled: Boolean(userId),
  });
}

export function useUpdateDossier(userId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateDossierPayload) => updateClientDossier(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: coachWorkspaceKeys.dossier(userId) });
    },
  });
}

export function useCreateGoal(userId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateGoalPayload) => createClientGoal(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: coachWorkspaceKeys.dossier(userId) });
    },
  });
}

export function useUpdateGoal(userId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ goalId, data }: { goalId: string; data: UpdateGoalPayload }) =>
      updateClientGoal(userId, goalId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: coachWorkspaceKeys.dossier(userId) });
    },
  });
}

export function useCoachSessions(userId: string | number) {
  return useQuery({
    queryKey: coachWorkspaceKeys.sessions(userId),
    queryFn: () => getCoachSessions(userId),
    enabled: Boolean(userId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      const isProcessing = data.some((s) =>
        ["queued", "transcribing", "extracting", "indexing"].includes(s.processing_status),
      );
      return isProcessing ? 3000 : false;
    },
  });
}

export function useUploadCoachSession(userId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      title,
      sessionDate,
    }: {
      file: File;
      title: string;
      sessionDate?: string;
    }) => uploadCoachSession(userId, file, title, sessionDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: coachWorkspaceKeys.sessions(userId) });
      queryClient.invalidateQueries({ queryKey: coachWorkspaceKeys.dossier(userId) });
    },
  });
}

export function useClientConversations(userId: string | number) {
  return useQuery({
    queryKey: coachWorkspaceKeys.conversations(userId),
    queryFn: () => getClientConversations(userId),
    enabled: Boolean(userId),
  });
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: coachWorkspaceKeys.messages(conversationId ?? ""),
    queryFn: () => (conversationId ? getConversationMessages(conversationId) : Promise.resolve([])),
    enabled: Boolean(conversationId),
  });
}

