"""Turns a raw, messy instructor requirement ("client's CRM sync keeps
duplicating records") into a full scenario config -- persona, synthetic
dataset shape, a technical task with an executable reference query, and an
optional legacy-system quirk -- ready to hand to POST /scenario-instances.
FDE-014: this is the "requirements in, full FDE Lab scenario out" half of
the platform; app/grading.py (FDE-013) is the other half, checking the
student's actual submission against what this module generates.

Deliberately never emits a compliance_checklist: a submission's whole
content is the SQL query itself (app/grading.py grades it by running it),
so a prose-phrasing rule on that same field could never be jointly
satisfiable with a working query -- an instructor authoring a scenario by
hand can still combine the two, but the generator doesn't produce that
combination itself.

Talks to the same OpenAI-compatible model backend persona-service talks to
(see persona-service/app/gateway.py) -- Groq by default (open-weight models,
free tier, far faster than a local CPU-bound Ollama instance), swappable via
FDE_PROMPTOPS_GATEWAY_URL/_API_KEY/_MODEL. This module duplicates that small
HTTP client rather than importing persona-service's, per this repo's "each
service is independent" convention (CLAUDE.md) -- they don't share a venv or
import each other's code.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

import httpx

from app.config import settings

# Mirrors data-gen/generator/domains.py's DOMAINS fieldnames -- kept in sync
# by hand since data-gen and backend are independent services (no shared
# import). Only used here to (a) tell the model what columns it may write a
# reference_query against and (b) sanity-check that query actually runs.
KNOWN_DOMAINS: dict[str, list[str]] = {
    "ecommerce_orders": [
        "order_id",
        "customer_name",
        "customer_email",
        "order_date",
        "product_sku",
        "quantity",
        "unit_price",
        "order_status",
    ],
    "hr_employees": [
        "employee_id",
        "full_name",
        "email",
        "department",
        "hire_date",
        "salary",
        "manager_id",
    ],
}

# The table name a domain's dataset is queried as. Fixed rather than
# model-chosen: letting the model invent its own table_name alongside a
# separately-written reference_query gave it two independent places to name
# the same table, and it frequently disagreed with itself (e.g. table_name
# "orders" but "FROM ecommerce_orders" in the query) -- caught live against
# the real model. One canonical name per domain removes that failure class
# instead of just detecting it.
TABLE_NAMES: dict[str, str] = {"ecommerce_orders": "orders", "hr_employees": "employees"}

# Mirrors mocks/legacy-api/scenarios/*.json -- the generator can only pick an
# already-authored legacy scenario (the mock service has no way to invent a
# new endpoint from an LLM call), so this is a closed set, not free-form.
KNOWN_LEGACY_SCENARIOS: dict[str, dict[str, Any]] = {
    "acme-crm": {
        "scenario_id": "acme-crm",
        "path": "/accounts",
        "auth_header_name": "X-Legacy-Auth",
        "description": "Acme CRM account lookup -- requires an auth header; schema drifts between calls.",
    },
    "northwind-erp": {
        "scenario_id": "northwind-erp",
        "path": "/orders",
        "auth_header_name": None,
        "description": "Northwind ERP order lookup -- no auth required, but responds slowly (~1.2s) and schema drifts between calls.",
    },
}

_VALID_MESSINESS = {"low", "medium", "high"}

# Cheap heuristic against the single most common way a small model's
# reference_query is syntactically valid but semantically wrong: the
# instructions describe deduplicating/cleaning messy rows, but the query is
# just a column projection that returns the same duplicates unchanged (the
# in-memory-table execution check above can't catch this -- an empty table
# has no duplicates to fail to remove).
_DEDUP_WORDS = re.compile(r"\b(duplicate|duplicated|duplicates|dedup|dedupe|deduplicate)\b", re.IGNORECASE)
_DEDUP_SQL = re.compile(r"\b(distinct|group\s+by|max\s*\(|min\s*\(|count\s*\()", re.IGNORECASE)


class GeneratorError(Exception):
    """The model backend was unreachable, or its output couldn't be turned
    into a usable scenario config after a retry."""


def _call_model_backend(prompt: str, *, client: httpx.Client | None = None) -> str:
    owns_client = client is None
    client = client or httpx.Client(timeout=120.0)
    headers = {"Authorization": f"Bearer {settings.promptops_gateway_api_key}"} if settings.promptops_gateway_api_key else {}
    try:
        response = client.post(
            f"{settings.promptops_gateway_url}/chat/completions",
            headers=headers,
            json={
                "model": settings.promptops_gateway_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GeneratorError(f"Model backend request failed: {exc}") from exc
    finally:
        if owns_client:
            client.close()
    return response.json()["choices"][0]["message"]["content"]


def _build_prompt(requirement: str, *, correction: str | None = None) -> str:
    domains_desc = "\n".join(
        f'- "{name}": table `{TABLE_NAMES[name]}`, columns {cols}' for name, cols in KNOWN_DOMAINS.items()
    )
    legacy_desc = "\n".join(
        f'- "{key}": {info["description"]}' for key, info in KNOWN_LEGACY_SCENARIOS.items()
    )
    correction_block = f"\n\nYour previous attempt was rejected: {correction}\nFix exactly that and try again." if correction else ""

    return f"""You are designing a training scenario for FDE Lab, a simulator that puts \
