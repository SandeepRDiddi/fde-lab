from fastapi import FastAPI

from app.routers import cohorts, scenario_instances, submissions

app = FastAPI(title="FDE Lab — Scenario Engine")

app.include_router(scenario_instances.router)
app.include_router(submissions.router)
app.include_router(cohorts.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
