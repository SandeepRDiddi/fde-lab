import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compliance_engine import Submission, UnknownScenarioError, default_engine


class ComplianceEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = default_engine()

    def test_submission_satisfying_every_rule_passes(self) -> None:
        submission = Submission(
            scenario_id="data-migration-01",
            content="Risk Assessment: low. Rollback plan: revert to snapshot X.",
            metadata={"pii_reviewed": True, "approval_ticket": "APR-42"},
        )

        result = self.engine.evaluate(submission)

        self.assertTrue(result.passed)
        self.assertEqual(result.failures, ())

    def test_submission_missing_rules_is_blocked_and_names_failures(self) -> None:
        submission = Submission(
            scenario_id="data-migration-01",
            content="Here is my migration plan.",
            metadata={},
        )

        result = self.engine.evaluate(submission)

        self.assertFalse(result.passed)
        failing_ids = {r.rule_id for r in result.failures}
        self.assertEqual(
            failing_ids,
            {
                "risk-assessment-present",
                "pii-reviewed",
                "rollback-plan-present",
                "approval-ticket-referenced",
            },
        )

    def test_partial_failure_names_only_the_failing_rules(self) -> None:
        submission = Submission(
            scenario_id="data-migration-01",
            content="Risk Assessment: medium. Rollback plan: none needed.",
            metadata={"pii_reviewed": True},
        )

        result = self.engine.evaluate(submission)

        self.assertFalse(result.passed)
        failing_ids = {r.rule_id for r in result.failures}
        self.assertEqual(failing_ids, {"approval-ticket-referenced"})

    def test_unknown_scenario_raises(self) -> None:
        submission = Submission(scenario_id="no-such-scenario", content="", metadata={})

        with self.assertRaises(UnknownScenarioError):
            self.engine.evaluate(submission)


if __name__ == "__main__":
    unittest.main()
