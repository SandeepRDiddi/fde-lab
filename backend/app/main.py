from fastapi import FastAPI

from app.routers import scenario_instances

app = FastAPI(title="FDE Lab — Scenario Engine")

app.include_router(scenario_instances.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
