# FDE-004: AI persona service

**Status:** Done
**Priority:** P0
**Depends on:** FDE-001
**Architecture ref:** architecture.md → AI persona service — Claude via PromptOps Gateway

## User story
As a student, I want to interact with an AI-driven stakeholder persona that
reflects the scenario's ambiguity and agenda, so that I practice translating a
vague ask into a spec.

## Acceptance criteria (EARS)
1. WHEN a student sends a message in an active scenario, THE persona service SHALL
   respond using the persona's configured system prompt for that scenario.
2. THE persona service SHALL route all model calls through PromptOps Gateway.
3. THE persona service SHALL persist conversation history per student per scenario
   instance.
4. WHEN a scenario's mid-engagement pivot fires, THE persona service SHALL
   incorporate the updated agenda into subsequent responses without restarting the
   conversation.

## Definition of done
- [x] Persona holds a coherent multi-turn conversation in a manual test (verified
      via automated test suite — `test_conversation_history_persists_across_turns`,
      `test_pivot_updates_agenda_without_resetting_conversation`; no live
      PromptOps Gateway/manual session available in this environment)
- [ ] Usage is visible in PromptOps Gateway logs (no live gateway in this
      environment — can't verify; gateway's wire contract itself is still an
      assumption, see architecture.md's open questions)
- [x] Story status updated below
- [x] architecture.md updated if the persona approach deviates from documented

## Implementation log

### 2026-09-17

Built `persona-service/` as its own FastAPI app (matches the `persona-service/`
entry already in architecture.md's repository layout), depending on FDE-001's
`scenario_instances` table for scenario/persona config:

- `app/scenario_ref.py` reads/writes `scenario_instances.config` directly against
  the shared Postgres instance (no HTTP call to the backend) to get/set
  `config["persona"] = {"system_prompt", "agenda"}`. This table is deliberately
  outside this service's own `Base`/Alembic metadata — the backend's FDE-001
  migration stays the sole owner of creating/altering `scenario_instances`.
- `app/models.py` — `Conversation` (one per scenario instance + student, unique
  constraint) and `Message` (role: student/persona, content, timestamp) own the
  persisted chat history (AC3). Own Alembic migration
  (`0001_create_conversations_and_messages.py`).
- `app/gateway.py` — `PromptOpsGatewayClient` is the only path to a model call
  (AC2); it POSTs to `{PROMPTOPS_GATEWAY_URL}/v1/messages`.
- `POST /scenario-instances/{id}/messages` — appends the student's message,
  rebuilds the system prompt from the scenario's *current* persona config on
  every turn, calls the gateway with full history, persists and returns the
  persona's reply (AC1).
- `GET /scenario-instances/{id}/messages?student_id=` — returns full history.
- `POST /scenario-instances/{id}/persona/pivot` — updates `config["persona"]["agenda"]`
  in place. Because the system prompt is rebuilt from config on every turn rather
  than cached on the conversation, the next message after a pivot reflects the new
  agenda without creating a new conversation or losing history (AC4). This is the
  hook FDE-002's pivot job is expected to call when it fires — FDE-002 itself was
  not implemented here.

Deviations / assumptions, folded into architecture.md's "AI persona service" and
"Open questions" sections:
- Persona config format (previously an open question) is now decided: JSON on
  `scenario_instances.config["persona"]`. Authoring *tooling* for that config is
  still open — instructors currently need to write it by hand/API call.
- PromptOps Gateway's actual wire contract isn't documented anywhere in this repo.
  `app/gateway.py` assumes it proxies the Anthropic Messages API shape (`model` /
  `system` / `messages` in, text out). Worth confirming against the real gateway
  before Phase 1 integration.

Testing: `persona-service/tests/test_conversations.py` covers AC1-AC4 (persona
system prompt usage, 404/400 on missing scenario/persona, per-student history
scoping, multi-turn persistence, and the pivot-without-restart behavior) against a
fake gateway client and an in-memory SQLite DB seeded with a `scenario_instances`
row. **Not executed in this session** — this sandbox denied approval for every
`pip install` / `pytest` invocation, so the "Persona holds a coherent multi-turn
conversation in a manual test" DoD item is unverified pending a run of
`cd persona-service && pip install -r requirements.txt && pytest` outside this
sandbox.

### 2026-09-18 (merge review)
Code-reviewed PR #16 and fixed before merge:
- `gateway.py` parsed the gateway response as `data["content"]` assumed to be
  a plain string, but the Anthropic Messages API shape this client's own
  docstring says it assumes returns `content` as a list of content blocks.
  Now normalizes either shape to text.
- `pivot_persona` used `config.setdefault("persona", {})`, which doesn't
  replace an existing key whose value is `None` — crashed with
  `TypeError` on the next line. Fixed to check `isinstance(..., dict)`.
- `_get_or_create_conversation` had a check-then-insert race on the
  `(scenario_instance_id, student_id)` unique constraint — two concurrent
  first messages could both pass the SELECT and the second would hit an
  unhandled `IntegrityError`. Now catches it and re-reads the row a
  concurrent request already created.
- Reused a single pooled `httpx.Client` in `PromptOpsGatewayClient` instead
  of a fresh connection per call (every chat turn is a hot-path gateway
  call).
- De-duplicated the conversation-lookup query shared by `send_message` and
  `get_conversation` into `_find_conversation`.
- **Cross-story bug surfaced by this review**: the implementation log above
  says the `/persona/pivot` endpoint is "the hook FDE-002's pivot job is
  expected to call," but FDE-002 (already merged) never calls it — its
  Celery task merges `pivot_config` into `config` directly in Postgres, with
  a *shallow* merge. A real pivot setting
  `pivot_config={"persona": {"agenda": "..."}}` would have replaced the
  entire `persona` object, dropping `system_prompt`, and broken the next
  message with a 400. Fixed in `backend/app/tasks.py`
  (`_merge_pivot_config`): the merge is now one-level-deep, so a `persona`
  key in `pivot_config` updates matching fields without clobbering siblings.
  Corrected architecture.md's "AI persona service" section to describe what
  actually happens (two independent paths reach `config["persona"]`, neither
  calls the other) rather than the aspirational call-chain it previously
  described.
- Also updated the root `CLAUDE.md`, which had fallen behind: added
  build/test commands for `backend/`, `data-gen/`, `persona-service/` (all
  landed since it was written) and a note on the stale-branch/migration
  collision pattern this review kept hitting.

`pytest -q`: persona-service 10 passed (2 new: null-persona pivot, gateway
content-list parsing, plus a race-condition regression test), backend 20
passed (1 new: nested-dict pivot merge). Merged via squash, PR #16 closed,
branch deleted.

### 2026-09-18 (validation pass, found during FDE-010's live docker compose run)
`PromptOpsGatewayClient.complete()` had no error handling around its
`httpx.post` call — an unreachable gateway (the everyday case, since
PromptOps Gateway isn't part of this repo) raised an unhandled exception
straight through `send_message`, returning a bare 500 and leaving the
student's message flushed-but-uncommitted in a half-written state. Caught
live: sent a real chat message against a running `persona-service` with no
gateway behind it and got exactly that. Fixed: `complete()` now raises a
clear `GatewayError` on any `httpx.HTTPError`, and `send_message` catches
it, rolls back the half-turn, and returns a 502 with a readable detail
instead. Added `test_send_message_gateway_failure_returns_502_and_rolls_back`;
`pytest -q`: 11 passed.

_(appended by the agent as work happens)_