a student in the shoes of a Forward Deployed Engineer handling a real, messy \
client request. Turn the instructor's raw requirement below into a scenario \
config as a single JSON object -- nothing else, no markdown fences, no \
explanation before or after it.

Instructor's requirement:
\"\"\"{requirement}\"\"\"

Output exactly this JSON shape:
{{
  "persona": {{
    "system_prompt": "<2-4 sentences: who this stakeholder is, their personality, what they do and don't know>",
    "agenda": "<one sentence: what this stakeholder wants from the student right now>"
  }},
  "data_gen": {{
    "domain": "<one of the domain names below>",
    "messiness": "<low, medium, or high>"
  }},
  "technical_task": {{
    "instructions": "<what the student must write a SQL query to accomplish, referencing the mess in the data>",
    "reference_query": "<a single read-only SELECT statement, using ONLY the chosen domain's exact table name and columns below, that ACTUALLY implements what instructions describes -- e.g. if the task is about duplicate/messy rows, the query must use DISTINCT, GROUP BY, or an aggregate to actually resolve that, not just select columns unchanged>"
  }},
  "legacy_system": "<one of the legacy system ids below, or \\"none\\">"
}}

Available domains (technical_task.reference_query may only reference these columns):
{domains_desc}

Available legacy systems (pick one only if the requirement plausibly involves integrating with an old/external system; otherwise "none"):
{legacy_desc}

A student's whole submission is the SQL query itself -- there is no separate
written explanation, so do not invent any requirement about wording,
required phrases, or a minimum length; the query is graded purely by
running it.

