# FDE-004: AI persona service

**Status:** Not started
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
- [ ] Persona holds a coherent multi-turn conversation in a manual test
- [ ] Usage is visible in PromptOps Gateway logs
- [ ] Story status updated below
- [ ] architecture.md updated if the persona approach deviates from documented

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

_(appended by the agent as work happens)_
