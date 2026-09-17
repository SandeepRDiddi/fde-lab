import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import tasks
from app.celery_app import celery_app
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Scheduled jobs use their own DB session (not the FastAPI get_db dependency),
    # so point them at the same in-memory test DB, and run them synchronously
    # ("eager") so tests can verify job effects without a live Redis broker/worker.
    monkeypatch.setattr(tasks, "SessionLocal", TestingSessionLocal)
    prev_always_eager = celery_app.conf.task_always_eager
    prev_eager_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        celery_app.conf.task_always_eager = prev_always_eager
        celery_app.conf.task_eager_propagates = prev_eager_propagates
