import unittest
from app.schemas.coaching import CoachingWorkingState
from app.workflows.chat_workflow import WorkflowNodes


class SocraticGuardAndGROWTests(unittest.TestCase):
    def test_direct_solution_triggers_detected(self):
        triggers = [
            "What should I do in this situation?",
            "Can you write me a script for my 1-on-1?",
            "Just tell me what to do",
            "Give me advice please",
            "What would you say to him?",
            "Make this decision for me",
        ]
        empty_state = CoachingWorkingState()
        for trig in triggers:
            res = WorkflowNodes._evaluate_socratic_guard(trig, empty_state)
            self.assertTrue(
                res["seeks_direct_solution"],
                f"Expected trigger '{trig}' to be detected as seeking direct solution",
            )

    def test_non_directive_inquiry_not_flagged(self):
        queries = [
            "I'm feeling anxious about the upcoming product review.",
            "I noticed my VP of Eng was quiet during the sync.",
            "Let's explore how I handled the feedback session last week.",
            "I want to reflect on my communication patterns.",
        ]
        empty_state = CoachingWorkingState()
        for q in queries:
            res = WorkflowNodes._evaluate_socratic_guard(q, empty_state)
            self.assertFalse(
                res["seeks_direct_solution"],
                f"Expected '{q}' NOT to be flagged as seeking direct solution",
            )

    def test_grow_stage_mapping(self):
        # 1. Goal stage: no current concern
        state_goal = CoachingWorkingState(current_concern=None)
        res_goal = WorkflowNodes._evaluate_socratic_guard("Hello", state_goal)
        self.assertEqual(res_goal["socratic_stage"], "Goal")

        # 2. Reality stage: concern present, but few facts/observations
        state_reality = CoachingWorkingState(
            current_concern="Manage team friction",
            reported_facts=["Team missed deadline"],
            observations=[],
        )
        res_reality = WorkflowNodes._evaluate_socratic_guard("We missed the deadline", state_reality)
        self.assertEqual(res_reality["socratic_stage"], "Reality")

        # 3. Options stage: facts and observations established, but no action commitments
        state_options = CoachingWorkingState(
            current_concern="Manage team friction",
            reported_facts=["Team missed deadline", "Bob was defensive"],
            observations=["Tension during retro"],
            action_context=[],
            emerging_agency=[],
        )
        res_options = WorkflowNodes._evaluate_socratic_guard("How can I approach Bob?", state_options)
        self.assertEqual(res_options["socratic_stage"], "Options")

        # 4. Will stage: emerging agency or active commitments present
        state_will = CoachingWorkingState(
            current_concern="Manage team friction",
            reported_facts=["Team missed deadline", "Bob was defensive"],
            observations=["Tension during retro"],
            emerging_agency=["I can ask Bob for a 1-on-1 tomorrow morning"],
        )
        res_will = WorkflowNodes._evaluate_socratic_guard("I'll talk to him tomorrow", state_will)
        self.assertEqual(res_will["socratic_stage"], "Will")


if __name__ == "__main__":
    unittest.main()

