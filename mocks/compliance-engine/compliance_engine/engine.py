"""Compliance checklist engine: evaluates a submission against its scenario's checklist."""
from __future__ import annotations

from typing import Dict, List

from .models import ChecklistResult, Rule, Submission


class UnknownScenarioError(KeyError):
    """Raised when no checklist has been registered for a scenario."""


class ComplianceEngine:
    """Holds one checklist (an ordered list of Rules) per scenario_id."""

    def __init__(self) -> None:
        self._checklists: Dict[str, List[Rule]] = {}

    def register_checklist(self, scenario_id: str, rules: List[Rule]) -> None:
        self._checklists[scenario_id] = list(rules)

    def checklist_for(self, scenario_id: str) -> List[Rule]:
        try:
            return list(self._checklists[scenario_id])
        except KeyError:
            raise UnknownScenarioError(scenario_id) from None

    def evaluate(self, submission: Submission) -> ChecklistResult:
        """Run the submission's scenario checklist and return every rule's result.

        Raises UnknownScenarioError if the scenario has no registered checklist.
        Callers gate submission on `result.passed`; `result.failures` names the
        specific rules that blocked it.
        """
        rules = self.checklist_for(submission.scenario_id)
        results = tuple(rule.evaluate(submission) for rule in rules)
        return ChecklistResult(scenario_id=submission.scenario_id, results=results)
