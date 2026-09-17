# FDE-005: Legacy API mock service

**Status:** Not started
**Priority:** P1
**Depends on:** —
**Architecture ref:** architecture.md → Enterprise system mocks

## User story
As a student, I want to encounter a mock legacy system with realistic quirks, so
that I practice integrating with imperfect infrastructure.

## Acceptance criteria (EARS)
1. THE legacy API mock SHALL expose at least one endpoint per scenario that returns
   intentionally inconsistent field names or types across calls.
2. WHERE a scenario configures added latency, THE legacy API mock SHALL delay
   responses by the configured amount.
3. IF a request omits the scenario's required auth header, THEN THE legacy API mock
   SHALL return a 401 with a deliberately unhelpful error message.

## Definition of done
- [ ] Mock behavior is configurable per scenario without a code change
- [ ] Story status updated below
- [ ] architecture.md updated if the mock approach deviates from documented

## Implementation log

**2026-09-17** — Built `mocks/legacy-api/` as standalone FastAPI service, per
`architecture.md`'s repo layout (own `requirements.txt`/`pytest.ini`, mirrors
`backend/app`'s config/main structure). Scenario behavior lives entirely in
`mocks/legacy-api/scenarios/*.json` (scenario_id, path, optional auth_header,
latency_ms, list of response variants); `app/scenario_loader.py` reads every
file in that directory at startup and registers a `GET /{scenario_id}{path}`
route per scenario — adding a scenario is a new JSON file, no code change
(DoD item 1). Each route round-robins through its `responses` list so
repeated calls return payloads with different field names/types (AC1, e.g.
`account_id`/`int` vs `AccountID`/`str` in `scenarios/acme-crm.json`). If
`latency_ms` is set the handler `asyncio.sleep`s before responding (AC2,
`scenarios/northwind-erp.json`). If `auth_header` is set and the request
omits it, returns 401 with a generic `{"error": "ERR-4471", ...}` body that
never names the missing header (AC3). Added `tests/test_legacy_api.py`
covering schema drift across calls, latency delay, missing/present auth
header, directory-based scenario loading, and app boot + `/health`.

Deviation: could not execute `pip install` / `pytest` in this session — the
sandbox's Bash approval step blocked every command past trivial ones (`pwd`,
`python3 --version`), including `ls`, `python3 -m venv`, and `py_compile` on
this same repo. Tests were written to mirror `backend/tests`' existing
conventions and were reviewed by hand for correctness, but the suite has not
actually been run. Worth executing `cd mocks/legacy-api && pip install -r
requirements.txt && pytest -q` before merge.

_(appended by the agent as work happens)_
