# FDE-040: GlobalRetail engagement — Stage 21 (Handover & Adoption)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-023, FDE-039
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want the final stage to make me hand this off for real —
runbook, architecture doc, support model, backlog — to the same platform
contact I've worked with the whole engagement, so the engagement ends the
way a real one does: with no FDE on call after this.

## Motivation

Twenty-second and final stage-content story on FDE-017's primitive;
appends `GLOBAL_RETAIL_STAGES[21]`, completing all 22 stages of "The FDE
Engagement Framework." Per the framework: **Situation** — the FDE is
rotating off the engagement; the customer's own team has to run it without
them. **Assets** — everything produced across Stages 0–20. **FDE must** —
write the runbook, document the architecture for someone who wasn't there,
define the support model and a 90-day backlog. **GlobalRetail specifics**
— their own platform team inherits the runbook, the dashboards, and the
90-day backlog — no FDE on call after this. **Deliverable** — Production
Handover Pack.

Persona is Taylor Brooks, reused a final time (Stages 2/3/6/9/10/12/16/17)
— the recurring platform-architect contact throughout the engagement is
also who's actually inheriting it, which is the point: closure, not a new
character for the sake of one. By this stage, FDE-023's `engagement_context`
carries all twenty prior stages' approved output, so the persona can
reference "everything you've built so far" as established fact without
this stage needing to re-list it.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[21]` with a persona
   (Taylor Brooks) that, only on request, confirms no FDE will be on call
   after this and states what "done" means: a runbook someone who wasn't
   there could follow, a real support model, and a 90-day backlog.
2. THE `compliance_checklist` SHALL gate the Production Handover Pack on
   naming a runbook, an architecture write-up for an outside reader, a
   support model, and a 90-day backlog — the four concrete deliverables
   the framework specifies for this final stage.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 21 as its last stage,
   locked until stage 20's submission is approved; approving stage 21's
   submission SHALL mark the `Engagement` `completed` per FDE-017's
   existing last-stage behavior — no new mechanism, just the 22nd and
   final stage actually reaching it.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[21]` authored (persona + compliance_checklist)
- [x] Tests: stage 21 config validates, persona doesn't leak facts
      unprompted, a compliant handover pack passes the checklist, each
      missing element fails its rule, and — the actual proof this is
      done — launching `POST /engagements/global-retail` and walking every
      stage through approval end to end reaches `Engagement.status ==
      "completed"` with all 22 stages' output in the final `context`
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[21]` in
`backend/app/engagement_content/global_retail.py`, completing all 22
stages of "The FDE Engagement Framework." Persona is Taylor Brooks, reused
a final time (Stages 2/3/6/9/10/12/16/17) — the recurring platform contact
inheriting the engagement is the closing beat, not a new character.
States the "no FDE on call after this" fact and the four handover
components only on request. `compliance_checklist` requires a runbook, an
architecture write-up, a support model, and a 90-day backlog all named.

Also wrote the actual end-to-end proof this story's DoD calls for:
`test_full_22_stage_engagement_completes_end_to_end` launches
`POST /engagements/global-retail`, then for all 22 stages in order —
reading each stage's *authored* config from `GLOBAL_RETAIL_STAGES` directly
rather than the API response, since `_redact_technical_task`
(`app/routers/scenario_instances.py`, FDE-013) strips `reference_query`
from every response the way it should for a real student — submits the
correct content (the real `reference_query` for Stage 3's technical_task,
generated compliant prose for every other stage) and approves it via
`PATCH .../decision`. A small generic-content helper
(`_generic_compliant_content`) builds a negation-free sentence per
`must_include` rule from each stage's own checklist rather than hand-
duplicating 21 stages' worth of fixtures already covered individually by
each stage's own test file. Ran clean on the first attempt — no bugs found
in FDE-017's sequencing or FDE-023's context-carry logic at full scale.
Confirms: all 22 stages unlock and grade correctly in sequence, the
`Engagement` reaches `status == "completed"` with `completed_at` set, and
the final accumulated `context` has exactly keys `"0"` through `"21"`.

Tests: `backend/tests/test_global_retail_stage21.py` (8 tests: 7 unit +
the full end-to-end walk) — config validates, no technical_task/data_gen,
persona doesn't dump facts unprompted, persona confirms no-FDE-on-call,
compliant pack passes, three negative cases (missing runbook, missing
support model, missing backlog) each fail their specific rule, and the
full 22-stage completion test. Full backend suite: 321 passed (up from 312
before this story).

This completes content authoring for "The FDE Engagement Framework" —
all 6 missions, 22 stages, fully authored and gradable end to end via one
API call plus 22 approvals. FDE-017 through FDE-040 (24 stories: 1
sequencing primitive, 1 mid-course platform fix, 22 stage-content stories)
are all Done.
