# FDE Lab — Architecture

This document is the technical companion to `intent.md`. `intent.md` defines *what*
FDE Lab is and *why* it's built the way it is; this document defines *how* it's built.
If the two ever disagree, `intent.md` wins on intent and this document should be
updated to match — this file exists to serve that vision, not the other way around.

## System overview

FDE Lab is a platform, not a content bundle. Students log into a scheduled,
time-boxed scenario workspace; instructors configure and monitor cohorts from a
console in the same app. Under the hood, a scenario engine orchestrates timing and
state, an AI persona service plays the stakeholder/client role, a set of enterprise
system mocks reproduce real-world constraints, and everything reads/writes to a
shared data layer.

```
Student browser ──┐
                   ├──> FDE Lab platform ──> Data & storage
Instructor console ┘         │
                              ├── Scenario engine (FastAPI + Celery scheduler)
                              ├── AI persona (Claude via PromptOps Gateway)
                              └── Enterprise system mocks (legacy API, compliance, approvals)
```

## Components

### Frontend — single Next.js app, role-gated
Students and instructors share one app, gated by role:
- **Student view**: scenario workspace — AI-persona chat, incoming artifact/ticket
  feed, data explorer for the synthetic dataset, submission panel.
- **Instructor view**: cohort configuration, scenario scheduling, live progress
  monitoring across the cohort.

### Backend — FastAPI + Celery/Redis
A Python/FastAPI service owns scenario state, submissions, and the websocket
connection for the persona chat (streaming, not just request/response — the
demo/defend moments need to feel live). Celery + Redis handle everything
time-based:
- Unlocking a scenario at its scheduled time
- Auto-closing a scenario when its time-box expires
- Firing a scripted mid-scenario pivot (the "client changes their mind" moment) at a
  cohort-configured time

This mirrors the FastAPI + Celery + Redis stack already proven on `genai-pulse-bot`.

### AI persona service — Claude via PromptOps Gateway
Each scenario defines a persona: a system prompt encoding personality, agenda, and
what the persona does/doesn't know, plus per-student conversation state. Persona
calls route through [[promptops-gateway]] rather than hitting the Claude API
directly — this gives centralized usage governance and observability across the
whole training program for free, reusing infrastructure that already exists instead
of building it twice.

### Enterprise system mocks
Three purpose-built services reproducing the "someone else's constraints" friction:
- **Legacy API simulator** — mock REST endpoints with intentionally quirky behavior
  (inconsistent schemas, latency, auth friction)
- **Compliance checklist engine** — a rules-based gate a submission must satisfy
  before it can "ship"
- **Approval workflow** — a state machine (submitted → pending → approved/rejected),
  optionally with a built-in delay to simulate a real review cycle

### Synthetic data generation
A standalone module that runs at **cohort setup time**, not randomly or on a fixed
schedule. Given a scenario config (domain, target messiness, schema), it generates
that cohort's dataset fresh — nulls, duplicates, schema drift, fake PII to mask — so
no two training runs reuse the same data.

### Data layer
- **Postgres** — cohorts, students, scenario definitions, submissions, scores
- **Redis** — task queue and live session state for time-boxing
- **Object storage** (S3-compatible — R2 or S3) — synthetic datasets, artifact
  documents, submitted deliverables

## Repository layout

```
fde-lab/
  frontend/        # Next.js app (student + instructor views)
  backend/         # FastAPI service + Celery workers
  persona-service/ # Claude persona logic, routed via PromptOps Gateway
  mocks/           # legacy API sim, compliance engine, approval workflow
  data-gen/        # synthetic dataset generator
  infra/           # Docker, deploy config
  intent.md
  architecture.md
```

## Deployment

**v1 target: Railway**, using the same FastAPI + Celery + Redis combination already
proven on `genai-pulse-bot` — no new deployment toolchain, fastest path to a working,
demoable end-to-end system (matching the v1 scope in `intent.md`: no smaller starting
slice, full client-ready demo).

**Future path**: if FDE Lab graduates from demo into something run inside an actual
training program's infrastructure (UST, NIIT/StackRoute, or anything with stricter
data-handling expectations), the natural migration is containerizing the services and
moving to per-cohort isolated environments on a cloud provider. This is a
post-validation migration, not a v1 blocker.

## Traceability to intent.md

| Intent.md requirement | Architecture answer |
|---|---|
| Flexible scenario engine, cohort-calibrated | Scenario engine service + per-cohort scenario config |
| Synthetic data generated fresh per run | Data-gen module, triggered at cohort setup |
| AI-driven persona (stakeholder + demo audience) | Persona service on Claude, via PromptOps Gateway |
| Enterprise constraints (legacy systems, compliance, approvals) | Mocks service (three sub-components) |
| Scheduled, time-boxed cohort pacing | Celery + Redis scheduling in the backend |
| Solo scenarios, team capstone | Data model supports both individual and team-scoped submissions |
| End-to-end, client-ready v1 (no smaller slice) | Railway deployment of the full stack above, not a partial slice |

## Open questions

- Auth model for v1 (email/magic-link vs SSO)
- How persona personality/agenda gets authored per scenario (config format, tooling)
- Exact parameterization schema for the data generator (what "messiness" knobs exist)
- Whether the legacy API mock, compliance engine, and approval workflow are separate
  services or route-namespaced within the main backend for v1
