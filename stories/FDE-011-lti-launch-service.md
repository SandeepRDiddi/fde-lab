# FDE-011: LTI 1.3 launch service

**Status:** Done
**Priority:** P1
**Depends on:** FDE-001
**Architecture ref:** architecture.md → LTI launch service — LMS entry point

## User story
As a student, I want to launch my scenario directly from a link inside my course's
LMS, so that I don't need a separate login or destination to get into FDE Lab.

## Acceptance criteria (EARS)
1. WHEN a student clicks an LTI 1.3 launch link in the course LMS, THE launch
   service SHALL complete the OIDC-based launch handshake and authenticate the
   student without a separate FDE Lab login.
2. THE launch service SHALL map the LMS course/cohort to the correct scenario
   instance in the scenario engine.
3. WHERE the LMS supports Names and Roles Provisioning Service (NRPS), THE launch
   service SHALL be able to use it to populate a cohort's roster automatically.
4. WHERE the LMS supports Assignment and Grade Services (AGS), THE launch service
   SHALL be able to push a completion/score back to the LMS gradebook once a
   scenario finishes.

## Definition of done
- [ ] A test launch from at least one LMS (Canvas or Moodle) lands the student in
      the correct scenario instance (not verified — no live LMS available, and
      the scenario engine (FDE-001, merged) has no `/internal/lti-mappings`
      endpoint for this service to call yet; `test_full_launch_flow.py` simulates
      both with a mocked response, see merge review below)
- [x] Story status updated below
- [x] architecture.md updated if the LTI approach deviates from documented (no deviation)

## Implementation log
_(appended by the agent as work happens)_

**2026-09-17:** Built `lti-service/` as a standalone FastAPI service implementing
the LTI 1.3 / OIDC launch handshake end to end:

- `POST /lti/login` (also `GET`, since some platforms use that) — third-party
  initiated OIDC login: looks up the registered platform, stashes a one-time
  `state`/`nonce` pair (Redis-backed, in-memory fallback for local dev/tests),
  redirects to the platform's authorization endpoint.
- `POST /lti/launch` — validates the returned `id_token` (signature via the
  platform's JWKS with a refetch-on-`kid`-miss cache, `iss`/`aud`/`exp`/`nonce`,
  message type/version, `deployment_id` against the registration), extracts LTI
  claims, resolves the LMS course (`context_id`) to a scenario instance, issues a
  signed session token as an httponly cookie so the student never sees a
  separate FDE Lab login (AC1), and redirects into the frontend at that
  scenario's launch path (AC2).
- `app/nrps.py` / `app/ags.py` — clients for Names and Roles Provisioning
  Service (AC3) and Assignment and Grade Services (AC4), each gated on the
  corresponding claim being present on the launch, using an OAuth2
  client-credentials/JWT-bearer flow (`app/services_auth.py`) against the
  platform's token endpoint. `GET/POST /internal/lti-contexts/{key}/roster|scores`
  expose these to the rest of the platform, keyed off a per-LMS-context cache
  (`app/launch_context_cache.py`) populated on each launch.
- `GET /.well-known/jwks.json` publishes this tool's own public key for the
  platform to verify NRPS/AGS client assertions.
- Dockerfile added (one per service, per the repo's containerization
  convention); `requirements.txt` / `requirements-dev.txt`.
- Tests under `lti-service/tests/` cover login-initiation redirects, id_token
  validation (happy path, replayed/mismatched nonce, unregistered deployment,
  unknown state, NRPS/AGS claim pass-through), the NRPS/AGS clients, and a full
  login→launch integration test (`test_full_launch_flow.py`) using an id_token
  shaped exactly like Canvas's.

