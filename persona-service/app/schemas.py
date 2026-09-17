from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import MessageRole


class SendMessageRequest(BaseModel):
    student_id: uuid.UUID
    message: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationRead(BaseModel):
    scenario_instance_id: uuid.UUID
    student_id: uuid.UUID
    messages: list[MessageRead]


class PivotRequest(BaseModel):
    agenda: str
