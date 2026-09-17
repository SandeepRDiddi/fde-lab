"""Scenario checklist definitions shipped with the compliance engine.

Each scenario's checklist lives here as a plain list of Rules. Adding a new
scenario means adding a new list + registering it in `default_engine()` — no
change to the engine itself.
"""
from __future__ import annotations

from .engine import ComplianceEngine
from .models import Rule, Submission


def _mentions(*keywords: str):
    def check(submission: Submission) -> bool:
        text = submission.content.lower()
        return any(keyword in text for keyword in keywords)

    return check


DATA_MIGRATION_01_RULES = [
    Rule(
        id="risk-assessment-present",
        description="Submission must include a risk assessment section",
        check=_mentions("risk assessment"),
    ),
    Rule(
        id="pii-reviewed",
        description="PII exposure must be reviewed and flagged (metadata.pii_reviewed)",
        check=lambda s: bool(s.metadata.get("pii_reviewed")),
    ),
    Rule(
        id="rollback-plan-present",
        description="Submission must describe a rollback plan",
        check=_mentions("rollback"),
    ),
    Rule(
        id="approval-ticket-referenced",
        description="Submission metadata must reference an approval ticket (metadata.approval_ticket)",
        check=lambda s: bool(s.metadata.get("approval_ticket")),
    ),
]


def default_engine() -> ComplianceEngine:
    """Build a ComplianceEngine pre-loaded with the checklists defined in this module."""
    engine = ComplianceEngine()
    engine.register_checklist("data-migration-01", DATA_MIGRATION_01_RULES)
    return engine
