# FDE Lab — story backlog

Full stories live in `stories/`. This index tracks priority, status, and
dependencies at a glance — the source of truth for status is still each story
file's own `Status` field; keep this table in sync when a story moves.

**Status legend:** Not started → In progress → In review → Done

| ID | Title | Priority | Depends on | Status |
|---|---|---|---|---|
| FDE-001 | Scenario engine skeleton | P0 | — | Not started |
| FDE-002 | Time-box scheduler | P0 | FDE-001 | Not started |
| FDE-003 | Synthetic data generator v1 | P0 | — | Not started |
| FDE-004 | AI persona service | P0 | FDE-001 | Not started |
| FDE-005 | Legacy API mock service | P1 | — | Not started |
| FDE-006 | Compliance checklist engine | P1 | — | Not started |
| FDE-007 | Approval workflow state machine | P1 | FDE-006 | Not started |
| FDE-008 | Student scenario workspace (frontend) | P0 | FDE-001, FDE-004 | Not started |
| FDE-009 | Instructor console (frontend) | P1 | FDE-001, FDE-002 | Not started |
| FDE-010 | Railway deployment pipeline | P0 | FDE-001, FDE-002, FDE-003, FDE-004 | Not started |

## Pick-up order

A story is only eligible once everything in its "Depends on" column is Done. The
P0 stories (001, 002, 003, 004, 008, 010) together constitute the full end-to-end
v1 demo committed to in `intent.md` — the P1 stories (005, 006, 007, 009) round out
the remaining enterprise-friction and instructor-facing pieces.

See `AGENT-WORKFLOW.md` for how a story moves from this table into working, merged,
documented code.
