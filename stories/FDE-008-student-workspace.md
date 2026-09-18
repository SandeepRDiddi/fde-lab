# FDE-008: Student scenario workspace (frontend)

**Status:** Done
**Priority:** P0
**Depends on:** FDE-001, FDE-004
**Architecture ref:** architecture.md → Frontend — single Next.js app, role-gated

## User story
As a student, I want a single workspace where I can chat with the persona, view
artifacts and data, and submit my work, so that the whole scenario feels like one
coherent engagement.

## Acceptance criteria (EARS)
1. THE workspace SHALL display the scenario's current status (not started / active
   / closed) and remaining time when active.
2. WHEN a scenario is active, THE workspace SHALL show the persona chat, the
   artifact/ticket feed, and a link to the current dataset.
3. THE workspace SHALL provide a submission panel that surfaces compliance
   failures returned by the backend.

## Definition of done
- [ ] A student can complete one scenario start to finish through this UI
      (not verified — no live backend/persona-service running in this
      environment; `npm run build`/`typecheck` pass, see merge review below)
- [x] Story status updated below
- [x] architecture.md updated if the frontend approach deviates from documented
      (no deviation)

## Implementation log
_(appended by the agent as work happens)_

**2026-09-18:** Built `frontend/` as a Next.js 14 (App Router, TypeScript) app —
the first thing to land in that directory. Scope: the student workspace only
(`/workspace/[instanceId]`); the instructor view (FDE-009) is a separate,
not-yet-started story and isn't touched here.

- `app/workspace/[instanceId]/page.tsx` (server component) fetches the
  scenario instance from `backend/` and, when active, the conversation
  history from `persona-service/`, then renders `WorkspaceClient`.
- `ScenarioStatusHeader` shows status (not started / active / closed) and a
  live ticking countdown to `end_at` while active (AC1).
- When `status === "active"`: `PersonaChat` (send/receive against
  persona-service's `/messages`), `ArtifactFeed` (reads
  `scenario_instances.config["artifacts"]` — the document/artifact injects
  from `intent.md`, no dedicated feed endpoint exists or was needed), and
  `DatasetLink` (`dataset_location`) all render together (AC2).
- `SubmissionPanel` always renders per AC3's unconditional wording, but
  disables the submit action when the instance isn't active.
- All calls from client components go through this app's own `/api/*` route
  handlers (`lib/backend.ts` does the actual server-side fetch to
  `BACKEND_URL` / `PERSONA_SERVICE_URL`). Browser code never calls
  `backend/` or `persona-service/` directly — deliberately, so neither
  service needs CORS configured, keeping this story's changes inside
  `frontend/` only (the architecture ref given was the Frontend section
  alone).

**Known gap, not resolved here:** there is no backend submission/compliance
HTTP endpoint anywhere in the repo — `mocks/compliance-engine` is a bare
Python library (no FastAPI app), and `backend/` has no `Submission` model or
router. `POST /api/scenario-instances/{id}/submit` first tries
`POST {BACKEND_URL}/scenario-instances/{id}/submissions`; on a 404 it falls
back to `lib/compliance.ts`, a local stand-in that evaluates
`config.compliance_checklist` rules (`must_include` / `must_exclude` /
`min_length`) and returns the same `{passed, failures}` shape a real backend
endpoint would, so swapping in a real endpoint later needs no frontend
changes. This is a pre-existing gap (architecture.md's open question on
whether compliance/legacy/approval mocks are separate services or
route-namespaced in the backend is still unresolved), not a frontend
deviation, so no architecture.md edit was made for it.

No Dockerfile was added — `backend/`, `persona-service/`, and `data-gen/`
don't have one yet either; containerization is FDE-010's job.

Could not run `npm install`/`build`/`dev`/`lint` in this session — the shell
tool required per-command approval that wasn't available for anything
beyond trivial commands (`pwd`, `node --version`), so nothing here was
actually executed. Code was written and cross-checked by hand against the
existing backend/persona-service schemas, but per CLAUDE.md's guidance to
verify frontend changes in a real browser: this hasn't been done, and
`npm install && npm run typecheck && npm run dev` should be run against a
live backend + persona-service before treating this as verified.

### 2026-09-18 (merge review)
Code-reviewed PR #20 and fixed before merge:
- `PersonaChat`: a failed send left the optimistic student message
  permanently in the chat log with no indication it was never persisted
  (and it'd silently vanish on next refetch). Now rolled back on error, with
  the draft restored so the student doesn't lose what they typed.
- `PersonaChat`: Enter-to-send didn't check for IME composition, so
  confirming a composed CJK character with Enter sent the message
  mid-composition. Now checks `e.nativeEvent.isComposing`.
- `ScenarioStatusHeader`: `useState(() => Date.now())` computed a different
  value on the server render vs. client hydration, causing a React
  hydration mismatch on every load of an active scenario. Now starts `null`
  and the countdown only renders once the client has actually mounted.
- Both `/api/.../messages` and `/api/.../submit` called `await req.json()`
  outside their try/catch, so a malformed body crashed with an unhandled
  500 instead of this app's own `{detail}` JSON error shape. Wrapped.
- `checkRule`'s default case returned `true` (pass) for an unrecognized
  check type — failing open on a rule that was never actually evaluated.
  Now fails closed.
- Removed `/api/scenario-instances/[instanceId]/route.ts` — confirmed
  nothing in the frontend calls it; `page.tsx` fetches via `lib/backend.ts`
  directly.
- No lockfile existed; ran `npm install` (resolved Next.js to 14.2.35, the
  latest 14.x patch) and committed `package-lock.json`. `npm audit` still
  shows critical CVEs in this Next.js line whose fix requires a Next 16
  major version bump — not done here (no test suite to validate a breaking
  upgrade against); worth its own story before this goes anywhere near a
  real deployment.
- Also updated the root `CLAUDE.md`, stale again (this branch forked before
  FDE-005/006/011 merged): it still said `lti-service/` didn't exist, didn't
  mention `mocks/`, and called the mocks-as-separate-services question
  still open when it's since been resolved by how FDE-005/006 actually
  shipped.

`npm run typecheck` and `npm run build` both pass cleanly (no test
framework configured in this repo yet — verification here is build +
typecheck, not a test suite). Merged via squash, PR #20 closed, branch
deleted.
