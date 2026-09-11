# FDE-012: Kubernetes migration

**Status:** Not started
**Priority:** P1
**Depends on:** FDE-010, FDE-011
**Architecture ref:** architecture.md → Deployment (Phase 4)

## User story
As a platform owner, I want FDE Lab running on Kubernetes with per-cohort
isolation, so that multiple courses and cohorts can launch concurrently without
interfering with each other.

## Acceptance criteria (EARS)
1. THE deployment SHALL provide Kubernetes manifests (or a Helm chart) for every
   containerized service already defined for Docker Compose.
2. WHEN a new cohort is provisioned (via LTI launch or instructor action), THE
   platform SHALL create an isolated Kubernetes namespace for that cohort.
3. THE deployment SHALL route requests to the correct cohort's namespace via
   ingress.
4. WHILE multiple cohorts are active at once, THE platform SHALL keep each
   cohort's synthetic data, mock services, and scenario state fully isolated from
   the others.

## Definition of done
- [ ] Two cohorts run concurrently on the cluster in separate namespaces without
      cross-contamination
- [ ] Namespace provisioning is triggered automatically, not manual per cohort
- [ ] Story status updated below
- [ ] architecture.md updated if the Kubernetes approach deviates from documented

## Implementation log
_(appended by the agent as work happens)_


## Implementation log
_(appended by the agent as work happens)_
