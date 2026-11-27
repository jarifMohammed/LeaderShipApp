"use client";

import { useRef, useState } from "react";
import {
  AlertCircle,
  FileAudio,
  FileCode,
  FileText,
  Loader2,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import {
  useCoachSessions,
  useUploadCoachSession,
} from "../hooks/useCoachWorkspace";
import type { CoachSession, SessionProcessingStatus } from "../types";

const statusConfig: Record<
  SessionProcessingStatus,
  { label: string; color: string; spinning?: boolean }
> = {
  queued: { label: "Queued", color: "bg-slate-100 text-slate-700" },
  transcribing: {
    label: "Transcribing Audio...",
    color: "bg-amber-100 text-amber-800 border-amber-200",
    spinning: true,
  },
  extracting: {
    label: "Extracting Knowledge...",
    color: "bg-blue-100 text-blue-800 border-blue-200",
    spinning: true,
  },
  indexing: {
    label: "Vector Indexing...",
    color: "bg-indigo-100 text-indigo-800 border-indigo-200",
    spinning: true,
  },
  completed: {
    label: "Completed & Indexed",
    color: "bg-emerald-100 text-emerald-800 border-emerald-200",
  },
  failed: {
    label: "Failed",
    color: "bg-rose-100 text-rose-800 border-rose-200",
  },
};

export function CoachSessionsManager({ userId }: { userId: string | number }) {
  const { data: sessions, isLoading, isError, refetch } = useCoachSessions(userId);
  const uploadSession = useUploadCoachSession(userId);

  // Upload dialog state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [sessionDate, setSessionDate] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Inspect drawer state
  const [inspectedSession, setInspectedSession] = useState<CoachSession | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (!title) {
        setTitle(file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " "));
      }
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !title.trim()) return;

    await uploadSession.mutateAsync({
      file: selectedFile,
      title: title.trim(),
      sessionDate: sessionDate || undefined,
    });

    setSelectedFile(null);
    setTitle("");
    setSessionDate("");
    setIsUploadOpen(false);
  };

  const getFileIcon = (fileType: string) => {
    if (["mp3", "wav", "m4a", "audio"].includes(fileType.toLowerCase())) {
      return <FileAudio className="size-5 text-amber-600" />;
    }
    if (["pdf", "docx", "doc", "txt"].includes(fileType.toLowerCase())) {
      return <FileText className="size-5 text-[#023337]" />;
    }
    return <FileCode className="size-5 text-slate-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Header and Upload action */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-4">
          <div>
            <CardTitle className="text-base font-semibold text-[#023337]">
              Human Executive Coaching Sessions
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              Upload recordings (.mp3, .wav, .m4a) or notes/transcripts (.pdf, .docx, .txt, .vtt).
              Background workers transcribe audio and extract executive goals and patterns into the client&apos;s vector memory.
            </CardDescription>
          </div>

          <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="bg-[#023337] hover:bg-[#023337]/90 text-white">
                <UploadCloud className="mr-1.5 size-4" />
                Upload Session
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <form onSubmit={handleUploadSubmit}>
                <DialogHeader>
                  <DialogTitle>Upload Coaching Session</DialogTitle>
                  <DialogDescription className="text-xs">
                    Audio files will be automatically transcribed via OpenAI Whisper and analyzed.
                  </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="session-file">Session File (Audio or Document)</Label>
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <input
                        ref={fileInputRef}
                        id="session-file"
                        type="file"
                        accept=".mp3,.wav,.m4a,.pdf,.docx,.txt,.vtt"
                        className="hidden"
                        onChange={handleFileChange}
                      />
                      <UploadCloud className="mx-auto size-8 text-slate-400 mb-2" />
                      {selectedFile ? (
                        <p className="text-sm font-medium text-slate-800">
                          {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                        </p>
                      ) : (
                        <div>
                          <p className="text-sm font-medium text-slate-700">
                            Click to select audio recording or transcript
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            Supports MP3, WAV, M4A, PDF, DOCX, TXT, VTT
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="session-title">Session Title</Label>
                    <Input
                      id="session-title"
                      placeholder="e.g. Session 4: Executive Alignment with Board"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="session-date">Session Date (Optional)</Label>
                    <Input
                      id="session-date"
                      type="date"
                      value={sessionDate}
                      onChange={(e) => setSessionDate(e.target.value)}
                    />
                  </div>
                </div>

                <DialogFooter>
                  <Button
                    type="submit"
                    className="bg-[#023337] text-white"
                    disabled={!selectedFile || !title.trim() || uploadSession.isPending}
                  >
                    {uploadSession.isPending ? (
                      <>
                        <Loader2 className="mr-1.5 size-4 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      "Upload & Process"
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="flex h-40 items-center justify-center text-slate-500">
              <Loader2 className="mr-2 size-5 animate-spin" />
              Loading sessions...
            </div>
          ) : isError ? (
            <div className="p-8 text-center">
              <p className="text-rose-600 mb-2">Failed to load coach sessions.</p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <div className="p-12 text-center border border-dashed rounded-lg">
              <UploadCloud className="mx-auto size-10 text-slate-300 mb-3" />
              <p className="text-sm font-medium text-slate-700">No human coaching sessions uploaded yet</p>
              <p className="text-xs text-slate-500 mt-1">
                Upload session audio recordings or notes to enrich Jess with 360° human coaching continuity.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {sessions.map((sess) => {
                const conf = statusConfig[sess.processing_status] || {
                  label: sess.processing_status,
                  color: "bg-slate-100 text-slate-700",
                };
                return (
                  <div
                    key={sess.id}
                    className="py-4 first:pt-0 last:pb-0 flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-1 p-2 rounded-lg bg-slate-50 border border-slate-100">
                        {getFileIcon(sess.file_type)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-slate-900 text-sm">{sess.title}</h4>
                          <Badge
                            variant="outline"
                            className={`text-[11px] font-medium flex items-center gap-1 ${conf.color}`}
                          >
                            {conf.spinning && <Loader2 className="size-3 animate-spin" />}
                            {conf.label}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                          <span>Format: {sess.file_type.toUpperCase()}</span>
                          {sess.session_date && (
                            <span>
                              Date: {new Date(sess.session_date).toLocaleDateString()}
                            </span>
                          )}
                          <span>
                            Uploaded: {sess.created_at ? new Date(sess.created_at).toLocaleDateString() : ""}
                          </span>
                        </div>

                        {sess.extracted_summary && (
                          <p className="text-xs text-slate-600 mt-2 line-clamp-2 max-w-2xl">
                            {sess.extracted_summary}
                          </p>
                        )}

                        {sess.error_message && (
                          <div className="mt-2 flex items-center gap-1.5 text-xs text-rose-600">
                            <AlertCircle className="size-3.5 shrink-0" />
                            <span>{sess.error_message}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setInspectedSession(sess)}
                        disabled={sess.processing_status !== "completed" && !sess.raw_transcript}
                      >
                        Inspect Facts & Transcript
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Inspect Session Sheet */}
      <Sheet open={Boolean(inspectedSession)} onOpenChange={(open) => !open && setInspectedSession(null)}>
        <SheetContent className="sm:max-w-2xl overflow-y-auto">
          {inspectedSession && (
            <>
              <SheetHeader>
                <div className="flex items-center gap-2">
                  {getFileIcon(inspectedSession.file_type)}
                  <SheetTitle className="text-lg font-bold text-[#023337]">
                    {inspectedSession.title}
                  </SheetTitle>
                </div>
                <SheetDescription className="text-xs">
                  Processed on {inspectedSession.created_at ? new Date(inspectedSession.created_at).toLocaleString() : ""}
                </SheetDescription>
              </SheetHeader>

              <div className="mt-6 space-y-6">
                {/* Executive Summary */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase text-slate-500 tracking-wider flex items-center gap-1.5">
                    <Sparkles className="size-3.5 text-[#023337]" />
                    Extracted Coaching Summary
                  </h4>
                  <div className="rounded-lg bg-slate-50 p-3.5 text-xs text-slate-700 leading-relaxed border border-slate-100">
                    {inspectedSession.extracted_summary || "No summary extracted."}
                  </div>
                </div>

                {/* Extracted Facts */}
                {inspectedSession.extracted_facts && Object.keys(inspectedSession.extracted_facts).length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase text-slate-500 tracking-wider">
                      Extracted Knowledge Facts
                    </h4>
                    <pre className="text-[11px] p-3 rounded-lg bg-slate-900 text-slate-100 overflow-x-auto">
                      {JSON.stringify(inspectedSession.extracted_facts, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Speaker Transcript */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase text-slate-500 tracking-wider flex items-center gap-1.5">
                    <FileText className="size-3.5 text-[#023337]" />
                    Full Speaker Transcript
                  </h4>
                  <div className="rounded-lg border border-slate-200 bg-white p-4 max-h-[360px] overflow-y-auto text-xs text-slate-800 font-mono whitespace-pre-wrap leading-relaxed">
                    {inspectedSession.raw_transcript || "Transcript not available."}
                  </div>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
