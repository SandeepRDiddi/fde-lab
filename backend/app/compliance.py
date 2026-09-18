"""Server-side compliance gate for submissions (FDE-006/FDE-007 integration).

Until now, compliance was only checked client-side in the frontend
(lib/compliance.ts) before it ever called this API — meaning anyone calling
POST .../submissions directly bypassed the compliance gate entirely, which
defeats the whole point of a "compliance checklist a submission must clear"
(intent.md). This module makes create_submission the actual enforcement
point instead.

Reuses the {id, description, check, value} rule shape scenario_instances
already carry in config["compliance_checklist"] (set up by FDE-008's
frontend) rather than mocks/compliance-engine's own hardcoded-per-scenario-id
registry (FDE-006), which was never wired to anything live and models
submissions with a `metadata` dict this codebase's real Submission doesn't
have. The negation-aware phrase matching below is ported from that module's
`_mentions` -- the same fix for "no rollback plan" trivially satisfying a
"must mention rollback" rule.
"""
from __future__ import annotations

import re

_NEGATIONS = {
    "no", "not", "none", "never", "without", "lack", "lacks", "lacking",
    "missing", "n/a", "na", "isn't", "isnt", "doesn't", "doesnt", "don't",
    "dont", "won't", "wont", "cannot", "can't", "cant",
}
_WORD_RE = re.compile(r"[a-z0-9']+")


def _mentions_affirmatively(content: str, phrase: str, negation_window: int = 3) -> bool:
    """True if `phrase` appears in `content` with no negation word within
    `negation_window` tokens on either side -- so "no rollback plan" or
    "rollback plan: none needed" don't satisfy a must_include rule just
    because the phrase is present."""
    phrase_tokens = _WORD_RE.findall(phrase.lower())
    if not phrase_tokens:
        return False
    tokens = _WORD_RE.findall(content.lower())
    n = len(phrase_tokens)
    for i in range(len(tokens) - n + 1):
        if tokens[i : i + n] != phrase_tokens:
            continue
        context = tokens[max(0, i - negation_window) : i] + tokens[i + n : i + n + negation_window]
        if not any(word in _NEGATIONS for word in context):
            return True
    return False


def evaluate_submission(content: str, rules: list[dict]) -> tuple[bool, list[dict]]:
    """Evaluate `content` against a scenario's compliance_checklist config.

    Returns (passed, failures) -- failures is [{rule_id, description}, ...]
    for each rule that didn't pass. An empty/missing rule list always passes
    (a scenario with no configured checklist has nothing to gate on).
    """
    failures: list[dict] = []

    for rule in rules:
        check = rule.get("check")
        value = rule.get("value")
        rule_id = rule.get("id", "")
        description = rule.get("description", "")

        if check == "must_include":
            ok = _mentions_affirmatively(content, str(value))
        elif check == "must_exclude":
            # Literal presence check, not negation-aware -- a must_exclude
            # rule is usually guarding against a forbidden phrase (e.g. raw
            # PII) actually appearing, regardless of the sentence around it.
            ok = str(value).lower() not in content.lower()
        elif check == "min_length":
            try:
                ok = len(content) >= float(value)
            except (TypeError, ValueError):
                ok = False
        else:
            # Fail closed: an unrecognized check type (a new rule kind not
            # yet handled here, or a malformed rule from the untyped config
            # JSON) should flag as a failure, not silently pass.
            ok = False

        if not ok:
            failures.append({"rule_id": rule_id, "description": description})

    return len(failures) == 0, failures
