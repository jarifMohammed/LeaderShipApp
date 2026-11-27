"use client";

import { ArrowLeft, Layers, MessageSquare, UserCheck } from "lucide-react";
import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DashboardShell } from "@/features/dashboard/components/DashboardShell";
import { useClientDossier } from "../hooks/useCoachWorkspace";
import { AdminChatInspector } from "./AdminChatInspector";
import { ClientDossierView } from "./ClientDossierView";
import { CoachSessionsManager } from "./CoachSessionsManager";

export function CoachWorkspacePage({ userId }: { userId: string | number }) {
  const { data: dossier } = useClientDossier(userId);

  const clientName = dossier?.full_name || `Client #${userId}`;
  const clientEmail = dossier?.email || "";

  return (
    <DashboardShell title="Coach Supervision Workspace">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <Link
              href="/dashboard/users"
              className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition-colors"
            >
              <ArrowLeft className="size-3.5" />
              Back to Users Directory
            </Link>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-[#023337] tracking-tight">{clientName}</h1>
              <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-0.5 rounded-full font-mono">
                {clientEmail}
              </span>
            </div>
          </div>
        </div>

        {/* Supervision Tabs */}
        <Tabs defaultValue="dossier" className="w-full">
          <TabsList className="bg-slate-100/80 p-1 border border-slate-200">
            <TabsTrigger value="dossier" className="text-xs data-[state=active]:bg-[#023337] data-[state=active]:text-white gap-2">
              <UserCheck className="size-3.5" />
              Client 360° Overview
            </TabsTrigger>
            <TabsTrigger value="sessions" className="text-xs data-[state=active]:bg-[#023337] data-[state=active]:text-white gap-2">
              <Layers className="size-3.5" />
              Human Coaching Sessions
            </TabsTrigger>
            <TabsTrigger value="inspector" className="text-xs data-[state=active]:bg-[#023337] data-[state=active]:text-white gap-2">
              <MessageSquare className="size-3.5" />
              Full AI Chat History & Coach X-Ray
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dossier" className="mt-6">
            <ClientDossierView userId={userId} />
          </TabsContent>

          <TabsContent value="sessions" className="mt-6">
            <CoachSessionsManager userId={userId} />
          </TabsContent>

          <TabsContent value="inspector" className="mt-6">
            <AdminChatInspector userId={userId} />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardShell>
  );
}
