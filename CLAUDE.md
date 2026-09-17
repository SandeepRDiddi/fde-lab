# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is right now

FDE Lab is a training platform (simulated FDE client engagements for AI/Data
professionals). Application services are landing one story at a time (see
`STORIES.md`); `frontend/`, `lti-service/`, and `mocks/` don't exist yet —
don't invent commands for services that aren't built. `orchestrator/` is
tooling (a LangGraph script that drives story implementation), not an
application service.

Each Python service (`backend/`, `data-gen/`, `persona-service/`) is
independent — its own `requirements.txt`, no shared venv, no dependency on
the others' packages (they only talk to each other over HTTP or a shared
Postgres instance, per `architecture.md`). Standard pattern for each:

```bash
cd <service> && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
FDE_DATABASE_URL="sqlite:///:memory:" .venv/bin/pytest -q   # backend only needs this env var
.venv/bin/pytest -q                                          # data-gen, persona-service
```

`backend/` and `persona-service/` both use Alembic; check the migration
chain has one head after adding a migration (especially relevant right after
rebasing a long-lived branch onto `main`):

```bash
cd <service> && .venv/bin/python -c "
from alembic.config import Config
from alembic.script import ScriptDirectory
script = ScriptDirectory.from_config(Config('alembic.ini'))
print('heads:', script.get_heads())"
```

Add lint/typecheck commands here once a story introduces them — none exist yet.

## Document hierarchy — read in this order

1. **`intent.md`** — the *what and why*. Product intent, audience, scope of
   v1. This wins if any other doc disagrees with it.
2. **`architecture.md`** — the *how*. Technical design, component
   responsibilities, repo layout, deployment plan. Must stay aligned with
   `intent.md`.
3. **`ROADMAP.md`** — phased build plan (Phase 1 Docker Compose core loop →
   Phase 2 multi-cohort validation → Phase 3 LTI/LMS integration → Phase 4
   Kubernetes).
4. **`STORIES.md`** — backlog index (ID, priority, dependencies, status). The
   `Status` column here must stay in sync with each story file's own
   `Status` field.
5. **`stories/FDE-0XX-*.md`** — individual stories, each with a user story,
   EARS-format acceptance criteria, a "Definition of done" checklist, an
   `Architecture ref` pointing at the relevant `architecture.md` section, and
   an `## Implementation log` appended to as work happens.

**Standing rule:** if implementing a story reveals a deviation from
`architecture.md` (different library, changed schema, etc.), fold that
change back into `architecture.md` in the same PR rather than letting the
docs drift from the code. Same logic applies one level up: a scope change
belongs in `intent.md` first, with `architecture.md`/`ROADMAP.md` updated to
match.

## Agent workflow (see `AGENT-WORKFLOW.md` for full detail)

- One story per feature branch: `feature/FDE-00X-slug`.
- A coding agent is given only the story file + the matching `architecture.md`
  section as context — not the whole repo history.
- Acceptance criteria drive the implementation; PR description is generated
  from them, each checked off as satisfied.
- Commits are conventional-commit style referencing the story ID, e.g.
  `feat(data-gen): add schema-drift injector (FDE-003)`.
- Plain git + PR + human review is the real checkpoint — nothing merges
  automatically.
- On merge: update the story's `Status` field and the matching row in
  `STORIES.md`, and append a one-line entry to `CHANGELOG.md`.

### Stale branches are the norm, not the exception

The orchestrator forks each story's branch from `main` at pick-up time, but
runs stories sequentially while review/merge happens after the fact — so a
later story's branch is routinely forked *before* an earlier one actually
merges. Concretely: `feature/fde-003-*` and `feature/fde-004-*` were both cut
before FDE-002 merged, so both were missing FDE-002's `ScenarioInstance`
columns entirely and both reused Alembic revision id `0002` (a collision with
FDE-002's already-merged migration of the same number). Before merging any
PR that touches a file another already-merged story also touched: `git merge
main` into the PR branch first, resolve conflicts (they're usually clean
"both sides added something" conflicts, not real logic clashes), and
renumber any colliding Alembic revision so the chain has one head (see the
alembic heads check above) — don't just squash-merge a stale branch as-is.

### Story eligibility

A story in `STORIES.md` is eligible to pick up only when its status is "Not
started" **and** every ID in its `Depends on` column is already "Done".
Priority (`P0` before `P1`) breaks ties. See `STORIES.md`'s "Pick-up order"
section for the current P0/P1 breakdown.

### Running the unattended orchestrator

```bash
pip install langgraph                     # one-time
gh auth login                             # one-time, GitHub CLI
claude --version                          # confirm logged in interactively at least once

python orchestrator/orchestrator.py                                          # foreground
nohup python orchestrator/orchestrator.py > orchestrator_stdout.log 2>&1 &   # background
```

It loops: pick next eligible story from `STORIES.md` → branch → run
`claude -p` headless against that story → commit/push → `gh pr create` →
mark the story "In review" → repeat, until nothing eligible remains or a
20-story safety cap is hit. It runs against the interactive Claude
subscription (`claude` CLI), not the API directly, so the machine needs to
stay awake and `claude` needs to already be authenticated. Nothing it does
ever merges to `main` — PR review is still the real checkpoint. A failing
step (bad git state, crashed agent call, empty diff, stale branch, duplicate
PR) is caught, logged to `orchestrator.log`, and the story is skipped for
that run rather than halting the loop; partial work is preserved on its
branch as a `wip:` commit. Logs: `orchestrator.log` (structured) and
`orchestrator_stdout.log` (raw stdout, background runs only).

## Architecture at a glance

See `architecture.md` for full detail; the load-bearing shape:

- **Frontend**: single Next.js app, role-gated between student and instructor
  views (not split into separate apps).
- **Backend**: FastAPI service + Celery/Redis for everything time-based
  (scenario unlock/close, scripted mid-scenario pivots).
- **Persona service**: Claude, routed through PromptOps Gateway (not called
  directly) for centralized usage governance/observability.
- **Enterprise mocks**: three sub-components — legacy API simulator,
  compliance checklist engine, approval workflow state machine — reproducing
  "someone else's constraints" friction. Not yet decided whether these ship
  as separate services or route-namespaced within the backend for v1 (see
  `architecture.md`'s open questions).
- **Data-gen**: synthetic dataset generator that runs once per cohort setup
  (not randomized, not shared/reused across cohorts) — nulls, duplicates,
  schema drift, fake PII.
- **LTI launch service**: Phase 3 — LTI 1.3 / OIDC handshake mapping an LMS
  course/cohort onto a scenario instance.
- **Deployment**: Docker Compose through Phase 1-3 (every service
  containerized regardless); Kubernetes in Phase 4 adds per-cohort namespaces
  once concurrent multi-cohort/multi-course load is real. Compose remains the
  local dev target even after Kubernetes is production.

Planned repo layout (most of these directories don't exist yet — see
`architecture.md` → "Repository layout" for the authoritative version):

```
frontend/ backend/ persona-service/ lti-service/ mocks/ data-gen/
orchestrator/   # exists today — LangGraph story-picker
infra/docker-compose.yml   infra/k8s/
```
