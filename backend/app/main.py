from fastapi import FastAPI

from app.routers import (
    cohorts,
    engagements,
    legacy_system,
    scenario_generator,
    scenario_instances,
    submissions,
    technical_task,
)

app = FastAPI(title="FDE Lab — Scenario Engine")

app.include_router(scenario_instances.router)
app.include_router(engagements.router)
app.include_router(submissions.router)
app.include_router(cohorts.router)
app.include_router(legacy_system.router)
app.include_router(scenario_generator.router)
app.include_router(technical_task.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
