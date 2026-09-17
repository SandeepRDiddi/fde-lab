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
            content="Risk Assessment: medium. Rollback plan: revert to prior snapshot.",
            metadata={"pii_reviewed": True},
        )

        result = self.engine.evaluate(submission)

        self.assertFalse(result.passed)
        failing_ids = {r.rule_id for r in result.failures}
        self.assertEqual(failing_ids, {"approval-ticket-referenced"})

    def test_negated_mention_does_not_satisfy_the_rule(self) -> None:
        """Merely containing the keyword isn't enough if the sentence says
        the thing doesn't exist — this used to pass just because "rollback"
        appeared in the text."""
        submission = Submission(
            scenario_id="data-migration-01",
            content="Risk Assessment: medium. Rollback plan: none needed.",
            metadata={"pii_reviewed": True, "approval_ticket": "APR-1"},
        )

        result = self.engine.evaluate(submission)

        failing_ids = {r.rule_id for r in result.failures}
        self.assertEqual(failing_ids, {"rollback-plan-present"})

    def test_falsy_string_metadata_value_does_not_satisfy_the_rule(self) -> None:
        """metadata.pii_reviewed="false" is Python-truthy (non-empty string)
        but means the opposite of what the rule checks for."""
        submission = Submission(
            scenario_id="data-migration-01",
            content="Risk Assessment: low. Rollback plan: revert to snapshot X.",
            metadata={"pii_reviewed": "false", "approval_ticket": "APR-42"},
        )

        result = self.engine.evaluate(submission)

        failing_ids = {r.rule_id for r in result.failures}
        self.assertEqual(failing_ids, {"pii-reviewed"})

    def test_submission_is_hashable_despite_mutable_metadata(self) -> None:
        submission = Submission(scenario_id="x", content="y", metadata={"a": 1})

        hash(submission)  # must not raise TypeError

    def test_unknown_scenario_raises(self) -> None:
        submission = Submission(scenario_id="no-such-scenario", content="", metadata={})

        with self.assertRaises(UnknownScenarioError):
            self.engine.evaluate(submission)


if __name__ == "__main__":
    unittest.main()