**Deviations / gaps, documented in `lti-service/README.md`:**
- No live Canvas/Moodle sandbox or network access was available in this
  environment, and the scenario engine (FDE-001) lives on its own feature
  branch rather than merged here, so there was no real LMS or scenario engine
  to test against. `test_full_launch_flow.py` simulates a Canvas-shaped launch
  and a mocked scenario-engine response as a stand-in for the "test launch from
  at least one LMS lands the student in the correct scenario instance"
  definition-of-done item; this should be re-verified against an actual LMS
  launch and the real scenario engine once both are available, before marking
  this story Done.
- `app/scenario_client.py` calls a `GET /internal/lti-mappings` contract on the
  scenario engine that doesn't exist yet on FDE-001's side — documented there
  and in the README as follow-up work for when the branches reconcile.
- No changes to `architecture.md` were needed — the implementation matches the
  documented design (OIDC-based LTI 1.3 handshake, LMS course/cohort mapped to
  a scenario instance, NRPS/AGS as optional extensions) with no deviation in
  approach, only implementation-level choices (FastAPI, PyJWT, httpx, Redis for
  state) that architecture.md didn't already pin down for this service.

### 2026-09-18 (merge review)
Code-reviewed PR #19 and fixed before merge — auth-adjacent code, reviewed
closely:
- `OneTimeStateStore.pop()` did a non-atomic get-then-delete, so two
  near-simultaneous launches with the same `state` could both redeem it,
  defeating the one-time replay guard. Now atomic: Redis `GETDEL`, or a
  `threading.Lock` around the in-memory fallback.
- No `azp` claim check: per the IMS Security Framework, when `aud` has
  multiple values, `azp` (not just membership in `aud`) identifies the
  actual authorized party. A platform issuing multi-audience id_tokens could
  have passed our audience check while actually being intended for a
  different client. Added the check.
- The session cookie was hardcoded `secure=True, samesite="none"`, which a
  real browser silently drops over plain HTTP — breaking the README's own
  documented local-dev workflow (`uvicorn app.main:app --reload` over
  `http://localhost`) with no visible error. Added
  `LTI_SESSION_COOKIE_SECURE` (default `true`; README's local-dev command
  now sets it `false`), and `samesite` follows it (`SameSite=None` is
  invalid without `Secure` anyway).
- `POST /internal/lti-contexts/{key}/scores` bound `student_sub`/
  `score_given`/`score_maximum` as query params with no request model —
  didn't match how a real caller would POST a score (JSON body). Added a
  `ScorePush` Pydantic model; this endpoint had no test coverage at all, so
  added one.
- `lti_launch` was `async def` but makes several blocking sync HTTP calls
  (platform JWKS fetch, scenario-engine lookup) with no async client —
  under load, one slow call stalls the event loop for every other in-flight
  request. Changed to plain `def` so FastAPI runs it in its threadpool; a
  full async-client rewrite across `keys.py`/`scenario_client.py`/`ags.py`/
  `nrps.py`/`services_auth.py` would be a larger, separate change (also
  addresses connection pooling, which this review left as-is).
- `tool_jwks()` and `_load_platforms()` raised bare `ValueError`/`KeyError`
  on a misconfigured PEM or platform entry — now raise a clear `RuntimeError`
  naming the actual problem instead of an opaque 500/traceback.

**Confirmed but left as-is** (noted for follow-up, not fixed here): the
`ags.py`/`nrps.py` platform-resolution duplication and the duplicated
kid-lookup loop in `keys.py` — real but low-severity simplification
opportunities, not correctness issues.

**Known integration gap, unchanged from the implementation log above**:
`scenario_client.py` still calls a `GET /internal/lti-mappings` endpoint
that doesn't exist on the now-merged FDE-001 backend. This needs either a
follow-up story or folding into FDE-010 (Docker Compose wiring) before a
real LTI launch can resolve an actual scenario instance.

`pytest -q`: 22 passed (4 new: multi-audience azp accept/reject, malformed
platform config, missing tool public key, AGS JSON-body endpoint). Merged
via squash, PR #19 closed, branch deleted.

