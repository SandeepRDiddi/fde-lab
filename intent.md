# FDE Lab — Intent

## What this is

FDE Lab is a training platform that gives experienced AI/Data professionals an
**enterprise-flavoured, hands-on simulation** of what it actually feels like to work
as a Forward Deployed Engineer (FDE) — before they're doing it for real, with a real
client.

The core idea: technical skill isn't the gap for this audience. The gap is everything
that surrounds the technical work on a real engagement — ambiguity, mess, constraints,
and having to defend your work to a skeptical audience under time pressure. FDE Lab is
built to make students *feel* that, repeatedly, in a controlled environment.

## Audience

Working professionals already skilled in AI/Data, upskilling into an FDE role.
No need to teach fundamentals — the lab assumes technical competence and trains the
*engagement* skills layered on top of it.

## The experience students go through

Each scenario is designed to reproduce, in compressed form, the frictions of a real
client engagement:

- **Ambiguous asks** — a non-technical stakeholder gives a vague, underspecified
  request that the student has to translate into a working spec themselves.
- **Messy, realistic data** — synthetic data generated fresh for each training run,
  deliberately dirty (nulls, duplicates, schema drift, PII needing masking) rather
  than clean demo data.
- **Working inside someone else's constraints** — mock legacy systems, a compliance
  checklist to satisfy, an approval workflow to navigate before shipping.
- **Demo or defend, not just ship** — students present their work to a skeptical
  "client" and have to hold up under questioning.
- **Shifting ground mid-engagement** — priorities, requirements, or constraints can
  change partway through, the way a real client's mind changes.

Students work **solo** through individual scenarios. The **capstone is a team
project**, mirroring how real engagements escalate from individual contribution to
collaborative delivery.

## How it's delivered: a scenario engine, not fixed content

FDE Lab is architected as a **flexible scenario engine** — a platform with a library
of reusable "injects" that can be assembled into whatever scenario a given training
cohort needs, rather than one fixed course.

Inject types:

1. **Document/artifact injects** — client emails, Slack-style messages, garbled
   requirement docs, support tickets.
2. **Data-level injects** — synthetic messy datasets, generated fresh per training run
   (not reused/static), simulating a real client's data quality problems.
3. **System-level injects** — mock legacy APIs, compliance checklists, fake approval
   workflows that gate what students can ship.
4. **Live persona injects** — an **AI-driven persona** (not a human role-player) plays
   the stakeholder and the skeptical demo audience, with a defined personality and
   agenda per scenario.

Injects are **calibrated per training cohort**, not randomized or auto-triggered —
each run of the platform generates its own data and scenario conditions for that
specific cohort.

## Pacing

The platform is **scheduled and time-boxed** to the cohort's training calendar, not
self-paced. Scenarios unlock and close on a timeline set by the training program, and
the cohort moves through them together.

## Scope of v1

**No smaller starting slice.** V1 is a full **end-to-end, client-ready demo system**:
one complete scenario flow, working start to finish — ambiguous ask, messy generated
data, a system-level constraint, an AI persona for both the stakeholder interaction
and the demo/defend moment, time-boxed — polished enough to demo to stakeholders as
the platform's proof of concept, not just a prototype of one piece.

## Technical implementation

See `architecture.md` for the full technical design — platform architecture, tech
stack, deployment plan, and repo layout. `architecture.md` must stay aligned with
this document: it exists to serve this intent, and any change to scope or experience
here should be reflected there.

## Open questions (to resolve next)

- What "client-ready demo" needs to include to be presentable (UI polish? one scenario
  or a menu of scenarios? live cohort or single-user walkthrough?)
- Auth model, persona-authoring workflow, and data-generator parameterization — see
  `architecture.md`'s own open questions
