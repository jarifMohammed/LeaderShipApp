import { useQuery } from "@tanstack/react-query";
import { getObservabilitySummary, getRecentTraces } from "../api/manager.api";

export const managerQueryKeys = {
  summary: ["manager", "observability", "summary"] as const,
  traces: (limit: number, offset: number) =>
    ["manager", "observability", "traces", limit, offset] as const,
};

export function useManagerObservabilitySummary() {
  return useQuery({
    queryKey: managerQueryKeys.summary,
    queryFn: getObservabilitySummary,
    refetchInterval: 10_000, // refresh every 10s for live health
  });
}

export function useManagerTraces(limit: number = 50, offset: number = 0) {
  return useQuery({
    queryKey: managerQueryKeys.traces(limit, offset),
    queryFn: () => getRecentTraces(limit, offset),
    refetchInterval: 10_000,
  });
}

