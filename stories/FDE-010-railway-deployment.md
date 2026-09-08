# FDE-010: Railway deployment pipeline

**Status:** Not started
**Priority:** P0
**Depends on:** FDE-001, FDE-002, FDE-003, FDE-004
**Architecture ref:** architecture.md → Deployment

## User story
As a platform owner, I want the full stack deployed to Railway with one pipeline,
so that the end-to-end demo is actually reachable outside a local machine.

## Acceptance criteria (EARS)
1. THE deployment pipeline SHALL build and deploy the FastAPI backend, Celery
   workers, persona service, and frontend as separate Railway services.
2. THE deployment pipeline SHALL provision Postgres, Redis, and object storage
   bindings for those services.
3. WHEN a change is pushed to main, THE deployment pipeline SHALL redeploy the
   affected services automatically.

## Definition of done
- [ ] A full scenario can be run end to end against the deployed Railway environment
- [ ] Story status updated below
- [ ] architecture.md updated if the deployment approach deviates from documented

## Implementation log
_(appended by the agent as work happens)_
