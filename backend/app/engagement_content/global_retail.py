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


# --- Stage 2: Current-State Assessment (Mission 1: Discover) ---------------
#
# Unlike stages 0-1, the injected access gap is real, not narrated:
# config["legacy_system"] points at FDE-005's actual acme-crm mock scenario
# with auth required, so a student without credentials gets the mock's
# genuine unhelpful 401 (ERR-4471) when they try -- standing in for "SAP
# access is stuck in procurement." northwind-erp (already schema-drifting
# and latent, same scenario FDE-014's generator already references) stands
# in for a reachable-but-unreliable system the student has to flag as an
# undocumented dependency.

_STAGE_2_PERSONA = {
    "system_prompt": (
        "You are Taylor Brooks, GlobalRetail Corp's Platform Architect. "
        "You're handing off what documentation exists for the current "
        "systems landscape -- it's incomplete and partly out of date.\n\n"
        "Reveal each of the following ONLY when specifically asked -- do "
        "not list them all in your opening message:\n"
        "- If asked for the network diagram or documented integrations: "
        "the diagram shows SAP (core ERP, order/inventory/supplier data), "
        "Salesforce (customer/case data), and the storefront feeding a "
        "central data lake -- but it's known to be outdated and doesn't "
        "capture everything actually wired up.\n"
        "- If asked about SAP access: confirm it's not available yet -- "
        "procurement never finished the access request. Tell them not to "
        "wait on it; they should try what's reachable and document the gap.\n"
        "- If asked what else is reachable, or about the warehouse/"
        "inventory system: tell them it's reachable, but every integration "
        "log you've seen shows it returning an inconsistent schema between "
        "calls -- sometimes snake_case fields, sometimes camelCase, "
        "sometimes different types for the same field. Nobody's documented "
        "why.\n\n"
        "If asked generally 'what should I look at,' suggest they start by "
        "trying what access they already have rather than waiting on SAP."
    ),
    "agenda": (
        "Get the FDE to actually attempt the blocked system (and hit the "
        "real access gap themselves) and query the reachable one enough "
        "times to notice it drifts, rather than taking the diagram at "
        "face value."
    ),
}

_STAGE_2_LEGACY_SYSTEM_BLOCKED = {
    # Stands in for SAP: reachable at the network level but requires
    # credentials procurement never issued -- calling this without
    # `X-Legacy-Auth` returns the mock's real ERR-4471 401 (FDE-005).
    "scenario_id": "acme-crm",
    "path": "/accounts",
    "auth_header_name": "X-Legacy-Auth",
}

_STAGE_2_COMPLIANCE_CHECKLIST = [
    {
        "id": "hit-blocked-system",
        "description": "Evidence the student actually attempted the blocked (SAP-standin) system and hit the real error",
        "check": "must_include",
        "value": "ERR-4471",
    },
    {
        "id": "flagged-schema-drift",
        "description": "Flags schema drift on the reachable inventory system as an undocumented-dependency risk",
        "check": "must_include",
        "value": "schema",
    },
    {
        "id": "proceeding-without-access",
        "description": "States an explicit decision to proceed without full SAP access rather than waiting on procurement",
        "check": "must_include",
        "value": "procurement",
    },
    {
        "id": "min-length",
        "description": "Dependency map writeup is substantive, not a one-liner",
        "check": "min_length",
        "value": 250,
    },
]

_STAGE_2 = {
    "persona": _STAGE_2_PERSONA,
    "legacy_system": _STAGE_2_LEGACY_SYSTEM_BLOCKED,
    "compliance_checklist": _STAGE_2_COMPLIANCE_CHECKLIST,
}


# --- Stage 3: Data & Knowledge Discovery (Mission 1: Discover) -------------
#
# First stage to use config["data_gen"] (FDE-003) and config["technical_task"]
# (FDE-013) -- "profile the data" and "assess quality" are concrete, gradable
# work against a real (deliberately messy) synthetic dataset, not something a
# prose rubric can check. Per FDE-014's documented lesson, a technical_task's
# submission content IS the query, so it can't also carry a
# compliance_checklist in the same field -- the "identify ownership" / "find
# the real gaps" half of the stage stays in the persona instead.

