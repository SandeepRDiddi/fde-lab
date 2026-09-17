import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.gateway import get_gateway_client
from app.main import app
from app.scenario_ref import scenario_instances_table
from app.scenario_ref import _metadata as scenario_metadata


class FakeGatewayClient:
    """Stands in for PromptOps Gateway in tests — no network calls, no live model."""

    def __init__(self):
        self.calls: list[dict] = []

    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        return f"[persona reply #{len(self.calls)}]"


@pytest.fixture()
def fake_gateway():
    return FakeGatewayClient()


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    scenario_metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        scenario_metadata.drop_all(bind=engine)


@pytest.fixture()
def client(engine, fake_gateway):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_gateway_client] = lambda: fake_gateway
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def seed_scenario_instance(engine):
    def _seed(scenario_instance_id: uuid.UUID, config: dict):
        with engine.begin() as conn:
            conn.execute(
                scenario_instances_table.insert().values(id=scenario_instance_id, config=config)
            )

    return _seed
