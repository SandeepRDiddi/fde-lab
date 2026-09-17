"""Data models for the compliance checklist engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Tuple


@dataclass(frozen=True)
class Submission:
    """A student's attempt to submit a deliverable for a given scenario."""

    scenario_id: str
    content: str
    # Excluded from eq/hash: it's a mutable dict, and a frozen dataclass's
    # auto-generated __hash__ would otherwise try to hash it and raise
    # TypeError the moment anything hashes a Submission.
    metadata: Dict = field(default_factory=dict, compare=False)


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    description: str
    passed: bool


@dataclass(frozen=True)
class Rule:
    """A single checklist rule: a named, described predicate over a Submission."""

    id: str
    description: str
    check: Callable[[Submission], bool]

    def evaluate(self, submission: Submission) -> RuleResult:
        return RuleResult(rule_id=self.id, description=self.description, passed=bool(self.check(submission)))


@dataclass(frozen=True)
class ChecklistResult:
    scenario_id: str
    results: Tuple[RuleResult, ...]

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> Tuple[RuleResult, ...]:
        return tuple(r for r in self.results if not r.passed)
