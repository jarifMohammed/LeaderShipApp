"use client";

import { DollarSign, Layers, Sparkles, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ManagerObservabilitySummary } from "../types";

export function UnitEconomicsRow({
  summary,
}: {
  summary: ManagerObservabilitySummary;
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Spend */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Total USD Spend
            </CardTitle>
            <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
              <DollarSign className="size-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              ${summary.total_cost_usd.toFixed(4)}
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Across {summary.total_turns} coaching turn{summary.total_turns === 1 ? "" : "s"}
            </p>
          </CardContent>
        </Card>

        {/* Avg Cost Per Turn */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Avg Cost / Turn
            </CardTitle>
            <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
              <TrendingUp className="size-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              ${summary.avg_cost_per_turn_usd.toFixed(5)}
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Deterministic OpenAI pricing model
            </p>
          </CardContent>
        </Card>

        {/* Total Token Consumption */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Total Token Burn
            </CardTitle>
            <div className="rounded-lg bg-amber-50 p-2 text-amber-600">
              <Sparkles className="size-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              {summary.total_tokens.toLocaleString()}
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              {summary.total_prompt_tokens.toLocaleString()} in / {summary.total_completion_tokens.toLocaleString()} out
            </p>
          </CardContent>
        </Card>

        {/* Total Turns */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Completed Turns
            </CardTitle>
            <div className="rounded-lg bg-purple-50 p-2 text-purple-600">
              <Layers className="size-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              {summary.total_turns.toLocaleString()}
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Live Socratic chat sessions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Active Model Usage Breakdown */}
      {summary.models && summary.models.length > 0 && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="py-3 px-4 border-b border-slate-100">
            <CardTitle className="text-xs font-semibold text-slate-800 uppercase tracking-wider">
              Active Model Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {summary.models.map((m) => (
                <div
                  key={m.model_name}
                  className="rounded-lg border border-slate-200 bg-slate-50/50 p-3 text-xs"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-semibold text-slate-900 font-mono text-[11px]">
                      {m.model_name}
                    </span>
                    <Badge variant="outline" className="text-[10px] bg-white">
                      {m.turn_count} turn{m.turn_count === 1 ? "" : "s"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-slate-500 text-[11px]">
                    <span>Spend:</span>
                    <span className="font-medium text-slate-800">
                      ${m.total_cost_usd.toFixed(4)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-500 text-[11px] mt-0.5">
                    <span>Tokens:</span>
                    <span className="font-mono text-slate-700">
                      {m.total_tokens.toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

