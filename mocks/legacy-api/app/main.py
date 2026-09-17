from fastapi import FastAPI

from app.scenario_loader import build_router, load_scenarios

app = FastAPI(title="FDE Lab — Legacy API Mock")

for scenario in load_scenarios():
    app.include_router(build_router(scenario))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
