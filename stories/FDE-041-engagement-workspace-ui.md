# FDE-041: Engagement workspace UI

**Status:** Done
**Priority:** P1
**Depends on:** FDE-008, FDE-009, FDE-017
**Architecture ref:** architecture.md → Frontend — single Next.js app, role-gated

## User story
As a student working through a multi-stage engagement, I want one page that
shows every stage's status and lets me work the current one, instead of
being handed a raw scenario-instance URL per stage with no sense of where I
am in the whole thing. As an instructor, I want a one-click way to launch
the GlobalRetail engagement for a student and get a link to hand them.

## Motivation

FDE-017 through FDE-040 built the `Engagement` backend primitive and
authored all 22 stages of content, but no frontend work happened in that
arc — `frontend/` (FDE-008/009) only knows about a single
`ScenarioInstance` at `/workspace/<instanceId>`, with no concept of a
chain of stages or which one is currently unlocked. Verified live via curl
during that arc's testing that the engine works end to end; this story is
the missing piece to actually see and use it as a student or instructor
would, in a browser, not via curl.

## Acceptance criteria (EARS)
1. THE frontend SHALL expose `/engagement/<engagementId>`, rendering a
   stage list (all stages the engagement has, each showing Locked/Active/
   Approved/Needs resubmission) and the currently-selected stage's
   persona chat + submission panel, reusing the existing FDE-008
   components rather than duplicating them.
2. WHERE a stage is `not_started` (locked), THE stage list SHALL show it
   as locked and SHALL NOT let the student select it as the focused stage.
3. WHEN a submission is approved, THE frontend SHALL reflect the next
   stage unlocking without a manual page reload being the only way to see
   it (a refetch after decision, or the student revisiting the page).
4. THE instructor console SHALL expose a way to launch a GlobalRetail
   engagement for a given student (cohort id already in context, student
   id entered), returning a link to `/engagement/<id>` to hand the
   student — reusing `POST /engagements/global-retail` (FDE-018).
5. `npm run typecheck` and `npm run lint` SHALL both pass with no new
   errors.

## Definition of done
- [x] `/engagement/<engagementId>` page + `EngagementClient` component
- [x] Stage list shows correct status per stage (locked/active/approved/
      rejected), locked stages not selectable
- [x] Instructor console: GlobalRetail engagement launcher, links to the
      created engagement
- [x] `lib/types.ts` / `lib/backend.ts` extended for `Engagement` (no
      changes to existing types' shape, additive only)
- [x] New `/api/engagements/*` proxy routes, same pattern as existing
      `/api/scenario-instances/*` routes
- [x] Verified live in a browser against the real backend/persona-service
      (not just typecheck) — launch an engagement, chat with stage 0,
      submit, approve via instructor console, confirm stage 1 unlocks in
      the UI
- [x] `npm run typecheck` and `npm run lint` both clean (ESLint config added
      as a same-day follow-up — see log)
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — New `frontend/app/engagement/[engagementId]/page.tsx`
(server component, mirrors `workspace/[instanceId]/page.tsx`'s pattern) +
`EngagementClient.tsx` (client component). The page computes the
"frontier" stage — the last stage that isn't `not_started` — since every
approved stage stays instance-status `active` forever (FDE-017 never
closes a prior stage; only `approval_outcome`, not `instance.status`,
distinguishes "currently open" from "already done"). `?stage=N` lets a
student (or this session's own test) navigate to any unlocked stage; a
locked stage requested via the query param falls back to the frontier
rather than 404ing. `EngagementClient` reuses the exact same components
`WorkspaceClient` already uses (`PersonaChat`, `SubmissionPanel`,
`ArtifactFeed`, `LegacySystemPanel`, `DatasetPreview`,
`ScenarioStatusHeader`) for the focused stage's panel, plus a new stage-list
sidebar deriving a display status (`locked`/`active`/`approved`/`rejected`)
per stage from `instance.status` + `approval_outcome`. AC3 (see a newly
unlocked stage without a full reload) is a "Refresh" button calling Next's
`router.refresh()` — re-runs the server component's fetch without a full
page navigation; simpler than adding client-side polling or duplicating
fetch state, and Next.js App Router already supports it natively.

New `frontend/components/EngagementLauncher.tsx`: a small card (student-ID
input + Launch button) added to `InstructorConsole` above the roster,
calling the new `POST /api/engagements/global-retail` proxy route (which
wraps FDE-018's backend endpoint) and showing the resulting
`/engagement/<id>` link to hand the student.

`lib/types.ts`: added `Engagement`/`EngagementStatus`, and
`engagement_id`/`stage_order` on `ScenarioInstance` (both additive,
matching the backend's `ScenarioInstanceRead`/`EngagementRead` shapes
exactly — no existing field changed). `lib/backend.ts`: `getEngagement`,
`createGlobalRetailEngagement`, following the existing server-side-fetch
convention (never exposed to the browser directly).

`npm run typecheck`: clean. `npm run lint`: this repo had never had an
ESLint config committed (`next lint`'s interactive first-run setup doesn't
accept piped input in this environment) — a pre-existing gap, not
introduced by this story.

**Follow-up (same day):** set it up non-interactively instead of leaving
the gap. `npx eslint@9`'s auto-resolve picked `eslint-config-next@16` (the
current major) against this project's Next 14.2.5 — a real version
mismatch, not just noise, so pinned explicitly: `eslint@^8` +
`eslint-config-next@^14.2.5` (matching Next.js's own "Strict" scaffold
option), plus `.eslintrc.json` (`{"extends": "next/core-web-vitals"}`) so
the setup never prompts again. `npm run lint`: clean, zero warnings across
the whole existing codebase (not just this story's new files) on the first
real run.

Verified live end to end with a real browser (Playwright, driven
programmatically — screenshots captured, not just DOM assertions) against
the actual running backend (`:8010`) and persona-service (`:8001`, real
Groq-backed model, not mocked): instructor console → launch GlobalRetail
engagement → real persona chat exchange on Stage 0 (asked "who do I report
to", got the correct Marcus Chen / Priya Anand / Jordan Lee answer, same as
the earlier curl-based verification) → submit compliant brief → passed
compliance checklist in the UI → instructor approves via the existing
submission-review flow → back on the engagement page, click Refresh →
Stage 1 now shows Active with its own live persona chat and submission
panel, Stage 0 shows Approved, Stages 2+ still show Locked. Confirms
AC1–AC4 all work as a real user would experience them, not just via API.
