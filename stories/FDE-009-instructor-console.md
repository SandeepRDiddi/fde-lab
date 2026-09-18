# FDE-009: Instructor console (frontend)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-001, FDE-002
**Architecture ref:** architecture.md → Frontend — single Next.js app, role-gated

## User story
As an instructor, I want to configure and monitor a cohort's scenario run from one
screen, so that I don't need to touch the backend directly.

## Acceptance criteria (EARS)
1. THE console SHALL let an instructor set a scenario's start time, end time, and
   optional pivot time.
2. WHILE a cohort's scenario is active, THE console SHALL show each student's
   current status.
3. THE console SHALL let an instructor view a student's submission and its
   compliance/approval outcome.

## Definition of done
- [x] An instructor can schedule and monitor a full cohort run without backend access
      (verified live — see merge review below: created an instance via a live backend,
      scheduled it from the console's own endpoints, watched it unlock, viewed and
      approved a real submission, all through this story's API surface)
- [x] Story status updated below
- [x] architecture.md updated if the console scope deviates from documented (no deviation)

## Implementation log
_(appended by the agent as work happens)_

### 2026-09-18

Built the instructor console inside the existing `frontend/` Next.js app (no
separate app — matches "single Next.js app, role-gated" in
`architecture.md` → Frontend):

- `app/instructor/page.tsx` — landing page, instructor enters a cohort id
  and is routed to `app/instructor/[cohortId]/page.tsx`.
- `app/instructor/[cohortId]/page.tsx` (server component) + new
  `components/InstructorConsole.tsx` (client) — one screen with: a schedule
  form (start/end/optional pivot, AC1) that applies the same schedule to
  every student instance in the cohort; a roster table showing each
  instance's `status` and `approval_outcome` (AC2); and a per-student
  submission viewer (content, approval status, approve/reject actions) that
  opens on "View submission" (AC3).
- Extended `lib/types.ts` (`approval_outcome`/`approval_decided_at` on
  `ScenarioInstance`, new `SubmissionDetail`/`ScenarioSchedule` types) and
  `lib/backend.ts` (`listCohortInstances`, `scheduleScenarioInstance`,
  `listSubmissions`, `decideSubmission`), plus four new `/api/*` proxy route
  handlers following the existing FDE-008 pattern (browser never calls
  `BACKEND_URL` directly).
- New CSS in `app/globals.css` for the roster table and approval badges,
  reusing the existing `.panel`/`.status-badge`/`.empty-state` conventions.

**Deviation — two small backend endpoints added.** AC2 and AC3 need to
enumerate a cohort's instances and a student's submissions; neither existed
(`backend/` only had get-by-id routes). Added, with tests:
`GET /scenario-instances?cohort_id=` (`backend/app/routers/scenario_instances.py`)
and `GET /scenario-instances/{instance_id}/submissions`
(`backend/app/routers/submissions.py`). Both are read-only list endpoints
reusing existing schemas (`list[ScenarioInstanceRead]` /
`list[SubmissionRead]`) — no schema or model changes. `architecture.md`
doesn't enumerate individual routes, so this isn't a documented deviation
needing an architecture.md edit, but it is scope beyond "frontend" in the
story title.

**Known gaps, not fixed here (pre-existing repo state):**
- No `students`/`cohorts` tables exist yet (`backend/app/models.py`
  comment) — the roster shows opaque student UUIDs, not names.
- No auth/role-gating exists anywhere in `frontend/` yet (`architecture.md`
  open question); `/instructor/*` is reachable by anyone who knows a cohort
  id, same maturity level as the rest of the app today.
- The backend never persists per-rule compliance detail for a submission
  (compliance runs client-side before submit, per FDE-008's
  `lib/compliance.ts`) — the submission viewer notes compliance passed
  (implied by the submission existing) rather than showing rule-level
  results that don't exist server-side.
- Added approve/reject actions to the submission viewer (backed by
  FDE-007's existing decision endpoint) even though AC3 only says "view" —
  needed for the Definition of Done's "without backend access" framing,
  since a submission with no auto-decision configured would otherwise be
  stuck pending forever.

**Not verified in this session:** this sandbox blocked every non-trivial
shell command (`npm run typecheck`, `npm run lint`,
`.venv/bin/pytest`) behind an interactive approval prompt that never
resolved. Please run those three before merging.

### 2026-09-18 (merge review — merged directly by the repo owner, reviewed after)
This PR was merged without going through the usual review-before-merge
step, so it got a full pass afterward instead: `npm run typecheck` and
`npm run build` both pass; backend's 42 tests pass; and, since Docker
happened to be reachable in this session (see FDE-010's merge review), the
whole flow was exercised against a real running stack rather than just
read: created a scenario instance directly on the live backend, scheduled
it through `POST /scenario-instances/{id}/schedule` (the same endpoint this
console's "Apply to cohort" button calls), watched the real Celery
unlock job fire, submitted and approved a real submission through the
approval-workflow endpoints this console's submission viewer uses, and
loaded `/instructor/<cohortId>` itself (200, server-rendered against the
live backend). No bugs found in this story's own code.

One noted gap, not a bug: the schedule form's "Pivot (optional)" field only
collects a pivot *time* — there's no way to enter `pivot_config` through
this UI, so setting a pivot time alone schedules a job that fires and does
nothing (`apply_scenario_pivot` no-ops without `pivot_config`). AC1 as
literally worded ("set... optional pivot time") is satisfied; giving the
console a way to actually configure *what* the pivot changes is follow-up
scope, not a defect in what's here.
