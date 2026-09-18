# FDE Lab — Kubernetes deployment (Phase 4, FDE-012)

`architecture.md` → Deployment → Phase 4 is the authoritative description;
this is the how-to. Docker Compose (`infra/docker-compose.yml`) remains the
local development target — nothing here changes that file or how Phase 1-2
works.

## Layout

- `chart/` — Helm chart. One release == one cohort's full, isolated stack:
  own namespace (`cohort-<slug>`), Postgres, Redis, MinIO, `backend`,
  `celery-worker`, `persona-service`, `frontend`. Mirrors
  `infra/docker-compose.yml` service-for-service.
- `provisioner/` — small standalone FastAPI service, `POST
  /provision/{cohort_id}`, that runs `helm upgrade --install` against
  `chart/`. The only component in the platform meant to hold cluster
  credentials broad enough to create namespaces — kept separate from
  `backend` on purpose (see "Why a separate provisioner service" below).
  Deployed once at the platform level (its own namespace, e.g.
  `fde-lab-platform`), not per cohort.
- `provision_cohort.py` — CLI wrapper around
  `provisioner/app/provision.py`'s same logic, for direct/ops/CI use
  against a repo checkout without going over HTTP to the provisioner
  service.

## Provisioning a cohort

Automatic, not manual (FDE-012 DoD): the instructor-action trigger is
`POST /cohorts/{cohort_id}/provision` on `backend`
(`backend/app/routers/cohorts.py`), which calls the provisioner service
over HTTP. There is no human running `helm install` by hand per cohort.

For ops/CI use directly against a checkout:

```bash
python infra/k8s/provision_cohort.py acme-univ-cs101-fall26
# -> creates/updates namespace cohort-acme-univ-cs101-fall26 with the full stack
```

Both paths are idempotent — calling either twice for the same `cohort_id`
is safe (`helm upgrade --install` rolls an existing release forward rather
than erroring), since the DoD requires namespace *provisioning* to be
automatic, not that callers de-duplicate their own trigger events.

## Running data-gen for a scenario instance

`data-gen` isn't a standing workload in the chart either (same as its
`profiles: tools` treatment in `infra/docker-compose.yml`) — render and
apply its Job template per scenario-instance setup:

```bash
helm template infra/k8s/chart --set cohortId=acme-univ-cs101-fall26 \
  --set dataGen.scenarioInstanceId=<instance-id> \
  --show-only templates/data-gen-job.yaml | kubectl apply -n cohort-acme-univ-cs101-fall26 -f -
```

## Why a separate provisioner service

`backend` is the student/instructor-facing API — reachable from outside
the cluster (through each cohort's own `Ingress`). Giving that pod a
`ServiceAccount` capable of creating namespaces cluster-wide would mean
any compromise of a public-facing pod compromises the whole cluster's
tenancy boundary. The provisioner is a second, narrowly-scoped service
(`RBAC`: create/get on `namespaces`, plus whatever a Helm install needs
inside the namespaces it creates) that `backend` calls over HTTP instead
of embedding that capability in-process — the same shape this repo already
uses for `lti-service` and the enterprise mocks (small standalone service
per concern, not a route folded into `backend/`).

## Known gap: LTI-launch trigger

FDE-012 AC2 asks for provisioning "via LTI launch or instructor action."
Only the instructor-action path is wired up. The LTI-launch path isn't,
for two reasons:

1. `backend` has no `/internal/lti-mappings` endpoint at all yet —
   `lti-service/app/scenario_client.py` already calls a contract that
   doesn't exist on `backend` (flagged in FDE-011's implementation log).
   There's no real "a new cohort just showed up via LTI" event to hang a
   trigger off of until that exists.
2. Even once it does, the natural trigger is an *instructor* linking an
   LMS course to a cohort (creating that mapping) — not every raw launch
   attempt. Auto-provisioning a cluster namespace off of an unauthenticated
   student's launch hitting a 404 would be a resource-exhaustion vector,
   not just an incomplete feature.

Follow-up: once `/internal/lti-mappings` gains a real create path, call
the provisioner from there the same way `backend/app/routers/cohorts.py`
does.

## Scope: what isn't in the chart

`chart/` covers every service `infra/docker-compose.yml` already defines
(FDE-012 AC1's literal scope) plus Postgres/Redis/MinIO. Deliberately not
included, and why:

- `lti-service/` — has a Dockerfile but was never added to
  `infra/docker-compose.yml`; it's also conceptually a shared/platform-level
  service (maps an LMS course to *some* cohort's scenario instance), not a
  per-cohort one, so it doesn't belong inside this per-cohort chart even
  once it does get containerized manifests.
- `mocks/legacy-api/` — has a FastAPI app but no Dockerfile and no
  `docker-compose.yml` entry (same gap noted in `architecture.md`'s open
  questions).
- `mocks/compliance-engine/` — stdlib rule engine, no HTTP surface, not
  containerized at all (`architecture.md` → Enterprise system mocks).

## Verification and its limits

No live Kubernetes cluster was reachable in this session (`kubectl` is on
PATH but has no configured/reachable cluster context; `helm` isn't
installed at all) — same environment constraint FDE-010's merge review hit
with `docker pull`. Everything above was reviewed by hand: template
rendering logic, resource ordering (Namespace's built-in Helm kind-priority
vs. the post-install-hook Jobs' `pg_isready`/`mc` wait-loops), env var names
matched 1:1 against `infra/docker-compose.yml` and each service's
`app/config.py`, and the chart's namespace/label/selector consistency. Not
verified: an actual `helm install`, whether the `pg_isready`-wait
initContainers fully close the bootstrap race against `backend`/
`celery-worker` starting before their migrate Jobs finish (see next
paragraph), and the two-cohorts-concurrently DoD item. Whoever has a real
cluster available should run this before trusting those.

**Known bootstrap-race caveat**: `backend`, `celery-worker`, and
`persona-service` are normal (non-hook) chart resources, so Kubernetes
creates their pods around the same time as the `backend-migrate`/
`persona-migrate` post-install hook Jobs, not strictly after. Each of
those Deployments' pods wait for Postgres to accept connections
(`pg_isready` initContainer) but not for the migration itself to finish,
so on a cohort's very first install there's a short window where a
request could reach `backend` before its schema exists. This is a common,
generally-accepted limitation of "migrations as a separate Job" in
Kubernetes (most setups either accept it, given how fast a `helm --wait`
install typically settles, or gate app pods on a migration-complete
marker via extra RBAC to read Job status) — left as a documented
follow-up rather than added RBAC surface for this story.