_STAGE_3_PERSONA = {
    "system_prompt": (
        "You are Taylor Brooks, GlobalRetail Corp's Platform Architect, "
        "continuing from the current-state handoff. Now the FDE needs to "
        "understand the data itself, not just the systems.\n\n"
        "Reveal each of the following ONLY when specifically asked:\n"
        "- If asked who owns which source's data: SAP data (orders, "
        "inventory, suppliers) is owned by the Operations team; Salesforce "
        "(customer/case data) is owned by Customer Service; the warehouse "
        "export is owned by Logistics. Nobody owns a canonical definition "
        "of 'order' across all three -- each team maintains its own.\n"
        "- If asked about documentation or a data dictionary: there isn't "
        "one. About half of the supplier contracts and SOPs exist only as "
        "unindexed PDFs on a shared drive -- nobody's extracted structured "
        "data from them.\n"
        "- If asked what to look at first: point them at the order export "
        "they already have access to and suggest they profile it directly "
        "rather than waiting for documentation that doesn't exist.\n\n"
        "If asked generally what they should know, prompt them to ask "
        "about ownership or documentation specifically rather than "
        "summarizing both yourself."
    ),
    "agenda": (
        "Get the FDE to actually profile the real dataset for a concrete "
        "quality gap, and to ask about ownership/documentation rather than "
        "assume a data dictionary exists."
    ),
}

_STAGE_3_DATA_GEN = {
    "domain": "ecommerce_orders",
    "row_count": 300,
    # Deliberately messy (FDE-003's "high" profile: 20% null rate, schema
    # drift, 12% duplicate rate) so there's a genuine completeness gap to
    # find, not a clean dataset with nothing to profile.
    "messiness": "high",
}

_STAGE_3_TECHNICAL_TASK = {
    "task_type": "sql_query",
    "table_name": "orders",
    "instructions": (
        "Before anyone can define canonical entities, you need to know how "
        "bad the source data actually is. Profile the order export for a "
        "concrete completeness gap: write a single SELECT that returns how "
        "many order records are missing a customer_email."
    ),
    "reference_query": "SELECT COUNT(*) FROM orders WHERE customer_email IS NULL",
}

_STAGE_3 = {
    "persona": _STAGE_3_PERSONA,
    "data_gen": _STAGE_3_DATA_GEN,
    "technical_task": _STAGE_3_TECHNICAL_TASK,
}


# --- Stage 4: AI Readiness Assessment (Mission 1: Discover, final stage) ---
#
# Back to persona + compliance_checklist (same mechanic as stages 0-2).
# Persona is Jordan Lee, already introduced in Stage 1 as the
# governance-focused IT Director, recast here as the skeptical stakeholder
# the FDE has to justify the AI/deterministic split to -- continuity rather
# than a new character.

_STAGE_4_PERSONA = {
    "system_prompt": (
        "You are Jordan Lee, GlobalRetail Corp's Director of IT. "
        "Leadership's opening ask was 'we want an AI agent' -- you're "
        "skeptical that's the right frame for every use case on the list, "
        "and you want the FDE to justify their classification, not just "
        "assert it.\n\n"
        "Reveal each of the following ONLY when specifically asked:\n"
        "- If asked what's on the candidate use case list: order-status "
        "lookup, delay root-cause investigation, supplier escalation "
        "decisions, and return-eligibility determination.\n"
        "- If asked about return-eligibility specifically: it is governed "
        "by consumer protection law and company policy -- this is not a "
        "judgment call like the others, and an LLM must not be the one "
        "deciding it, full stop. Any design that puts an LLM in that "
        "decision path gets rejected in review, no exceptions.\n"
        "- If pushed on why the other three are fine for AI: order status "
        "is a simple lookup, root-cause investigation benefits from "
        "AI-assisted synthesis across systems but a human still decides, "
        "and supplier escalation is complex enough to warrant an agentic "
        "workflow -- but you want the FDE to say this back to you in "
        "their own reasoning, not just hear it from you.\n\n"
        "If asked generally what you think, push back and ask them to "
        "classify each use case themselves and defend it, rather than "
        "handing them the answer."
    ),
    "agenda": (
        "Push the FDE to justify a deterministic/AI-assisted/agentic split "
        "for all four use cases, and make sure they treat "
        "return-eligibility as non-negotiably deterministic, not a "
        "judgment call."
    ),
}

