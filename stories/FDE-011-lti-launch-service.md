# FDE-011: LTI 1.3 launch service

**Status:** Not started
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
      the correct scenario instance
- [ ] Story status updated below
- [ ] architecture.md updated if the LTI approach deviates from documented

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

