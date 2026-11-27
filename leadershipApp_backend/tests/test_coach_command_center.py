import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.user import User
from app.schemas.coach_command import GoalCreateRequest, GoalUpdateRequest, AdminDossierUpdateRequest
from app.api.v1.admin.coach_command_center import (
    get_client_dossier,
    update_client_dossier,
    create_client_goal,
    update_client_goal,
    list_coach_sessions,
    list_user_conversations_for_admin,
)


class CoachCommandCenterEndpointTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.admin_user = User(
            id=1,
            email="admin@example.com",
            full_name="Admin Coach",
            role="admin",
            is_active=True,
        )

    async def test_create_and_update_client_goal_schemas(self):
        create_req = GoalCreateRequest(
            title="Master delegation with VP of Product",
            description="Clear ownership matrix and weekly check-in",
            status="committed",
            readiness_stage="preparation",
        )
        self.assertEqual(create_req.title, "Master delegation with VP of Product")
        self.assertEqual(create_req.status, "committed")

        update_req = GoalUpdateRequest(
            status="in_progress",
            readiness_stage="action",
            evidence_quote="Delegated the Q3 roadmap review successfully",
        )
        self.assertEqual(update_req.status, "in_progress")
        self.assertEqual(update_req.readiness_stage, "action")

    async def test_update_client_dossier_schema(self):
        dossier_req = AdminDossierUpdateRequest(
            executive_summary="Executive coaching focused on executive presence and managing upwards.",
            coach_private_notes="Client is responsive to Socratic questions about stakeholder trust.",
        )
        self.assertIn("executive presence", dossier_req.executive_summary)
        self.assertIn("Socratic questions", dossier_req.coach_private_notes)


if __name__ == "__main__":
    unittest.main()
