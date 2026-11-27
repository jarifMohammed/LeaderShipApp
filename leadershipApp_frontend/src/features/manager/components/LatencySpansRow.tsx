"use client";

import { Clock, Cpu, Gauge } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ManagerObservabilitySummary } from "../types";

export function LatencySpansRow({
  summary,
}: {
  summary: ManagerObservabilitySummary;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {/* p50 TTFT */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            p50 Time-To-First-Token
          </CardTitle>
          <div className="rounded-lg bg-teal-50 p-2 text-teal-600">
            <Clock className="size-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {summary.p50_ttft_ms.toFixed(1)} <span className="text-sm font-sans font-normal text-slate-500">ms</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            Median streaming perception latency
          </p>
        </CardContent>
      </Card>

      {/* p95 TTFT */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            p95 Time-To-First-Token
          </CardTitle>
          <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
            <Gauge className="size-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {summary.p95_ttft_ms.toFixed(1)} <span className="text-sm font-sans font-normal text-slate-500">ms</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            95th percentile worst-case TTFT
          </p>
        </CardContent>
      </Card>

      {/* p95 Qdrant Retrieval */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            p95 Qdrant Retrieval
          </CardTitle>
          <div className="rounded-lg bg-rose-50 p-2 text-rose-600">
            <Cpu className="size-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {summary.p95_context_retrieval_ms.toFixed(1)} <span className="text-sm font-sans font-normal text-slate-500">ms</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            Vector similarity query latency
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

