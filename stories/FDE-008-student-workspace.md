# FDE-008: Student scenario workspace (frontend)

**Status:** Not started
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
- [ ] Story status updated below
- [ ] architecture.md updated if the frontend approach deviates from documented

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
