import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationState

STATE_IDLE = "idle"
STATE_WAITING_WRITING_TASK_TYPE = "waiting_for_writing_task_type"
STATE_WAITING_WRITING_TEXT = "waiting_for_writing_text"
STATE_WAITING_SENTENCE_TO_UPGRADE = "waiting_for_sentence_to_upgrade"
STATE_WAITING_SENTENCE_TO_EXPLAIN = "waiting_for_sentence_to_explain"
STATE_WAITING_VOCAB_TOPIC = "waiting_for_vocab_topic"
STATE_WAITING_DAYS_LEFT = "waiting_for_days_left"


async def get_conversation_state(session: AsyncSession, user_id: int) -> ConversationState:
    stmt = select(ConversationState).where(ConversationState.user_id == user_id)
    state = (await session.execute(stmt)).scalars().first()
    if state:
        return state

    state = ConversationState(user_id=user_id, current_state=STATE_IDLE, context_json="{}")
    session.add(state)
    await session.flush()
    return state


def get_context(state: ConversationState) -> dict[str, Any]:
    try:
        value = json.loads(state.context_json or "{}")
    except json.JSONDecodeError:
        value = {}
    return value if isinstance(value, dict) else {}


async def set_conversation_state(
    session: AsyncSession,
    user_id: int,
    current_state: str,
    pending_intent: str | None = None,
    context: dict[str, Any] | None = None,
) -> ConversationState:
    state = await get_conversation_state(session, user_id)
    state.current_state = current_state
    state.pending_intent = pending_intent
    state.context_json = json.dumps(context or {}, ensure_ascii=False)
    await session.flush()
    return state


async def clear_conversation_state(session: AsyncSession, user_id: int) -> None:
    state = await get_conversation_state(session, user_id)
    state.current_state = STATE_IDLE
    state.pending_intent = None
    state.context_json = "{}"
    await session.flush()

