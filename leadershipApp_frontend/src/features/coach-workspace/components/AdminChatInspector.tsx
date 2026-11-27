"use client";

import { useState } from "react";
import {
  Activity,
  BookOpen,
  Bot,
  ChevronRight,
  Eye,
  EyeOff,
  MessageSquare,
  User,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useClientConversations,
  useConversationMessages,
} from "../hooks/useCoachWorkspace";
import type { AdminConversationSummary, AdminMessage, TurnDiagnostics } from "../types";

export function AdminChatInspector({ userId }: { userId: string | number }) {
  const { data: conversations, isLoading: loadingConvs } = useClientConversations(userId);

  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [showXRay, setShowXRay] = useState(true);

  const activeConvId = selectedConvId || conversations?.[0]?.id || null;
  const { data: messages, isLoading: loadingMessages } = useConversationMessages(activeConvId);

  const defaultAssistantMessage = messages && messages.length > 0
    ? ([...messages].reverse().find((m) => m.role === "assistant" && m.turn_diagnostics) || messages[messages.length - 1])
    : null;

  const selectedMessage = messages?.find((m) => m.id === selectedMessageId) || defaultAssistantMessage || null;
  const activeConv = conversations?.find((c) => c.id === activeConvId);

  return (
    <div className="flex flex-col lg:flex-row h-[780px] rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
      {/* Pane 1: Conversations List (Left) */}
      <div className="w-full lg:w-72 border-r border-slate-200 flex flex-col bg-slate-50/50 shrink-0">
        <div className="p-4 border-b border-slate-200 bg-white">
          <h3 className="font-semibold text-sm text-[#023337] flex items-center gap-2">
            <MessageSquare className="size-4" />
            AI Sessions ({conversations?.length || 0})
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">Select a coaching thread to inspect</p>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-1">
          {loadingConvs ? (
            <p className="text-xs text-slate-400 p-4 text-center">Loading conversations...</p>
          ) : !conversations || conversations.length === 0 ? (
            <p className="text-xs text-slate-400 p-4 text-center italic">No AI sessions recorded yet</p>
          ) : (
            conversations.map((conv: AdminConversationSummary) => {
              const isSelected = conv.id === selectedConvId;
              return (
                <button
                  key={conv.id}
                  onClick={() => {
                    setSelectedConvId(conv.id);
                  }}
                  className={`w-full text-left p-3 rounded-lg text-xs transition-colors flex items-center justify-between ${
                    isSelected
                      ? "bg-[#023337] text-white shadow-sm"
                      : "hover:bg-slate-100 text-slate-700"
                  }`}
                >
                  <div className="truncate pr-2">
                    <p className={`font-medium truncate ${isSelected ? "text-white" : "text-slate-900"}`}>
                      {conv.title || "Untitled Conversation"}
                    </p>
                    <p className={`text-[10px] mt-1 ${isSelected ? "text-slate-200" : "text-slate-400"}`}>
                      {conv.message_count} messages • {conv.updated_at ? new Date(conv.updated_at).toLocaleDateString() : ""}
                    </p>
                  </div>
                  <ChevronRight className={`size-4 shrink-0 ${isSelected ? "text-white" : "text-slate-300"}`} />
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Pane 2: Transcript (Center) */}
      <div className="flex-1 flex flex-col border-r border-slate-200 bg-white min-w-0">
        <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/30">
          <div>
            <h4 className="text-xs font-semibold text-slate-800 truncate">
              {activeConv ? activeConv.title : "Select Conversation"}
            </h4>
            <span className="text-[10px] text-slate-400 font-mono">
              ID: {selectedConvId || "none"}
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-[#023337] gap-1.5"
            onClick={() => setShowXRay(!showXRay)}
          >
            {showXRay ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
            {showXRay ? "Hide Coach X-Ray" : "Show Coach X-Ray"}
          </Button>
        </div>

        {/* Message stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loadingMessages ? (
            <p className="text-xs text-slate-400 p-8 text-center">Loading transcript...</p>
          ) : !messages || messages.length === 0 ? (
            <p className="text-xs text-slate-400 p-8 text-center italic">No messages in this conversation</p>
          ) : (
            messages.map((msg: AdminMessage) => {
              const isAssistant = msg.role === "assistant";
              const isSelected = selectedMessage?.id === msg.id;

              return (
                <div
                  key={msg.id}
                  onClick={() => setSelectedMessageId(msg.id)}
                  className={`cursor-pointer rounded-xl p-3.5 transition-all text-xs border ${
                    isSelected
                      ? "ring-2 ring-[#023337] border-transparent"
                      : "border-slate-100 hover:border-slate-300"
                  } ${isAssistant ? "bg-slate-50/70" : "bg-white"}`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-semibold flex items-center gap-1.5 text-slate-800">
                      {isAssistant ? (
                        <>
                          <Bot className="size-3.5 text-[#023337]" />
                          Jess (AI Coach)
                        </>
                      ) : (
                        <>
                          <User className="size-3.5 text-slate-600" />
                          Client
                        </>
                      )}
                    </span>
                    <div className="flex items-center gap-2">
                      {msg.turn_diagnostics?.socratic_stage && (
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 bg-teal-50 text-teal-800">
                          GROW: {msg.turn_diagnostics.socratic_stage}
                        </Badge>
                      )}
                      {msg.turn_diagnostics?.seeks_direct_solution && (
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 bg-amber-50 text-amber-800">
                          Solution Sought
                        </Badge>
                      )}
                      <span className="text-[10px] text-slate-400">
                        {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ""}
                      </span>
                    </div>
                  </div>

                  <p className="whitespace-pre-wrap leading-relaxed text-slate-700">
                    {msg.content}
                  </p>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Pane 3: Coach Diagnostics X-Ray (Right) */}
      {showXRay && (
        <div className="w-full lg:w-84 xl:w-96 flex flex-col bg-slate-50/80 shrink-0 border-l border-slate-200">
          <div className="p-3.5 border-b border-slate-200 bg-white flex items-center justify-between">
            <h3 className="font-semibold text-xs text-[#023337] flex items-center gap-1.5">
              <Activity className="size-4" />
              Coach Diagnostics X-Ray
            </h3>
            <span className="text-[10px] text-slate-400 uppercase font-mono">Calibration C5</span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {!selectedMessage ? (
              <p className="text-slate-400 text-center italic py-8">Select a message turn to inspect internal coaching diagnostics</p>
            ) : !selectedMessage.turn_diagnostics ? (
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-amber-800">
                <p className="font-medium">No turn diagnostics recorded</p>
                <p className="text-[11px] mt-1 text-amber-700">
                  Diagnostics are computed and persisted on AI assistant turns.
                </p>
              </div>
            ) : (
              (() => {
                const diag = selectedMessage.turn_diagnostics as TurnDiagnostics;
                return (
                  <div className="space-y-4">
                    {/* Socratic GROW Stage */}
                    <Card className="shadow-none border-slate-200">
                      <CardHeader className="p-3 pb-1">
                        <CardTitle className="text-xs font-semibold text-slate-800">
                          Socratic Inquiry Stage
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-3 pt-1 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">GROW Stage:</span>
                          <Badge className="bg-[#023337] text-white text-[10px]">
                            {diag.socratic_stage || "Not classified"}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Seeks Direct Solution:</span>
                          <span className={`font-semibold ${diag.seeks_direct_solution ? "text-amber-600" : "text-emerald-600"}`}>
                            {diag.seeks_direct_solution ? "Yes (Refused)" : "No (Autonomous)"}
                          </span>
                        </div>
                        {diag.enforced_move && (
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500">Enforced Move:</span>
                            <span className="font-mono text-[10px] text-slate-700">{diag.enforced_move}</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Progress Assessment */}
                    {diag.progress_assessment && (
                      <Card className="shadow-none border-slate-200">
                        <CardHeader className="p-3 pb-1">
                          <CardTitle className="text-xs font-semibold text-slate-800">
                            Progress Assessment (Cycle 4)
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-3 pt-1">
                          <pre className="text-[10px] p-2 bg-white rounded border border-slate-100 overflow-x-auto text-slate-700 font-mono">
                            {JSON.stringify(diag.progress_assessment, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    )}

                    {/* Support Assessment */}
                    {diag.support_assessment && (
                      <Card className="shadow-none border-slate-200">
                        <CardHeader className="p-3 pb-1">
                          <CardTitle className="text-xs font-semibold text-slate-800">
                            Support Assessment (Cycle 5)
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-3 pt-1">
                          <pre className="text-[10px] p-2 bg-white rounded border border-slate-100 overflow-x-auto text-slate-700 font-mono">
                            {JSON.stringify(diag.support_assessment, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    )}

                    {/* Action Context */}
                    {diag.action_context && diag.action_context.length > 0 && (
                      <Card className="shadow-none border-slate-200">
                        <CardHeader className="p-3 pb-1">
                          <CardTitle className="text-xs font-semibold text-slate-800">
                            Active Coaching Commitments
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-3 pt-1 space-y-1.5">
                          {diag.action_context.map((act, i) => (
                            <div key={i} className="p-2 bg-white rounded border border-slate-100">
                              <p className="font-medium text-slate-800">{String(act.action_title || act.title || `Action ${i+1}`)}</p>
                              {Boolean(act.status) && <p className="text-[10px] text-slate-500">Status: {String(act.status)}</p>}
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}

                    {/* RAG Dual Scope Knowledge Sources */}
                    {diag.rag_sources && diag.rag_sources.length > 0 && (
                      <Card className="shadow-none border-slate-200">
                        <CardHeader className="p-3 pb-1">
                          <CardTitle className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                            <BookOpen className="size-3.5" />
                            Retrieved Vector Context ({diag.rag_sources.length})
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-3 pt-1 space-y-1.5">
                          {diag.rag_sources.map((src, i) => (
                            <div key={i} className="p-2 bg-white rounded border border-slate-100 text-[11px]">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-slate-800 truncate max-w-[180px]">
                                  {src.title || "Document"}
                                </span>
                                <Badge variant="outline" className="text-[9px] px-1 py-0 h-4">
                                  {src.scope === "global_playbook" ? "Playbook" : "Client Episodic"}
                                </Badge>
                              </div>
                              {src.similarity !== undefined && (
                                <p className="text-[10px] text-slate-400 mt-1">
                                  Similarity: {(src.similarity * 100).toFixed(1)}%
                                </p>
                              )}
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}
                  </div>
                );
              })()
            )}
          </div>
        </div>
      )}
    </div>
  );
}
