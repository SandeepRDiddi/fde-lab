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
_(appended by the agent as work happens)_
