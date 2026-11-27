import { api } from "@/lib/api";
import type {
  ManagerObservabilitySummary,
  ManagerTracesResponse,
} from "../types";

export async function getObservabilitySummary(): Promise<ManagerObservabilitySummary> {
  const response = await api.get<ManagerObservabilitySummary>(
    "/manager/observability/summary",
  );
  return response.data;
}

export async function getRecentTraces(
  limit: number = 50,
  offset: number = 0,
): Promise<ManagerTracesResponse> {
  const response = await api.get<ManagerTracesResponse>(
    "/manager/observability/traces",
    {
      params: { limit, offset },
    },
  );
  return response.data;
}

