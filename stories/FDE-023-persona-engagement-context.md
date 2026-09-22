# FDE-023: Surface engagement context to the persona

**Status:** Done
**Priority:** P0
**Depends on:** FDE-004, FDE-017
**Architecture ref:** architecture.md → AI persona service

## User story
As a student, I want a later engagement stage's persona to actually know
what I produced in an earlier stage — the semantic model I defined, the
architecture I chose — so a "continuous engagement" is real continuity, not
22 stages that happen to share a database row.

## Motivation

Discovered while starting Mission 2's content stories (Stage 5 needs its
persona to reference Stage 4's AI Readiness Matrix): FDE-017's
`_advance_engagement` correctly writes the accumulated context into the next
stage's `config["engagement_context"]`, but `persona-service`'s
`_build_system_prompt` (`app/routers/conversations.py`) only ever reads
`config["persona"]["system_prompt"]` and `config["persona"]["agenda"]` — it
never looks at `config["engagement_context"]` at all. So the context FDE-017
carries forward currently sits inert in the database; nothing surfaces it to
the actual persona conversation a student has. This is a real gap in
FDE-017 itself (found by trying to use it, not a pre-existing issue), fixed
here before any more Mission 2+ content assumes stage-to-stage continuity
actually works end to end.

## Acceptance criteria (EARS)
1. WHEN `config["engagement_context"]` is present and non-empty, THE
   persona's system prompt SHALL be extended with a rendering of each prior
   stage's `submission_content` (ordered by stage number), clearly
   delimited from the persona's own system prompt and agenda.
2. WHEN `config["engagement_context"]` is absent or empty (a standalone
   instance, or an engagement's first stage), THE system prompt SHALL be
   built exactly as before — no empty "Context from earlier stages" section
   appended.
3. THE existing FDE-004 behavior — system prompt rebuilt from current config
   on every turn, so a pivot takes effect on the next message without
   restarting the conversation — SHALL be unchanged; engagement context is
   read the same way, on every turn, not cached.

## Definition of done
- [x] `_build_system_prompt` reads `config["engagement_context"]` (not just
      `config["persona"]`) and renders it into the system prompt when present
- [x] Existing persona-service tests still pass unmodified
- [x] New tests: engagement context renders into the system prompt sent to
      the gateway, absent/empty context changes nothing, ordering is by
      stage number not insertion order
- [x] Story status updated below
- [x] architecture.md updated (AI persona service section)
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — `persona-service/app/routers/conversations.py`: renamed
`_require_persona_config` → `_require_config` (still validates a persona
exists, now returns the whole config instead of just `config["persona"]`),
and `_build_system_prompt` now takes the full config rather than just the
persona sub-dict. When `config["engagement_context"]` is present and
non-empty, each stage's `submission_content` is rendered — sorted
numerically by stage order key (`sorted(..., key=int)`, since dict keys are
strings and lexicographic sort would put "10" before "2") — into a "Context
from earlier stages of this engagement" section appended after the
persona's own system prompt/agenda. Absent or empty context changes nothing
(same prompt shape as before this story), and the read happens on every
turn (same as the rest of config), so it updates the moment an engagement
advances — no conversation restart needed, consistent with FDE-004 AC4's
existing pivot behavior.

Tests: `persona-service/tests/test_engagement_context.py` (4 tests) —
context renders with both the persona's own prompt and the context section
present, absent context changes nothing, empty-dict context changes
nothing, and stage ordering is numeric (verified with keys "10"/"2"/"1"
seeded out of order, where lexicographic sort would have put "10" before
"2"). Full persona-service suite: 18 passed (14 pre-existing + 4 new, all
unmodified). First time `persona-service/.venv` was created in this
environment — set up per CLAUDE.md's standard per-service venv pattern.

architecture.md: AI persona service section updated to describe
`_build_system_prompt` reading `engagement_context`.
