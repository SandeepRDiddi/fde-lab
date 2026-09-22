# FDE-033: GlobalRetail engagement — Stage 14 (Evaluation & Testing)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-030, FDE-032
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 14 to make me build real evaluation coverage —
functional, agent-behavior, RAG-accuracy, adversarial/security, and
regression — against real held-out data and security's own adversarial
prompts, so "it worked once" stops being an acceptable bar.

## Motivation

Fifteenth stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[14]`. Per the framework: **Situation** — "it answered
my question correctly once" is not evidence the platform is ready for
real, ongoing use. **Assets** — a held-out set of real, anonymized support
tickets, adversarial prompts supplied by the security team. **FDE must** —
build functional, agent-behavior, RAG-accuracy, security, and regression
evaluation — not a vibe check. **GlobalRetail specifics** — "ready for real
use" means ready for 1,200 stores' worth of concurrent, messy questions.
**Deliverable** — Evaluation Harness.

Persona is Jordan Lee, reused a fifth time (Stages 1/4/11), supplying the
adversarial-prompts half of the assets — a natural extension of the
security-review role established in Stage 11, not a new responsibility for
the character.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[14]` with a persona
   (Jordan Lee) that, only on request, describes the held-out ticket set
   and hands over adversarial prompts from security, and states the real
   bar: ready for 1,200 stores' worth of concurrent, messy questions, not
   one clean demo.
2. THE `compliance_checklist` SHALL gate the Evaluation Harness deliverable
   on naming all five evaluation categories the framework specifies:
   functional, agent-behavior, RAG-accuracy, adversarial/security, and
   regression.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 14, locked until stage 13's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[14]` authored (persona + compliance_checklist)
- [x] Tests: stage 14 config validates, persona doesn't leak facts
      unprompted, a compliant harness writeup passes the checklist, each
      missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[14]` in
`backend/app/engagement_content/global_retail.py`. Persona is Jordan Lee,
reused a fifth time (Stages 1/4/11), extending the security-review role
from Stage 11 into supplying adversarial test prompts. Reveals the
held-out ticket set, the adversarial prompts, and the real "1,200 stores'
worth of concurrent, messy questions" readiness bar only on request.
`compliance_checklist` requires all five evaluation categories the
framework names by name: functional, agent-behavior, RAG-accuracy,
adversarial, and regression.

Tests: `backend/tests/test_global_retail_stage14.py` (8 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona states the 1,200-store readiness bar, compliant harness
passes, and three negative cases (missing agent-behavior, missing
adversarial, missing regression evaluation) each fail their specific rule.
Full backend suite: 264 passed (up from 256 before this story).
