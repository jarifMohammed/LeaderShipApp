"use client";

import { UserCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { UserCostBreakdown } from "../types";

export function PerClientCostTable({
  users,
}: {
  users: UserCostBreakdown[];
}) {
  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="py-3 px-4 border-b border-slate-100 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <UserCheck className="size-4 text-[#023337]" />
          <CardTitle className="text-xs font-semibold text-slate-800 uppercase tracking-wider">
            Per-Client Unit Economics & Token Burn
          </CardTitle>
        </div>
        <span className="text-[11px] text-slate-400">
          {users.length} Active Coachee{users.length === 1 ? "" : "s"}
        </span>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-500 font-medium border-b border-slate-100">
              <tr>
                <th className="py-2.5 px-4">Client</th>
                <th className="py-2.5 px-4">Email</th>
                <th className="py-2.5 px-4 text-right">Turns</th>
                <th className="py-2.5 px-4 text-right">Total Tokens</th>
                <th className="py-2.5 px-4 text-right">Total Spend (USD)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400 italic">
                    No client usage data recorded yet
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.user_id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-900">
                      {u.user_name}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {u.user_email}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {u.turn_count}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {u.total_tokens.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-700">
                      ${u.total_cost_usd.toFixed(4)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