Respond with only the JSON object.{correction_block}"""


def _extract_json(text: str) -> dict:
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise GeneratorError("Model output contained no JSON object")
    try:
        return json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise GeneratorError(f"Model output was not valid JSON: {exc}") from exc


def _is_single_select(sql: str) -> bool:
    # Mirrors app/grading.py's own check -- both modules independently agree
    # that only a single read-only SELECT is acceptable; kept local rather
    # than importing grading's private helper.
    statements = [s.strip() for s in sql.strip().rstrip(";").split(";") if s.strip()]
    return len(statements) == 1 and statements[0].lower().startswith("select")


def _reference_query_executes(table_name: str, columns: list[str], reference_query: str) -> str | None:
    """Runs the query against an empty table shaped like the chosen domain --
    catches a hallucinated column or SQL syntax error immediately rather than
    only discovering it the first time a student submits. Returns an error
    message, or None if it ran cleanly."""
    conn = sqlite3.connect(":memory:")
    try:
        quoted = ", ".join(f'"{c}"' for c in columns)
        conn.execute(f'CREATE TABLE "{table_name}" ({quoted})')
        conn.execute(reference_query)
        return None
    except sqlite3.Error as exc:
        return str(exc)
    finally:
        conn.close()


def _validate(draft: dict) -> tuple[dict | None, str | None]:
    """Returns (config, None) on success or (None, reason) naming the first
    problem worth retrying for. Fields that don't affect whether the
    scenario actually works (messiness, row_count) are defaulted instead of
    failing the whole draft -- only a broken technical task or an unknown
    domain is worth a retry. technical_task.table_name is never taken from
    the model at all (see TABLE_NAMES) -- fixed per domain instead. No
    compliance_checklist is ever emitted: a submission's whole content is
    the SQL query, so a prose-phrasing rule on the same field could never
    be satisfiable alongside it."""
    if not isinstance(draft, dict):
        return None, "top-level output must be a JSON object"

    persona = draft.get("persona") or {}
    system_prompt = str(persona.get("system_prompt") or "").strip()
    agenda = str(persona.get("agenda") or "").strip()
    if not system_prompt or not agenda:
        return None, 'persona.system_prompt and persona.agenda must both be non-empty strings'

    data_gen = draft.get("data_gen") or {}
    domain = data_gen.get("domain")
    if domain not in KNOWN_DOMAINS:
        return None, f'data_gen.domain must be one of {list(KNOWN_DOMAINS)}, got {domain!r}'
    messiness = data_gen.get("messiness")
    if messiness not in _VALID_MESSINESS:
        messiness = "medium"

    technical_task = draft.get("technical_task") or {}
    reference_query = str(technical_task.get("reference_query") or "").strip()
    table_name = TABLE_NAMES[domain]
    instructions = str(technical_task.get("instructions") or "").strip()
    if not reference_query:
        return None, "technical_task.reference_query must be a non-empty string"
    if not _is_single_select(reference_query):
        return None, "technical_task.reference_query must be a single read-only SELECT statement"
    if _DEDUP_WORDS.search(instructions) and not _DEDUP_SQL.search(reference_query):
        return None, (
            "technical_task.instructions describes a duplicate/messy-row problem, but "
            "reference_query doesn't use DISTINCT, GROUP BY, or an aggregate to actually "
            "resolve it -- it would just select the same duplicated rows unchanged"
        )
    exec_error = _reference_query_executes(table_name, KNOWN_DOMAINS[domain], reference_query)
    if exec_error is not None:
        return None, (
            f'technical_task.reference_query must select FROM a table literally named "{table_name}" '
            f"(not the domain name {domain!r}) using only its columns {KNOWN_DOMAINS[domain]}; "
            f"it failed to run: {exec_error}"
        )
    if not instructions:
        instructions = f'Write a query against "{table_name}" that addresses: {reference_query}'

    legacy_system_id = draft.get("legacy_system")
    legacy_system = KNOWN_LEGACY_SCENARIOS.get(legacy_system_id)

    config: dict[str, Any] = {
        "persona": {"system_prompt": system_prompt, "agenda": agenda},
        "data_gen": {"domain": domain, "messiness": messiness},
        "technical_task": {
            "task_type": "sql_query",
            "table_name": table_name,
            "instructions": instructions,
            "reference_query": reference_query,
        },
    }
    if legacy_system is not None:
        config["legacy_system"] = {
            "scenario_id": legacy_system["scenario_id"],
            "path": legacy_system["path"],
            "auth_header_name": legacy_system["auth_header_name"],
            "description": legacy_system["description"],
        }
    return config, None


def generate_scenario_config(requirement: str, *, client: httpx.Client | None = None) -> dict:
    """Drafts a scenario config from a raw requirement. Retries once with a
    corrective prompt naming the specific problem if the first attempt's
    output can't be parsed or is missing something a scenario can't work
    without; raises GeneratorError if the second attempt also fails."""
    if not requirement or not requirement.strip():
        raise GeneratorError("requirement must not be empty")

    last_error = "no output"
    for attempt in range(2):
        prompt = _build_prompt(requirement, correction=last_error if attempt else None)
        raw = _call_model_backend(prompt, client=client)
        try:
            draft = _extract_json(raw)
        except GeneratorError as exc:
            last_error = str(exc)
            continue
        config, error = _validate(draft)
        if config is not None:
            return config
        last_error = error or "invalid draft"

    raise GeneratorError(f"Could not generate a usable scenario after 2 attempts: {last_error}")
