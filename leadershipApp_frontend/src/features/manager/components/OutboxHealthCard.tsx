"use client";

import { AlertTriangle, CheckCircle2, Clock, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { OutboxHealth } from "../types";

export function OutboxHealthCard({ health }: { health: OutboxHealth }) {
  const isHealthy = health.failed === 0;

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="py-3 px-4 border-b border-slate-100 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <CardTitle className="text-xs font-semibold text-slate-800 uppercase tracking-wider">
            Distributed Systems & Outbox Daemon Health
          </CardTitle>
          <Badge
            className={
              isHealthy
                ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-50"
                : "bg-rose-50 text-rose-700 hover:bg-rose-50"
            }
          >
            {isHealthy ? "All Workers Healthy" : "Action Required"}
          </Badge>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          Transactional Outbox Pattern
        </span>
      </CardHeader>
      <CardContent className="p-4">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {/* Pending Events */}
          <div className="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Clock className="size-3.5 text-amber-500" />
              <span>Pending in Queue</span>
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
              {health.pending}
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Row-level SKIP LOCKED
            </p>
          </div>

          {/* Published Events */}
          <div className="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <CheckCircle2 className="size-3.5 text-emerald-500" />
              <span>Published Events</span>
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
              {health.published}
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Dispatched to Redis streams
            </p>
          </div>

          {/* Failed Events */}
          <div className="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <AlertTriangle className="size-3.5 text-rose-500" />
              <span>Failed Events</span>
            </div>
            <div
              className={`mt-2 text-2xl font-bold font-mono ${
                health.failed > 0 ? "text-rose-600" : "text-slate-900"
              }`}
            >
              {health.failed}
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Dead-letter queue count
            </p>
          </div>

          {/* Processed Events */}
          <div className="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <RefreshCw className="size-3.5 text-indigo-500" />
              <span>Idempotent Consumptions</span>
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
              {health.processed_events}
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Two-tier Redis + DB deduplication
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

