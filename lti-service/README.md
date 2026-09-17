# lti-service

LTI 1.3 launch service (FDE-011) -- the LMS entry point into FDE Lab. See
`architecture.md` → "LTI launch service — LMS entry point" and
`stories/FDE-011-lti-launch-service.md` for the spec this implements.

## What it does

1. **`GET`/`POST /lti/login`** -- third-party initiated OIDC login. The LMS
   hits this first; the service looks up the registered platform, stashes a
   one-time `state`/`nonce` pair, and redirects to the platform's own
   authorization endpoint.
2. **`POST /lti/launch`** -- the platform form-posts an `id_token` back here.
   The service verifies its signature against the platform's JWKS, checks
   `nonce`/`state`/`deployment_id`, maps the LMS course (`context_id`) to a
   scenario instance via the scenario engine, issues a signed FDE Lab session
   cookie (so the student never sees a separate login), and redirects into
   the frontend at that scenario's launch path.
3. **`GET /internal/lti-contexts/{key}/roster`** -- Names and Roles
   Provisioning Service (NRPS) pull, when the launching platform/deployment
   advertised support for it.
4. **`POST /internal/lti-contexts/{key}/scores`** -- Assignment and Grade
   Services (AGS) score push, for the scenario engine to call once a
   scenario finishes.
5. **`GET /.well-known/jwks.json`** -- this tool's public key, so the
   platform can verify the client-assertion JWTs sent for NRPS/AGS token
   requests.

## Configuration

All via environment variables (see `app/config.py`):

- `LTI_PLATFORMS_JSON` -- JSON array of registered platforms, e.g.
  `[{"issuer": "https://canvas.instance.instructure.com", "client_id": "...",
  "deployment_ids": ["1:abc"], "auth_login_url": "...", "auth_token_url":
  "...", "key_set_url": "..."}]`
- `LTI_TOOL_PRIVATE_KEY_PEM` / `LTI_TOOL_PUBLIC_KEY_PEM` -- this service's own
  RSA keypair (PEM), registered with each platform as the tool's public key
  and used to sign the FDE Lab session token and NRPS/AGS client assertions.
- `FRONTEND_BASE_URL` -- where a validated launch redirects to.
- `SCENARIO_ENGINE_BASE_URL`, `SCENARIO_ENGINE_INTERNAL_TOKEN` -- the
  scenario engine's internal API (see "Known gap" below).
- `REDIS_URL` -- shared with the rest of the platform for OIDC state/nonce
  storage; falls back to an in-process dict if unset (fine for local dev
  and tests, not for multiple replicas).
- `LTI_SESSION_COOKIE_SECURE` -- defaults to `true` (required for the
  session cookie's `SameSite=None`, since the launch redirect is cross-site
  from the LMS). Set to `false` for local dev over plain `http://localhost`
  -- a real browser silently drops a `Secure` cookie over HTTP, which
  otherwise makes the launch look broken with no error.

## Running locally

```
pip install -r requirements-dev.txt
LTI_SESSION_COOKIE_SECURE=false uvicorn app.main:app --reload
```

## Tests

```
pip install -r requirements-dev.txt
python -m pytest
```

`tests/test_full_launch_flow.py` drives a full login → launch round trip
using an id_token shaped exactly like Canvas's, from the login initiation
redirect through to the session cookie and scenario redirect -- see "Known
gap" below for why this stands in for a live LMS test.

## Known gap / deviation from the story's definition of done

FDE-011's definition of done calls for "a test launch from at least one LMS
(Canvas or Moodle) lands the student in the correct scenario instance." This
service implements the full Canvas/Moodle-compatible LTI 1.3 handshake, but
this environment has no network access to an actual Canvas or Moodle
developer sandbox, and the scenario engine (FDE-001) lives on its own
feature branch rather than merged alongside this one, so there's no live
`/internal/lti-mappings` endpoint to call end-to-end either. In place of a
live LMS test, `tests/test_full_launch_flow.py` simulates a launch using an
id_token built to the exact shape Canvas issues (same claim URNs, same
`LtiResourceLinkRequest`/`1.3.0` message type/version) and a mocked scenario
engine response, and asserts the service redirects to the mapped scenario
path with a session cookie set. Once both a real Canvas/Moodle developer key
and a merged scenario engine are available, this should be re-verified with
an actual LMS-initiated launch before the story is marked Done.

`resolve_scenario_instance` in `app/scenario_client.py` documents the
contract this service expects from the scenario engine at
`GET /internal/lti-mappings?platform_issuer=&deployment_id=&context_id=` --
that endpoint doesn't exist yet on the scenario engine side and should be
added when FDE-001's branch and this one are reconciled.
