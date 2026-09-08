# FDE-002: Time-box scheduler

**Status:** Not started
**Priority:** P0
**Depends on:** FDE-001
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis

## User story
As an instructor, I want scenarios to automatically unlock and close on the schedule
I configure, so that the cohort experiences a time-boxed engagement without manual
intervention.

## Acceptance criteria (EARS)
1. WHEN an instructor sets a start and end time for a scenario instance, THE
   scheduler SHALL enqueue an unlock job and a close job in Celery/Redis for those
   times.
2. WHEN the unlock job fires, THE scenario engine SHALL transition the scenario
   instance to "active" and notify the student.
3. WHEN the close job fires, THE scenario engine SHALL transition the scenario
   instance to "closed" and lock further submissions.
4. IF an instructor configures a mid-scenario pivot time, THEN THE scheduler SHALL
   enqueue a pivot job that injects the configured change at that time.

## Definition of done
- [ ] Scheduled jobs verified against a test cohort with compressed timings
- [ ] Story status updated below
- [ ] architecture.md updated if the scheduling model deviates from what's documented

## Implementation log
_(appended by the agent as work happens)_
