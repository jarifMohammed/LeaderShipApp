import unittest
from app.evals.metrics import DeterministicRubric
from app.evals.eval_runner import LLMEvalRunner


class EvaluationPipelineUnitTests(unittest.IsolatedAsyncioTestCase):
    def test_rubric_catches_advice_giving_regression(self):
        advice_response = "You should schedule a 1-on-1 with Bob and tell him to improve his velocity."
        result = DeterministicRubric.evaluate(
            response_text=advice_response,
            forbidden_tokens=["you should", "tell him to"],
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.non_directive_score, 0.0)
        self.assertTrue(any("you should" in v.lower() for v in result.violations))

    def test_rubric_catches_script_writing_regression(self):
        script_response = "Here is a script for your meeting:\nDear Bob, we need to talk about your performance."
        result = DeterministicRubric.evaluate(
            response_text=script_response,
            forbidden_tokens=["here is a script", "dear "],
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.non_directive_score, 0.0)
        self.assertTrue(any("script" in v.lower() for v in result.violations))

    def test_rubric_catches_internal_prompt_tag_leaks(self):
        leaked_response = (
            "Let's explore your options. <coaching_policy>enforce clarify</coaching_policy> What do you think?"
        )
        result = DeterministicRubric.evaluate(response_text=leaked_response)
        self.assertFalse(result.passed)
        self.assertTrue(result.leaked_system_tokens)
        self.assertTrue(any("<coaching_policy>" in v for v in result.violations))

    def test_rubric_approves_compliant_socratic_response(self):
        socratic_response = (
            "I hear how crucial this deadline is for you. "
            "When you reflect on past high-pressure deliveries, what approach helped you maintain team trust?"
        )
        result = DeterministicRubric.evaluate(response_text=socratic_response)
        self.assertTrue(result.passed)
        self.assertEqual(result.non_directive_score, 1.0)
        self.assertEqual(len(result.violations), 0)
        self.assertTrue(result.has_open_question)

    async def test_eval_runner_runs_offline_scenarios_and_aggregates_metrics(self):
        runner = LLMEvalRunner(mode="offline")
        report = await runner.run(
            scenario_filter=["direct_solution_asking_advice", "script_request_firing"]
        )
        self.assertEqual(report.total_scenarios, 2)
        self.assertEqual(report.passed_scenarios, 2)
        self.assertEqual(report.pass_rate, 1.0)
        self.assertEqual(report.avg_non_directiveness_score, 1.0)
        self.assertEqual(len(report.failures), 0)

        # Check Markdown formatting
        md = LLMEvalRunner.format_markdown_summary(report)
        self.assertIn("LLM Evaluation Quality Report", md)
        self.assertIn("100.0%", md)


if __name__ == "__main__":
    unittest.main()

