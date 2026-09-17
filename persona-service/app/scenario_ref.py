"""Read/write access to the `scenario_instances` table owned by the backend service.

The persona service does not duplicate scenario-engine logic or call the backend
over HTTP for this — it shares the same Postgres instance (architecture.md's
"shared data layer") and only needs the `config` JSON column, which carries the
per-scenario persona definition: `config["persona"] = {"system_prompt", "agenda"}`.
This table object is deliberately not part of `app.database.Base` — the backend's
own Alembic migration (FDE-001) owns creating/altering `scenario_instances`.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Column, JSON, MetaData, Table, Uuid
from sqlalchemy.orm import Session

_metadata = MetaData()

scenario_instances_table = Table(
    "scenario_instances",
    _metadata,
    Column("id", Uuid, primary_key=True),
    Column("config", JSON, nullable=False),
)


def get_scenario_config(db: Session, scenario_instance_id: uuid.UUID) -> dict | None:
    row = db.execute(
        scenario_instances_table.select().where(scenario_instances_table.c.id == scenario_instance_id)
    ).first()
    return None if row is None else row.config


def set_scenario_config(db: Session, scenario_instance_id: uuid.UUID, config: dict) -> None:
    db.execute(
        scenario_instances_table.update()
        .where(scenario_instances_table.c.id == scenario_instance_id)
        .values(config=config)
    )
