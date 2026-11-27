"use client";

import { useState } from "react";
import {
  Brain,
  CheckCircle2,
  Clock,
  Edit3,
  FileText,
  History,
  Plus,
  Save,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  useClientDossier,
  useCreateGoal,
  useUpdateDossier,
  useUpdateGoal,
} from "../hooks/useCoachWorkspace";
import type { ClientGoal, GoalStatus, ReadinessStage } from "../types";

const statusColors: Record<GoalStatus, string> = {
  exploring: "bg-amber-100 text-amber-800 border-amber-200",
  committed: "bg-blue-100 text-blue-800 border-blue-200",
  in_progress: "bg-emerald-100 text-emerald-800 border-emerald-200",
  completed: "bg-purple-100 text-purple-800 border-purple-200",
  stalled: "bg-rose-100 text-rose-800 border-rose-200",
};

const readinessColors: Record<string, string> = {
  precontemplation: "bg-slate-100 text-slate-700",
  contemplation: "bg-orange-100 text-orange-800",
  preparation: "bg-indigo-100 text-indigo-800",
  action: "bg-teal-100 text-teal-800",
  maintenance: "bg-emerald-100 text-emerald-800",
};

export function ClientDossierView({ userId }: { userId: string | number }) {
  const { data: dossier, isLoading, isError, refetch } = useClientDossier(userId);
  const updateDossier = useUpdateDossier(userId);
  const createGoal = useCreateGoal(userId);
  const updateGoal = useUpdateGoal(userId);

  // Private notes state
  const [coachNotes, setCoachNotes] = useState<string | null>(null);
  const [isEditingNotes, setIsEditingNotes] = useState(false);

  // Goal creation dialog state
  const [isAddGoalOpen, setIsAddGoalOpen] = useState(false);
  const [newGoalTitle, setNewGoalTitle] = useState("");
  const [newGoalDesc, setNewGoalDesc] = useState("");
  const [newGoalStatus, setNewGoalStatus] = useState<GoalStatus>("committed");
  const [newGoalReadiness, setNewGoalReadiness] = useState<ReadinessStage>("preparation");

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-500">
        <Clock className="mr-2 size-5 animate-spin" />
        Loading executive dossier...
      </div>
    );
  }

  if (isError || !dossier) {
    return (
      <div className="p-8 text-center">
        <p className="text-rose-600 mb-3">Unable to load client executive dossier.</p>
        <Button variant="outline" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  const { profile, goals, recent_events, stats } = dossier;
  const currentNotes = coachNotes !== null ? coachNotes : profile?.coach_private_notes || "";

  const handleSaveNotes = async () => {
    await updateDossier.mutateAsync({ coach_private_notes: currentNotes });
    setIsEditingNotes(false);
  };

  const handleCreateGoalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGoalTitle.trim()) return;
    await createGoal.mutateAsync({
      title: newGoalTitle.trim(),
      description: newGoalDesc.trim() || undefined,
      status: newGoalStatus,
      readiness_stage: newGoalReadiness,
    });
    setNewGoalTitle("");
    setNewGoalDesc("");
    setIsAddGoalOpen(false);
  };

  const handleStatusChange = async (goalId: string, newStatus: GoalStatus) => {
    await updateGoal.mutateAsync({
      goalId,
      data: { status: newStatus },
    });
  };

  const stakeholderMap = (profile?.stakeholder_map || {}) as Record<string, unknown>;
  const patterns = (profile?.leadership_style_and_patterns || {}) as Record<string, unknown>;

  return (
    <div className="space-y-6">
      {/* Metric Highlights */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card className="bg-slate-50/50">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold text-slate-500">
              Active Goals
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-[#023337]">
              {stats.active_goals ?? goals.filter((g) => g.status !== "completed").length}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card className="bg-slate-50/50">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold text-slate-500">
              Completed Goals
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-emerald-600">
              {stats.completed_goals ?? goals.filter((g) => g.status === "completed").length}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card className="bg-slate-50/50">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold text-slate-500">
              Coaching Sessions
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-[#023337]">
              {stats.total_sessions ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card className="bg-slate-50/50">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold text-slate-500">
              Knowledge Events
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-[#023337]">
              {recent_events?.length ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Row 1: Executive Summary & Coach Private Notes */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="size-5 text-[#023337]" />
              <CardTitle className="text-base font-semibold text-[#023337]">
                360° Executive Dossier
              </CardTitle>
            </div>
            <Badge variant="outline" className="text-xs font-normal">
              Profile v{profile?.version || 1}
            </Badge>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-wrap">
              {profile?.executive_summary ||
                "No executive dossier generated yet. As the client chats with Jess or human coaching session transcripts are uploaded, longitudinal facts will automatically compile here."}
            </p>
          </CardContent>
        </Card>

        {/* Coach Private Notes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div className="flex items-center gap-2">
              <FileText className="size-5 text-[#023337]" />
              <CardTitle className="text-base font-semibold text-[#023337]">
                Coach Private Notes (Confidential)
              </CardTitle>
            </div>
            {isEditingNotes ? (
              <Button
                size="sm"
                className="bg-[#023337] hover:bg-[#023337]/90 text-white"
                onClick={handleSaveNotes}
                disabled={updateDossier.isPending}
              >
                <Save className="mr-1.5 size-3.5" />
                {updateDossier.isPending ? "Saving..." : "Save"}
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setCoachNotes(profile?.coach_private_notes || "");
                  setIsEditingNotes(true);
                }}
              >
                <Edit3 className="mr-1.5 size-3.5" />
                Edit
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {isEditingNotes ? (
              <Textarea
                rows={5}
                value={currentNotes}
                onChange={(e) => setCoachNotes(e.target.value)}
                placeholder="Write private observations, supervisor notes, or strategic coaching hypotheses..."
                className="text-sm"
              />
            ) : (
              <p className="text-sm text-slate-700 whitespace-pre-wrap min-h-[96px]">
                {profile?.coach_private_notes || (
                  <span className="italic text-slate-400">
                    No coach private notes recorded. Click Edit to add notes visible only to coaches.
                  </span>
                )}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Stakeholder Map & Leadership Patterns */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Stakeholder Map */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Users className="size-5 text-[#023337]" />
              <CardTitle className="text-base font-semibold text-[#023337]">
                Stakeholder Map & Interpersonal Dynamics
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {Object.keys(stakeholderMap).length > 0 ? (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {Object.entries(stakeholderMap).map(([name, detail]) => (
                  <div
                    key={name}
                    className="rounded-lg border border-slate-200 bg-slate-50/50 p-3 text-sm"
                  >
                    <p className="font-semibold text-slate-900">{name}</p>
                    <p className="mt-1 text-xs text-slate-600">
                      {typeof detail === "object" ? JSON.stringify(detail) : String(detail)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">
                Stakeholder dynamics will automatically be detected as the client explores workplace
                scenarios in coaching conversations.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Leadership Style & Patterns */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Brain className="size-5 text-[#023337]" />
              <CardTitle className="text-base font-semibold text-[#023337]">
                Observed Leadership Patterns & Blind Spots
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {Object.keys(patterns).length > 0 ? (
              <div className="space-y-2">
                {Object.entries(patterns).map(([patternKey, detail]) => (
                  <div
                    key={patternKey}
                    className="flex items-start gap-2.5 rounded-lg border border-slate-100 bg-slate-50/50 p-2.5 text-sm"
                  >
                    <CheckCircle2 className="mt-0.5 size-4 text-[#023337] shrink-0" />
                    <div>
                      <span className="font-semibold text-slate-800 capitalize">
                        {patternKey.replace(/_/g, " ")}:
                      </span>{" "}
                      <span className="text-slate-600 text-xs">
                        {typeof detail === "object" ? JSON.stringify(detail) : String(detail)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">
                Cognitive and behavioral patterns will populate as Socratic exploration deepens.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Longitudinal Goals & Commitments */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <div className="flex items-center gap-2">
              <Target className="size-5 text-[#023337]" />
              <CardTitle className="text-base font-semibold text-[#023337]">
                Longitudinal Goals & Commitments
              </CardTitle>
            </div>
            <CardDescription className="text-xs mt-1">
              Persistent executive objectives tracked across AI conversations and human coaching sessions.
            </CardDescription>
          </div>

          <Dialog open={isAddGoalOpen} onOpenChange={setIsAddGoalOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="bg-[#023337] hover:bg-[#023337]/90 text-white">
                <Plus className="mr-1.5 size-4" />
                Add Goal
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[480px]">
              <form onSubmit={handleCreateGoalSubmit}>
                <DialogHeader>
                  <DialogTitle>Add Longitudinal Goal</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="goal-title">Goal Title</Label>
                    <Input
                      id="goal-title"
                      placeholder="e.g. Master executive boundary setting with VP Engineering"
                      value={newGoalTitle}
                      onChange={(e) => setNewGoalTitle(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="goal-desc">Description</Label>
                    <Textarea
                      id="goal-desc"
                      placeholder="Desired leadership outcome, success criteria, or context..."
                      rows={3}
                      value={newGoalDesc}
                      onChange={(e) => setNewGoalDesc(e.target.value)}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label>Initial Status</Label>
                      <Select
                        value={newGoalStatus}
                        onValueChange={(v) => setNewGoalStatus(v as GoalStatus)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="exploring">Exploring</SelectItem>
                          <SelectItem value="committed">Committed</SelectItem>
                          <SelectItem value="in_progress">In Progress</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Cycle 4/5 Readiness</Label>
                      <Select
                        value={newGoalReadiness}
                        onValueChange={(v) => setNewGoalReadiness(v as ReadinessStage)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="contemplation">Contemplation</SelectItem>
                          <SelectItem value="preparation">Preparation</SelectItem>
                          <SelectItem value="action">Action</SelectItem>
                          <SelectItem value="maintenance">Maintenance</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="submit"
                    className="bg-[#023337] text-white"
                    disabled={createGoal.isPending}
                  >
                    {createGoal.isPending ? "Creating..." : "Create Goal"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>

        <CardContent>
          {goals.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500 border border-dashed rounded-lg">
              No longitudinal goals recorded yet. Click &quot;Add Goal&quot; or conduct an AI coaching session.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {goals.map((goal: ClientGoal) => (
                <div key={goal.id} className="py-4 first:pt-0 last:pb-0 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1 max-w-2xl">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="font-semibold text-slate-900 text-sm">{goal.title}</h4>
                      <Badge
                        variant="outline"
                        className={`text-[11px] font-medium capitalize ${statusColors[goal.status]}`}
                      >
                        {goal.status.replace("_", " ")}
                      </Badge>
                      {goal.readiness_stage && (
                        <Badge
                          variant="secondary"
                          className={`text-[10px] capitalize ${readinessColors[goal.readiness_stage] || ""}`}
                        >
                          Readiness: {goal.readiness_stage}
                        </Badge>
                      )}
                      <span className="text-[11px] text-slate-400">
                        via {goal.source_type.replace("_", " ")}
                      </span>
                    </div>
                    {goal.description && (
                      <p className="text-xs text-slate-600">{goal.description}</p>
                    )}
                    {goal.evidence_log && goal.evidence_log.length > 0 && (
                      <div className="mt-2 text-[11px] text-slate-500 bg-slate-50 p-2 rounded border border-slate-100">
                        <span className="font-medium">Latest Evidence: </span>
                        &ldquo;{goal.evidence_log[goal.evidence_log.length - 1]?.quote || goal.evidence_log[goal.evidence_log.length - 1]?.observation || "Turn progress"}&rdquo;
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 self-start md:self-auto">
                    <Select
                      value={goal.status}
                      onValueChange={(val) => handleStatusChange(goal.id, val as GoalStatus)}
                    >
                      <SelectTrigger className="h-8 text-xs w-[130px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="exploring">Exploring</SelectItem>
                        <SelectItem value="committed">Committed</SelectItem>
                        <SelectItem value="in_progress">In Progress</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="stalled">Stalled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Row 4: Auto-Learned Knowledge Timeline */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <History className="size-5 text-[#023337]" />
            <CardTitle className="text-base font-semibold text-[#023337]">
              Auto-Learned Knowledge Timeline
            </CardTitle>
          </div>
          <CardDescription className="text-xs">
            Audit trail of facts, patterns, and goal updates extracted automatically by background workers or edited by coaches.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!recent_events || recent_events.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No knowledge audit events logged yet.</p>
          ) : (
            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {recent_events.map((evt) => (
                <div key={evt.id} className="relative text-xs">
                  <span className="absolute -left-6 top-1 size-2 rounded-full bg-[#023337]" />
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800">
                      [{evt.source_type.replace(/_/g, " ").toUpperCase()}]
                    </span>
                    <span className="text-slate-400">
                      {evt.created_at ? new Date(evt.created_at).toLocaleString() : ""}
                    </span>
                  </div>
                  <p className="mt-0.5 text-slate-600 font-medium">{evt.diff_summary}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
