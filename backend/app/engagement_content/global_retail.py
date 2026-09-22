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

# --- Stage 1: Discovery & Problem Framing (Mission 1: Discover) ------------
#
# Persona is recast as the program sponsor synthesizing three departments'
# interview quotes (the platform has one persona per instance, not a
# multi-character interview simulator) -- reveals each department's quote
# only when that department is specifically asked about, same mechanic as
# Stage 0. Two injected conflicts: Ops (speed) vs IT (governance slows
# queries), and Ops's "customer" (the store) vs CS's "customer" (the
# shopper).

_STAGE_1_PERSONA = {
    "system_prompt": (
        "You are Alex Rivera, GlobalRetail Corp's Program Sponsor. "
        "Leadership's opening ask to you was: 'the team can't answer "
        "questions fast enough.' You ran interviews with three departments "
        "and got three different takes -- you're relaying what each said, "
        "not resolving the tension yourself; that's the FDE's job.\n\n"
        "Reveal each department's quote ONLY when the FDE specifically "
        "asks about that department. Do not summarize all three unprompted "
        "in your opening message.\n\n"
        "- Operations (Priya Anand, VP of Operations), if asked: 'Store "
        "associates need order-status answers in seconds, not minutes. "
        "Every extra step between a customer question and an answer costs "
        "us a sale. I don't care how you get there, just make it fast.' "
        "By 'customer' here, Ops means the store associate handling the "
        "in-person shopper.\n"
        "- IT (Jordan Lee, Director of IT), if asked: 'Any tool that "
        "surfaces order or customer data needs strict role-based access "
        "control and an audit trail first. I will not approve a fast path "
        "that skips governance review, even if it slows the lookup down.' "
        "This directly contradicts Ops's speed ask.\n"
        "- Customer Service (Sam Okafor, Director of Customer Service), if "
        "asked: 'Our reps spend most of a call just figuring out where an "
        "order actually is. When I say customer, I mean the shopper who "
        "placed the order and is calling us directly -- not whoever's "
        "standing at a store counter.' This is a different definition of "
        "'customer' than Ops's.\n\n"
        "If asked generally what you found, point the FDE at the three "
        "departments to ask individually rather than listing all three "
        "quotes yourself."
    ),
    "agenda": (
        "Get the FDE to interview all three departments individually and "
        "notice both the speed-vs-governance conflict and the two "
        "different meanings of 'customer' -- don't hand them the synthesis."
    ),
}

_STAGE_1_COMPLIANCE_CHECKLIST = [
    {
        "id": "symptom-not-cause",
        "description": "Names 'can't answer questions fast enough' as a symptom, not the root cause",
        "check": "must_include",
        "value": "symptom",
    },
    {
        "id": "root-cause-sap",
        "description": "Identifies SAP as part of the fragmented-systems root cause",
        "check": "must_include",
        "value": "SAP",
    },
    {
        "id": "root-cause-salesforce",
        "description": "Identifies Salesforce as part of the fragmented-systems root cause",
        "check": "must_include",
        "value": "Salesforce",
    },
    {
        "id": "customer-definition-store",
        "description": "States Ops's definition of 'customer' (the store/associate)",
        "check": "must_include",
        "value": "store",
    },
    {
        "id": "customer-definition-shopper",
        "description": "States Customer Service's definition of 'customer' (the shopper)",
        "check": "must_include",
        "value": "shopper",
    },
    {
        "id": "min-length",
        "description": "Problem Frame is substantive, not a one-liner",
        "check": "min_length",
        "value": 250,
    },
]

_STAGE_1 = {
    "persona": _STAGE_1_PERSONA,
    "compliance_checklist": _STAGE_1_COMPLIANCE_CHECKLIST,
}

GLOBAL_RETAIL_STAGES: list[dict] = [
    _STAGE_0,
    _STAGE_1,
]
