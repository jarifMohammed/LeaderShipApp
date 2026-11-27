import { render, screen } from "@testing-library/react";
import { ManagerObservabilityDashboard } from "./ManagerObservabilityDashboard";
import {
  useManagerObservabilitySummary,
  useManagerTraces,
} from "../hooks/useManagerObservability";

jest.mock("../hooks/useManagerObservability");

const mockSummary = {
  total_cost_usd: 0.1254,
  total_prompt_tokens: 35000,
  total_completion_tokens: 8500,
  total_tokens: 43500,
  total_turns: 12,
  avg_cost_per_turn_usd: 0.01045,
  p50_ttft_ms: 210.5,
  p95_ttft_ms: 450.0,
  p95_context_retrieval_ms: 92.0,
  outbox_health: {
    pending: 0,
    published: 12,
    failed: 0,
    processed_events: 12,
  },
  models: [
    {
      model_name: "gpt-4o",
      turn_count: 10,
      prompt_tokens: 30000,
      completion_tokens: 7500,
      total_tokens: 37500,
      total_cost_usd: 0.12,
    },
  ],
  per_user_cost: [
    {
      user_id: 10,
      user_name: "Alex Coachee",
      user_email: "alex@example.com",
      turn_count: 12,
      total_tokens: 43500,
      total_cost_usd: 0.1254,
    },
  ],
};

const mockTraces = {
  total_count: 1,
  items: [
    {
      message_id: "msg-123",
      conversation_id: "conv-456",
      user_id: 10,
      user_email: "alex@example.com",
      created_at: "2026-11-04T02:00:00Z",
      trace_id: "trace-999",
      traceparent: "00-trace-999-root-01",
      model_name: "gpt-4o",
      tokens: 2500,
      prompt_tokens: 2000,
      completion_tokens: 500,
      cost_usd: 0.01,
      ttft_ms: 210.5,
      total_turn_latency_ms: 980.0,
      spans: [
        {
          name: "span.context_retrieval",
          duration_ms: 92.0,
          status: "OK",
          attributes: { docs_retrieved: 3 },
        },
      ],
    },
  ],
};

describe("ManagerObservabilityDashboard", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    jest.mocked(useManagerObservabilitySummary).mockReturnValue({
      data: mockSummary,
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
    } as unknown as ReturnType<typeof useManagerObservabilitySummary>);

    jest.mocked(useManagerTraces).mockReturnValue({
      data: mockTraces,
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
    } as unknown as ReturnType<typeof useManagerTraces>);
  });

  it("renders platform unit economics, token volume, and USD cost accurately", () => {
    render(<ManagerObservabilityDashboard />);

    expect(screen.getByText("Platform Observability & Unit Economics")).toBeInTheDocument();
    expect(screen.getAllByText("$0.1254").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("$0.01045")).toBeInTheDocument();
    expect(screen.getAllByText("43,500").length).toBeGreaterThanOrEqual(1);
  });

  it("renders latency spans including p50/p95 TTFT and Qdrant retrieval", () => {
    render(<ManagerObservabilityDashboard />);

    expect(screen.getByText("p50 Time-To-First-Token")).toBeInTheDocument();
    expect(screen.getAllByText(/210\.5/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("p95 Time-To-First-Token")).toBeInTheDocument();
    expect(screen.getByText(/450\.0/)).toBeInTheDocument();
    expect(screen.getByText("p95 Qdrant Retrieval")).toBeInTheDocument();
  });

  it("renders outbox daemon health card with zero failures", () => {
    render(<ManagerObservabilityDashboard />);

    expect(
      screen.getByText("Distributed Systems & Outbox Daemon Health"),
    ).toBeInTheDocument();
    expect(screen.getByText("All Workers Healthy")).toBeInTheDocument();
  });

  it("renders live trace inspector with user email and deterministic USD cost", () => {
    render(<ManagerObservabilityDashboard />);

    expect(
      screen.getByText("Live OpenTelemetry Span & Trace Inspector"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("alex@example.com").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("$0.01000")).toBeInTheDocument();
  });
});
