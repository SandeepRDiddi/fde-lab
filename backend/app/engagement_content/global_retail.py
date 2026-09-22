"""Stage content for the GlobalRetail worked example of "The FDE Engagement
Framework" artifact (22 stages / 6 missions). Each entry in
GLOBAL_RETAIL_STAGES is one EngagementStageCreate-shaped config, appended one
per stage-content story (FDE-018 = stage 0, FDE-019 = stage 1, ...) so
`POST /engagements/global-retail` launches whatever's been authored so far
rather than needing all 22 stages written before anything is usable.

Facts are fixed/canonical (not generated per student) because this is a
scripted narrative stage, not a data task — the compliance checklist can
therefore check for the exact names/phrases a student needed to extract
through the persona conversation, rather than a fuzzier rubric.
"""
from __future__ import annotations

# --- Stage 0: FDE Mission Briefing (Mission 1: Discover) -------------------
#
# Canonical facts the persona holds and a compliant Engagement Brief must
# surface: who the student reports to, two named stakeholders, one explicit
# out-of-scope item. The persona is instructed not to volunteer them
# unprompted -- the student has to ask.

_STAGE_0_PERSONA = {
    "system_prompt": (
        "You are Dana Whitfield, GlobalRetail Corp's IT Program Manager. "
        "You're onboarding a newly deployed Forward Deployed Engineer (FDE) "
        "who is picking up an AI platform engagement after two prior vendor "
        "attempts already failed here -- a chatbot pilot and a RAG search "
        "tool, both abandoned before shipping anything real. You are "
        "professional but a little guarded, having watched two vendors "
        "already waste the team's time.\n\n"
        "Facts you know and will share ONLY when the FDE specifically asks "
        "the relevant question -- do not volunteer any of this unprompted "
        "in your opening message or dump it all at once:\n"
        "- The FDE reports to Marcus Chen, VP of Engineering, for this "
        "engagement (not to you -- you're onboarding them, not managing "
        "them).\n"
        "- The two stakeholders who matter most day-to-day are Priya Anand "
        "(VP of Operations, cares about store-level speed) and Jordan Lee "
        "(Director of IT, cares about data governance and access control).\n"
        "- Explicitly out of scope for this engagement: any replacement of "
        "the core POS system. Leadership has been burned by scope creep "
        "into POS territory before and will not authorize touching it.\n\n"
        "If asked generally 'what should I know' without a specific "
        "question, prompt them to ask about reporting lines, stakeholders, "
        "or scope boundaries rather than listing the facts yourself."
    ),
    "agenda": (
        "Get the FDE to ask the right onboarding questions before assuming "
        "anything about scope or org structure."
    ),
}

_STAGE_0_COMPLIANCE_CHECKLIST = [
    {
        "id": "reporting-line",
        "description": "Names who the FDE reports to for this engagement (Marcus Chen)",
        "check": "must_include",
        "value": "Marcus Chen",
    },
    {
        "id": "stakeholder-ops",
        "description": "Names the Operations stakeholder (Priya Anand)",
        "check": "must_include",
        "value": "Priya Anand",
    },
    {
        "id": "stakeholder-it",
        "description": "Names the IT stakeholder (Jordan Lee)",
        "check": "must_include",
        "value": "Jordan Lee",
    },
    {
        "id": "out-of-scope",
        "description": "States the POS system replacement is out of scope",
        "check": "must_include",
        "value": "POS",
    },
    {
        "id": "min-length",
        "description": "Brief is substantive, not a one-liner",
        "check": "min_length",
        "value": 200,
    },
]

_STAGE_0 = {
    "persona": _STAGE_0_PERSONA,
    "compliance_checklist": _STAGE_0_COMPLIANCE_CHECKLIST,
}

GLOBAL_RETAIL_STAGES: list[dict] = [
    _STAGE_0,
]
