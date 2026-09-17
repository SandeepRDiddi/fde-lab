"""Scenario checklist definitions shipped with the compliance engine.

Each scenario's checklist lives here as a plain list of Rules. Adding a new
scenario means adding a new list + registering it in `default_engine()` — no
change to the engine itself.
"""
from __future__ import annotations

import re

from .engine import ComplianceEngine
from .models import Rule, Submission

_NEGATIONS = {
    "no", "not", "none", "never", "without", "lack", "lacks", "lacking",
    "missing", "n/a", "na", "isn't", "isnt", "doesn't", "doesnt", "don't",
    "dont", "won't", "wont", "cannot", "can't", "cant",
}
_WORD_RE = re.compile(r"[a-z0-9']+")


def _mentions(*keywords: str, negation_window: int = 3):
    """True if a keyword phrase appears with no negation word within
    `negation_window` tokens on either side — so "no rollback plan" or
    "rollback plan: none needed" don't satisfy a rule just because the
    keyword is present."""
    keyword_tokens = [_WORD_RE.findall(keyword.lower()) for keyword in keywords]

    def check(submission: Submission) -> bool:
        tokens = _WORD_RE.findall(submission.content.lower())
        for kw in keyword_tokens:
            n = len(kw)
            for i in range(len(tokens) - n + 1):
                if tokens[i : i + n] != kw:
                    continue
                context = (
                    tokens[max(0, i - negation_window) : i]
                    + tokens[i + n : i + n + negation_window]
                )
                if not any(word in _NEGATIONS for word in context):
                    return True
        return False

    return check


def _truthy_metadata(key: str):
    """True if metadata[key] is a real affirmative value — not just any
    Python-truthy value, since a string like "false" or "no" is truthy but
    means the opposite of what the rule is checking for."""
    falsy_strings = {"false", "no", "none", "n/a", "na", "0", ""}

    def check(submission: Submission) -> bool:
        value = submission.metadata.get(key)
        if isinstance(value, str):
            return value.strip().lower() not in falsy_strings
        return bool(value)

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
        check=_truthy_metadata("pii_reviewed"),
    ),
    Rule(
        id="rollback-plan-present",
        description="Submission must describe a rollback plan",
        check=_mentions("rollback"),
    ),
    Rule(
        id="approval-ticket-referenced",
        description="Submission metadata must reference an approval ticket (metadata.approval_ticket)",
        check=_truthy_metadata("approval_ticket"),
    ),
]


def default_engine() -> ComplianceEngine:
    """Build a ComplianceEngine pre-loaded with the checklists defined in this module."""
    engine = ComplianceEngine()
    engine.register_checklist("data-migration-01", DATA_MIGRATION_01_RULES)
    return engine
