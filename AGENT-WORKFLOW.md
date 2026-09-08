# FDE Lab — agent development workflow

How stories in `stories/` get picked up, built, and documented. Nothing here is
specific to any one employer's internal tooling — every piece is open source or a
standard practice you'd find on most real engineering teams, chosen deliberately so
building FDE Lab is also you learning the tools.

## Tooling

- **Orchestrator:** LangGraph (open source) — a small graph that reads
  `STORIES.md`, checks each story's dependencies, and hands the next eligible one
  to a coding agent session.
- **Coding agent:** a coding agent (e.g. Claude Code) invoked per story, given the
  story file plus the relevant `architecture.md` section as its only context.
- **Version control & review:** plain git — a feature branch per story, a pull
  request, a human review before merge. This *is* the checkpoint; nothing extra is
  layered on top of what any team already does.
- **CI:** GitHub Actions — run tests and lint on every PR.
- **Observability:** Langfuse (open source) — traces every LLM call the persona
  service or the coding agent makes, so cost, latency, and behavior are visible
  across the whole backlog as you build it.

## How a story moves

1. The orchestrator picks the next eligible story from `STORIES.md` — status
   "Not started" and every story in its "Depends on" column already "Done."
2. The coding agent creates a branch: `feature/FDE-00X-slug`.
3. It implements against the story's acceptance criteria and writes tests.
4. It opens a PR. The PR description is generated from the story's own acceptance
   criteria, each item checked off as satisfied.
5. You review the PR like any other PR — that review is the real checkpoint.
6. On merge, CI runs, and the story's status is updated.

## Documentation produced inline

- **Commits** — conventional-commit style, referencing the story ID, e.g.
  `feat(data-gen): add schema-drift injector (FDE-003)`
- **PR description** — built from the story's acceptance criteria, not written
  from scratch
- **Implementation log** — appended directly to the story file (see the
  `## Implementation log` section already in each one), dated, noting what was
  built and any deviation from the original criteria
- **`STORIES.md`** — status column kept in sync as a story moves through
  Not started -> In progress -> In review -> Done
- **`architecture.md`** — if implementation reveals a deviation from the
  documented design (a different library, a changed schema), the same PR includes
  a diff to `architecture.md`, so the three documents (`intent.md` ->
  `architecture.md` -> `stories/`) never drift apart
- **`CHANGELOG.md`** — one line per merged story

## Why this shape

Branch -> PR -> review -> merge -> changelog is how most real teams already work,
agents in the loop or not. The only things added here are: stories as the unit of
work an agent can pick up unambiguously, and a standing rule that any deviation
from `architecture.md` gets folded back into `architecture.md` in the same PR
rather than left to drift.
