from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.gateway import PromptOpsGatewayClient, get_gateway_client
from app.models import Conversation, Message, MessageRole
from app.scenario_ref import get_scenario_config, set_scenario_config
from app.schemas import ConversationRead, MessageRead, PivotRequest, SendMessageRequest

router = APIRouter(prefix="/scenario-instances/{scenario_instance_id}", tags=["persona"])


def _require_persona_config(db: Session, scenario_instance_id: uuid.UUID) -> dict:
    config = get_scenario_config(db, scenario_instance_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")
    persona = config.get("persona")
    if not persona or not persona.get("system_prompt"):
        raise HTTPException(status_code=400, detail="Scenario instance has no persona configured")
    return persona


def _find_conversation(db: Session, scenario_instance_id: uuid.UUID, student_id: uuid.UUID) -> Conversation | None:
    return db.execute(
        select(Conversation).where(
            Conversation.scenario_instance_id == scenario_instance_id,
            Conversation.student_id == student_id,
        )
    ).scalar_one_or_none()


def _get_or_create_conversation(db: Session, scenario_instance_id: uuid.UUID, student_id: uuid.UUID) -> Conversation:
    conversation = _find_conversation(db, scenario_instance_id, student_id)
    if conversation is not None:
        return conversation
    conversation = Conversation(scenario_instance_id=scenario_instance_id, student_id=student_id)
    db.add(conversation)
    try:
        db.flush()
    except IntegrityError:
        # Lost a race with a concurrent first message for the same
        # (scenario_instance_id, student_id) — the other request's
        # conversation now exists, so use that one instead of failing.
        db.rollback()
        conversation = _find_conversation(db, scenario_instance_id, student_id)
        if conversation is None:
            raise
    return conversation


def _build_system_prompt(persona: dict) -> str:
    system_prompt = persona["system_prompt"]
    agenda = persona.get("agenda")
    if agenda:
        system_prompt = f"{system_prompt}\n\nCurrent agenda: {agenda}"
    return system_prompt


@router.post("/messages", response_model=MessageRead, status_code=201)
def send_message(
    scenario_instance_id: uuid.UUID,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    gateway: PromptOpsGatewayClient = Depends(get_gateway_client),
) -> MessageRead:
    # Re-read the persona config on every turn (rather than caching it on the
    # conversation) so a mid-engagement pivot is picked up immediately, without
    # restarting the conversation (FDE-004 AC4).
    persona = _require_persona_config(db, scenario_instance_id)
    conversation = _get_or_create_conversation(db, scenario_instance_id, payload.student_id)

    student_message = Message(conversation_id=conversation.id, role=MessageRole.student, content=payload.message)
    db.add(student_message)
    db.flush()

    history = db.execute(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
    ).scalars().all()

    gateway_messages = [
        {"role": "user" if m.role == MessageRole.student else "assistant", "content": m.content} for m in history
    ]
    reply_text = gateway.complete(system_prompt=_build_system_prompt(persona), messages=gateway_messages)

    persona_message = Message(conversation_id=conversation.id, role=MessageRole.persona, content=reply_text)
    db.add(persona_message)
    db.commit()
    db.refresh(persona_message)
    return persona_message


@router.get("/messages", response_model=ConversationRead)
def get_conversation(
    scenario_instance_id: uuid.UUID, student_id: uuid.UUID, db: Session = Depends(get_db)
) -> ConversationRead:
    conversation = _find_conversation(db, scenario_instance_id, student_id)

    messages: list[Message] = []
    if conversation is not None:
        messages = list(
            db.execute(
                select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
            ).scalars()
        )

    return ConversationRead(scenario_instance_id=scenario_instance_id, student_id=student_id, messages=messages)


@router.post("/persona/pivot", status_code=204)
def pivot_persona(scenario_instance_id: uuid.UUID, payload: PivotRequest, db: Session = Depends(get_db)) -> None:
    config = get_scenario_config(db, scenario_instance_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")
    if not isinstance(config.get("persona"), dict):
        config["persona"] = {}
    config["persona"]["agenda"] = payload.agenda
    set_scenario_config(db, scenario_instance_id, config)
    db.commit()
