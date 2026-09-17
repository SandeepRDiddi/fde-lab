# FDE-005: Legacy API mock service

**Status:** Done
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
- [x] Mock behavior is configurable per scenario without a code change
- [x] Story status updated below
- [x] architecture.md updated if the mock approach deviates from documented (no deviation)

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

### 2026-09-18 (merge review)
Code-reviewed PR #17 and fixed before merge:
- `ScenarioConfig.responses` had no minimum length — an empty `responses: []`
  in a scenario JSON passed validation, then crashed the endpoint with
  `ZeroDivisionError` on `call_number % len(scenario.responses)` on the very
  first request. Added `Field(min_length=1)`.
- `load_scenarios()` had no per-file error isolation — one malformed scenario
  JSON crashed the entire service at startup (`ScenarioConfig(**json.loads(...))`
  raising inside the module-level loop in `main.py`), taking down every other
  correctly-configured scenario and `/health` with it. This directly undercut
  the DoD's "configurable per scenario without a code change" claim, since a
  typo in one scenario broke all of them. Now logs and skips an invalid file
  instead of raising.
- Replaced hand-built `Response(content=json.dumps(...), media_type=...)`
  with FastAPI's `JSONResponse` in both response paths — same behavior, less
  code, and correct encoding for free if a future response includes a
  non-JSON-native type.

Added tests for both fixes (empty-responses validation error,
load-skips-invalid-file-loads-the-rest). `pytest -q`: 8 passed. Merged via
squash, PR #17 closed, branch deleted.

_(appended by the agent as work happens)_
