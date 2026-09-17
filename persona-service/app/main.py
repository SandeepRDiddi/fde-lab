from fastapi import FastAPI

from app.routers import conversations

app = FastAPI(title="FDE Lab — AI Persona Service")

app.include_router(conversations.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
