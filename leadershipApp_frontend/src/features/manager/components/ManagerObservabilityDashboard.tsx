"use client";

import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useManagerObservabilitySummary,
  useManagerTraces,
} from "../hooks/useManagerObservability";
import { LatencySpansRow } from "./LatencySpansRow";
import { LiveTraceInspectorTable } from "./LiveTraceInspectorTable";
import { OutboxHealthCard } from "./OutboxHealthCard";
import { PerClientCostTable } from "./PerClientCostTable";
import { UnitEconomicsRow } from "./UnitEconomicsRow";

export function ManagerObservabilityDashboard() {
  const {
    data: summary,
    isLoading: loadingSummary,
    isError: errorSummary,
    refetch: refetchSummary,
  } = useManagerObservabilitySummary();

  const {
    data: tracesData,
    refetch: refetchTraces,
  } = useManagerTraces(50, 0);

  const handleRefresh = () => {
    void refetchSummary();
    void refetchTraces();
  };

  if (loadingSummary && !summary) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 rounded-xl bg-slate-100" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="h-24 rounded-xl bg-slate-100" />
          <div className="h-24 rounded-xl bg-slate-100" />
          <div className="h-24 rounded-xl bg-slate-100" />
          <div className="h-24 rounded-xl bg-slate-100" />
        </div>
        <div className="h-64 rounded-xl bg-slate-100" />
      </div>
    );
  }

  if (errorSummary && !summary) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800">
        <AlertCircle className="mx-auto size-8 text-rose-600 mb-2" />
        <h3 className="font-semibold text-base">Failed to load platform observability metrics</h3>
        <p className="text-xs text-rose-600 mt-1">
          Verify MANAGER authentication credentials and backend API health.
        </p>
        <Button
          onClick={handleRefresh}
          variant="outline"
          size="sm"
          className="mt-4 bg-white"
        >
          <RefreshCw className="size-3.5 mr-1.5" /> Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner / Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#023337] text-white p-5 rounded-xl shadow-sm">
        <div>
          <h2 className="text-lg font-bold">
            Platform Observability & Unit Economics
          </h2>
          <p className="text-xs text-slate-300 mt-0.5">
            Real-time financial telemetry, span latencies, and distributed outbox health
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleRefresh}
            variant="outline"
            size="sm"
            className="text-xs bg-white/10 hover:bg-white/20 text-white border-white/20 gap-1.5"
          >
            <RefreshCw className="size-3.5" />
            Refresh Telemetry
          </Button>
        </div>
      </div>

      {/* Row 1: Financial & Unit Economics */}
      {summary && <UnitEconomicsRow summary={summary} />}

      {/* Row 2: Latency Spans & Perception */}
      {summary && <LatencySpansRow summary={summary} />}

      {/* Row 3: Outbox Daemon & Worker Health */}
      {summary && <OutboxHealthCard health={summary.outbox_health} />}

      {/* Row 4: Per-Client Unit Economics Table */}
      {summary && <PerClientCostTable users={summary.per_user_cost} />}

      {/* Row 5: Live OpenTelemetry Trace Table */}
      <LiveTraceInspectorTable traces={tracesData?.items || []} />
    </div>
  );
}

