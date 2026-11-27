import { api } from "@/lib/api";
import {
  getClientDossier,
  updateClientDossier,
  createClientGoal,
  getCoachSessions,
  getClientConversations,
  getConversationMessages,
} from "./coach-workspace.api";

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
  },
}));

describe("coach-workspace API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches client dossier with profile, goals, and stats", async () => {
    const mockDossier = {
      user_id: 12,
      full_name: "Sarah Connors",
      email: "sarah@example.com",
      profile: {
        user_id: 12,
        executive_summary: "VP Engineering navigating team scaling",
        leadership_style_and_patterns: {},
        stakeholder_map: {},
        coach_private_notes: "Strong focus on autonomous delivery",
        version: 2,
      },
      goals: [
        {
          id: "goal-1",
          user_id: 12,
          title: "Scale engineering hiring",
          status: "committed",
          readiness_stage: "action",
          source_type: "coach_session",
          evidence_log: [],
        },
      ],
      recent_events: [],
      stats: { total_goals: 1, active_goals: 1, completed_goals: 0 },
    };

    jest.mocked(api.get).mockResolvedValueOnce({ data: mockDossier });

    const dossier = await getClientDossier(12);
    expect(api.get).toHaveBeenCalledWith("/admin/users/12/dossier");
    expect(dossier.user_id).toBe(12);
    expect(dossier.goals[0].title).toBe("Scale engineering hiring");
  });

  it("updates client dossier notes and summary", async () => {
    const mockUpdated = {
      user_id: 12,
      full_name: "Sarah Connors",
      email: "sarah@example.com",
      profile: {
        user_id: 12,
        executive_summary: "Updated summary",
        leadership_style_and_patterns: {},
        stakeholder_map: {},
        coach_private_notes: "New coach notes",
        version: 3,
      },
      goals: [],
      recent_events: [],
      stats: {},
    };

    jest.mocked(api.patch).mockResolvedValueOnce({ data: mockUpdated });

    const result = await updateClientDossier(12, {
      coach_private_notes: "New coach notes",
    });
    expect(api.patch).toHaveBeenCalledWith("/admin/users/12/dossier", {
      coach_private_notes: "New coach notes",
    });
    expect(result.profile.coach_private_notes).toBe("New coach notes");
  });

  it("creates a client goal", async () => {
    const mockGoal = {
      id: "goal-99",
      user_id: 12,
      title: "Master Socratic delegation",
      status: "committed",
      readiness_stage: "preparation",
      source_type: "admin_manual",
      evidence_log: [],
    };

    jest.mocked(api.post).mockResolvedValueOnce({ data: mockGoal });

    const result = await createClientGoal(12, {
      title: "Master Socratic delegation",
      status: "committed",
      readiness_stage: "preparation",
    });
    expect(api.post).toHaveBeenCalledWith("/admin/users/12/goals", {
      title: "Master Socratic delegation",
      status: "committed",
      readiness_stage: "preparation",
    });
    expect(result.id).toBe("goal-99");
  });

  it("fetches coach sessions with status badges", async () => {
    const mockSessions = [
      {
        id: "sess-1",
        user_id: 12,
        title: "Session 1: Executive Roadmap",
        file_type: "mp3",
        processing_status: "completed",
        extracted_summary: "Discussed delegation and board alignment",
        extracted_facts: {},
      },
    ];

    jest.mocked(api.get).mockResolvedValueOnce({ data: mockSessions });

    const sessions = await getCoachSessions(12);
    expect(api.get).toHaveBeenCalledWith("/admin/users/12/coach-sessions");
    expect(sessions[0].processing_status).toBe("completed");
  });

  it("fetches conversation messages with turn_diagnostics", async () => {
    const mockMessages = [
      {
        id: "msg-1",
        role: "user",
        content: "What should I do about Bob?",
      },
      {
        id: "msg-2",
        role: "assistant",
        content: "When you reflect on past conversations with Bob, what has opened up trust?",
        turn_diagnostics: {
          socratic_stage: "Goal",
          seeks_direct_solution: true,
          enforced_move: "clarify",
        },
      },
    ];

    jest.mocked(api.get).mockResolvedValueOnce({ data: mockMessages });

    const messages = await getConversationMessages("conv-123");
    expect(api.get).toHaveBeenCalledWith("/admin/conversations/conv-123/messages");
    expect(messages[1].turn_diagnostics?.seeks_direct_solution).toBe(true);
  });

  it("fetches client conversations", async () => {
    const mockConvs = [{ id: "conv-1", title: "Leadership Strategy" }];
    jest.mocked(api.get).mockResolvedValueOnce({ data: mockConvs });

    const convs = await getClientConversations(12);
    expect(api.get).toHaveBeenCalledWith("/admin/users/12/conversations");
    expect(convs[0].title).toBe("Leadership Strategy");
  });
});

