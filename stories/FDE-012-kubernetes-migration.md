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


**2026-09-18** — Implemented Kubernetes migration per architecture.md →
Deployment (Phase 4).

Added:
- `infra/k8s/chart/` — Helm chart, one release per cohort. Templates for
  every service `infra/docker-compose.yml` already defines (AC1):
  `postgres`, `redis`, `minio` (Deployment+Service+PVC each), the
  `backend-migrate`/`persona-migrate`/`minio-init` one-shot steps as
  `post-install,post-upgrade` Helm hook Jobs (with `pg_isready`/`mc`
  wait-loops instead of Compose's `depends_on: condition:
  service_healthy`/`service_completed_successfully`, which Kubernetes has
  no direct equivalent for), `backend`, `celery-worker`,
  `persona-service`, `frontend`, and `data-gen` as an on-demand Job
  template (not installed by default, rendered per scenario-instance setup
  — mirrors Compose's `profiles: tools` treatment). A templated `Namespace`
  resource (Helm's built-in kind-priority puts it first, no hook needed)
  gives each cohort its own `cohort-<slug>` namespace (AC2). An `Ingress`
  routes `<cohortId>.<domain>` to the `frontend` Service only — the sole
  public entry point, consistent with the frontend's own server-side
  `/api/*` proxying to `backend`/`persona-service` (AC3). Two
  `NetworkPolicy` resources default-deny all cross-namespace ingress and
  allow only the ingress-controller's namespace in to `frontend`, so
  `backend`/`celery-worker`/`persona-service`/Postgres/Redis/MinIO — and
  therefore each cohort's synthetic data, mock-adjacent state, and
  scenario/submission rows — stay unreachable from any other cohort's
  namespace (AC4).
- `infra/k8s/provisioner/` — small standalone FastAPI service (`POST
  /provision/{cohort_id}`) that runs `helm upgrade --install` against the
  chart. Deliberately separate from `backend` rather than an in-process
  call: it's the one component that needs cluster credentials broad enough
  to create namespaces, and giving that to the public-facing
  student/instructor API would be a privilege-escalation smell. Idempotent
  (`--install` on an existing release rolls forward rather than erroring).
  Own `Dockerfile` (bundles `helm`+`kubectl`, neither in `python:3.11-slim`
  by default; build context is `infra/k8s/`, not the service dir, so it
  can also `COPY` the chart in — documented in the Dockerfile and
  `infra/k8s/README.md`), `requirements.txt`, `pytest.ini`, and
  `tests/` (`test_provision.py` covers slugification incl. collapsing runs
  of invalid characters and the 53-char/no-trailing-dash truncation edge
  case, idempotent-call behavior, and helm-failure propagation via a fake
  `subprocess.run`; `test_main.py` covers the HTTP layer via
  `TestClient`+`monkeypatch`, no real cluster needed for either).
- `infra/k8s/provision_cohort.py` — thin CLI wrapper around the same
  provisioning logic, for direct/ops/CI use against a repo checkout
  without a network hop to the provisioner service.
- `backend/app/routers/cohorts.py` — `POST /cohorts/{cohort_id}/provision`,
  the instructor-action trigger from AC2: calls the provisioner over HTTP
  (`backend/app/config.py` gained `k8s_provisioner_url`), 502s cleanly if
  it's unreachable or itself errors. No new `cohorts` table — `cohort_id`
  stays an opaque identifier exactly as it already was on
  `ScenarioInstance` (`app/models.py`); namespace existence in the cluster
  is the source of truth for "provisioned," not a Postgres row. Registered
  in `app/main.py`. `backend/tests/test_cohorts.py` covers the success
  path, an unreachable provisioner, and a provisioner-side error, all via
  `monkeypatch` on `httpx.post` (no real provisioner/cluster needed).
- `infra/k8s/README.md` — usage (provisioning a cohort, running `data-gen`
  per scenario instance), the RBAC rationale for the separate provisioner,
  and everything below under "Deviations / gaps."
- `architecture.md` — rewrote the Phase 4 paragraph under Deployment to
  match what's actually built (chart shape, provisioner service + why it's
  separate, ingress/NetworkPolicy design), updated the Repository layout
  tree for `infra/k8s/`, and resolved the "Namespace provisioning trigger"
  open question for the instructor-action path (also cleaned up an
  apparent stray duplicate of that same bullet already sitting in the Open
  questions section — unrelated leftover, not something this story
  introduced).

**Deviations / gaps:**
- **AC2's LTI-launch trigger is not wired up.** Only the instructor-action
  path (`POST /cohorts/{cohort_id}/provision`) is real. Reason, in full in
  `infra/k8s/README.md`: `backend` still has no `/internal/lti-mappings`
  endpoint at all (the gap FDE-011's implementation log already flagged —
  `lti-service/app/scenario_client.py` calls a contract that doesn't exist
  on this branch), so there's no real "a new cohort showed up via LTI"
  event to hang a trigger off of yet; and auto-provisioning a cluster
  namespace off of an unauthenticated student's launch hitting a 404 would
  itself be a resource-exhaustion vector, not just an incomplete feature.
  Once `/internal/lti-mappings` gains a real *create* path (an instructor
  linking an LMS course to a cohort), that's the point to call the same
  provisioner — left as explicit follow-up rather than solved here or
  faked with an unsafe shortcut.
- **Scope of AC1 read literally.** `chart/` covers every service
  `infra/docker-compose.yml` already defines, plus Postgres/Redis/MinIO —
  not `lti-service/` (has a Dockerfile but was never added to
  `docker-compose.yml`, and is conceptually a shared/platform-level
  service, not per-cohort) or `mocks/legacy-api/`/`mocks/compliance-engine/`
  (neither containerized nor wired into Compose either). Detailed in
  `infra/k8s/README.md`'s "Scope: what isn't in the chart."
- **Known bootstrap race.** `backend`/`celery-worker`/`persona-service`
  are normal chart resources, so their pods start around the same time as
  the `backend-migrate`/`persona-migrate` post-install hook Jobs, not
  strictly after — each waits for Postgres to accept connections but not
  for migration to finish, so a cohort's very first install has a short
  window where a request could reach `backend` before its schema exists.
  Common, generally-accepted limitation of "migrations as a separate Job"
  in Kubernetes; documented rather than fixed with extra Job-status-read
  RBAC for this story.
- No `architecture.md` deviation beyond the Phase 4 rewrite above — the
  chart/provisioner/ingress/NetworkPolicy shape matches what `ROADMAP.md`
  already committed to (manifests or Helm chart, per-cohort namespace
  provisioned automatically, ingress routing per cohort); the one addition
  not previously spelled out is the separate provisioner service for RBAC
  isolation, now documented.

**Verification and its limits:** no live Kubernetes cluster was reachable
in this session (`kubectl` on PATH with no configured/reachable context;
`helm` not installed at all), and the sandboxed Bash tool blocked venv
creation and `pip install` outright (no approval was obtainable
interactively), so none of the new Python (`infra/k8s/provisioner/`,
`backend/app/routers/cohorts.py` + its test) was actually executed here —
same class of environment constraint FDE-010's and FDE-011's merge reviews
hit with Docker/network access. Everything was reviewed by hand instead:
template rendering logic and Helm resource-kind/hook ordering, env var
names matched 1:1 against `infra/docker-compose.yml` and each service's
`app/config.py`, namespace/label/selector consistency across all
templates, and the new Python by tracing test cases against the code by
hand line-by-line (this caught and fixed a real bug pre-review: the
slugify regex needed a `+` quantifier to collapse runs of invalid
characters, and truncation needed a second trailing-dash strip after the
53-char cut, both now covered by `test_provision.py`). Both DoD items below
(two cohorts running concurrently, namespace provisioning firing
automatically end to end against a real cluster) are consequently still
unverified against a live cluster — whoever has one available should run
this before checking those boxes.