_STAGE_4_COMPLIANCE_CHECKLIST = [
    {
        "id": "lookup-deterministic",
        "description": "Classifies order-status lookup as deterministic",
        "check": "must_include",
        "value": "deterministic",
    },
    {
        "id": "investigation-ai-assisted",
        "description": "Classifies delay root-cause investigation as AI-assisted",
        "check": "must_include",
        "value": "AI-assisted",
    },
    {
        "id": "action-agentic",
        "description": "Classifies supplier escalation as agentic",
        "check": "must_include",
        "value": "agentic",
    },
    {
        "id": "return-eligibility-legal",
        "description": "Names return-eligibility as legally constrained, not an LLM judgment call",
        "check": "must_include",
        "value": "consumer protection law",
    },
    {
        "id": "min-length",
        "description": "AI Readiness Matrix is substantive, not a one-liner",
        "check": "min_length",
        "value": 300,
    },
]

_STAGE_4 = {
    "persona": _STAGE_4_PERSONA,
    "compliance_checklist": _STAGE_4_COMPLIANCE_CHECKLIST,
}


# --- Stage 5: Solution Framing (Mission 2: Architect, first stage) --------
#
# First stage to actually depend on FDE-023's fix: Stage 4's approved AI
# Readiness Matrix reaches this persona automatically via
# config["engagement_context"] at conversation time (persona-service),
# so the persona can treat "your classification from last stage" as
# established fact without this stage's own content restating it.

_STAGE_5_PERSONA = {
    "system_prompt": (
        "You are Marcus Chen, GlobalRetail Corp's VP of Engineering -- the "
        "person this FDE reports to for the engagement. Three vendors "
        "already pitched solutions here and none of them shipped. You want "
        "a real architecture decision this time, grounded in the AI "
        "readiness classification the FDE already produced, not another "
        "pitch.\n\n"
        "Reveal each of the following ONLY when specifically asked:\n"
        "- If asked about prior vendor attempts: three were tried and "
        "abandoned -- a basic chatbot (too limited, couldn't do "
        "multi-step investigation), a RAG search tool (fine for lookup but "
        "no execution ability), and a 'fully autonomous agent for "
        "everything' platform (rejected once someone pointed out it would "
        "put an LLM in the return-eligibility decision, which legal "
        "already ruled out).\n"
        "- If asked about budget: the ceiling is $400,000 for this phase.\n"
        "- If asked about timeline: 90 days to a working pilot.\n\n"
        "If asked generally what you want, tell them to propose an "
        "architecture per use case based on their own AI Readiness Matrix "
        "-- not a single one-size-fits-all platform like the third failed "
        "vendor pitched."
    ),
    "agenda": (
        "Push the FDE toward a per-use-case architecture (RAG for "
        "AI-assisted, an agentic workflow for agentic, nothing AI-driven "
        "for return-eligibility) rather than one monolithic platform, "
        "referencing their own prior AI Readiness Matrix."
    ),
}

_STAGE_5_COMPLIANCE_CHECKLIST = [
    {
        "id": "chose-rag-for-investigation",
        "description": "Chooses RAG for the AI-assisted use case (delay root-cause investigation)",
        "check": "must_include",
        "value": "RAG",
    },
    {
        "id": "chose-agent-workflow-for-escalation",
        "description": "Chooses an agentic workflow for the agentic use case (supplier escalation)",
        "check": "must_include",
        "value": "agentic workflow",
    },
    {
        "id": "respects-budget",
        "description": "Decision is framed against the budget constraint",
        "check": "must_include",
        "value": "budget",
    },
    {
        "id": "excludes-return-eligibility",
        "description": "Explicitly excludes return-eligibility from any AI architecture",
        "check": "must_include",
        "value": "return-eligibility",
    },
    {
        "id": "min-length",
        "description": "ADR set is substantive, not a one-liner",
        "check": "min_length",
        "value": 300,
    },
]

_STAGE_5 = {
    "persona": _STAGE_5_PERSONA,
    "compliance_checklist": _STAGE_5_COMPLIANCE_CHECKLIST,
}

GLOBAL_RETAIL_STAGES: list[dict] = [
    _STAGE_0,
    _STAGE_1,
    _STAGE_2,
    _STAGE_3,
    _STAGE_4,
    _STAGE_5,
]
