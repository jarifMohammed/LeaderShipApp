"use client";

import { useState } from "react";
import { Activity, Eye } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ManagerTraceItem } from "../types";

export function LiveTraceInspectorTable({
  traces,
}: {
  traces: ManagerTraceItem[];
}) {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  const selectedTrace = traces.find(
    (t) => (t.trace_id || t.message_id) === selectedTraceId,
  );

  return (
    <div className="space-y-4">
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="py-3 px-4 border-b border-slate-100 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="size-4 text-[#023337]" />
            <CardTitle className="text-xs font-semibold text-slate-800 uppercase tracking-wider">
              Live OpenTelemetry Span & Trace Inspector
            </CardTitle>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            W3C TraceContext (traceparent)
          </span>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-500 font-medium border-b border-slate-100">
                <tr>
                  <th className="py-2.5 px-4">Timestamp</th>
                  <th className="py-2.5 px-4">Client</th>
                  <th className="py-2.5 px-4">Model</th>
                  <th className="py-2.5 px-4 text-right">Tokens (In/Out)</th>
                  <th className="py-2.5 px-4 text-right">Cost (USD)</th>
                  <th className="py-2.5 px-4 text-right">TTFT</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {traces.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-400 italic">
                      No live traces recorded yet
                    </td>
                  </tr>
                ) : (
                  traces.map((trace) => {
                    const rowKey = trace.trace_id || trace.message_id;
                    const isSelected = selectedTraceId === rowKey;

                    return (
                      <tr
                        key={rowKey}
                        onClick={() => setSelectedTraceId(isSelected ? null : rowKey)}
                        className={`cursor-pointer hover:bg-slate-50/70 transition-colors ${
                          isSelected ? "bg-slate-50 font-medium" : ""
                        }`}
                      >
                        <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                          {trace.created_at
                            ? new Date(trace.created_at).toLocaleTimeString()
                            : "Just now"}
                        </td>
                        <td className="py-3 px-4 text-slate-900 truncate max-w-[160px]">
                          {trace.user_email || `User #${trace.user_id}`}
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="outline" className="text-[10px] font-mono bg-white">
                            {trace.model_name || "gpt-4o"}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right font-mono">
                          {trace.tokens !== undefined && trace.tokens !== null
                            ? trace.tokens.toLocaleString()
                            : "—"}
                          {trace.prompt_tokens !== undefined && trace.completion_tokens !== undefined && (
                            <span className="text-[10px] text-slate-400 ml-1">
                              ({trace.prompt_tokens}/{trace.completion_tokens})
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-700">
                          {trace.cost_usd !== undefined && trace.cost_usd !== null
                            ? `$${trace.cost_usd.toFixed(5)}`
                            : "$0.00000"}
                        </td>
                        <td className="py-3 px-4 text-right font-mono">
                          {trace.ttft_ms !== undefined && trace.ttft_ms !== null
                            ? `${trace.ttft_ms.toFixed(1)} ms`
                            : "—"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2 text-xs text-[#023337]"
                          >
                            <Eye className="size-3.5 mr-1" />
                            {isSelected ? "Hide" : "Inspect"}
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Selected Trace Drilldown Inspector */}
      {selectedTrace && (
        <Card className="border-slate-300 shadow-md bg-white">
          <CardHeader className="py-3 px-4 border-b border-slate-100 flex flex-row items-center justify-between bg-slate-50/50">
            <div>
              <CardTitle className="text-xs font-semibold text-[#023337]">
                Trace Details & Span Breakdown
              </CardTitle>
              <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                Traceparent: {selectedTrace.traceparent || `00-${selectedTrace.trace_id}-root-01`}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedTraceId(null)}
              className="text-xs text-slate-500"
            >
              Close
            </Button>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            {/* Top Stats */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
              <div className="p-2.5 rounded border border-slate-100 bg-slate-50/40">
                <span className="text-slate-400 text-[10px] uppercase">Total Cost</span>
                <p className="font-bold font-mono text-emerald-700 mt-0.5">
                  ${selectedTrace.cost_usd?.toFixed(6) || "0.000000"}
                </p>
              </div>
              <div className="p-2.5 rounded border border-slate-100 bg-slate-50/40">
                <span className="text-slate-400 text-[10px] uppercase">Tokens</span>
                <p className="font-bold font-mono text-slate-800 mt-0.5">
                  {selectedTrace.tokens?.toLocaleString() || "0"}
                </p>
              </div>
              <div className="p-2.5 rounded border border-slate-100 bg-slate-50/40">
                <span className="text-slate-400 text-[10px] uppercase">TTFT</span>
                <p className="font-bold font-mono text-slate-800 mt-0.5">
                  {selectedTrace.ttft_ms?.toFixed(1) || "0.0"} ms
                </p>
              </div>
              <div className="p-2.5 rounded border border-slate-100 bg-slate-50/40">
                <span className="text-slate-400 text-[10px] uppercase">Turn Latency</span>
                <p className="font-bold font-mono text-slate-800 mt-0.5">
                  {selectedTrace.total_turn_latency_ms?.toFixed(1) || "0.0"} ms
                </p>
              </div>
            </div>

            {/* Spans List */}
            <div>
              <h4 className="text-xs font-semibold text-slate-700 mb-2">
                Distributed Execution Spans ({selectedTrace.spans.length})
              </h4>
              <div className="space-y-2">
                {selectedTrace.spans.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No child spans recorded for this trace</p>
                ) : (
                  selectedTrace.spans.map((span, idx) => (
                    <div
                      key={idx}
                      className="rounded border border-slate-200 p-2.5 text-xs flex items-center justify-between bg-white"
                    >
                      <div>
                        <span className="font-mono font-semibold text-slate-800">
                          {span.name}
                        </span>
                        {span.attributes && Object.keys(span.attributes).length > 0 && (
                          <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                            {JSON.stringify(span.attributes)}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={
                            span.status === "OK"
                              ? "bg-emerald-50 text-emerald-700 text-[10px]"
                              : "bg-rose-50 text-rose-700 text-[10px]"
                          }
                        >
                          {span.status}
                        </Badge>
                        <span className="font-mono text-xs font-medium text-slate-700">
                          {span.duration_ms.toFixed(1)} ms
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

