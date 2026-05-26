from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.quiz import QuizState
from app.handlers.utils import send_long_message
from app.services.conversation_service import (
    STATE_IDLE,
    STATE_WAITING_DAYS_LEFT,
    STATE_WAITING_SENTENCE_TO_EXPLAIN,
    STATE_WAITING_SENTENCE_TO_UPGRADE,
    STATE_WAITING_VOCAB_TOPIC,
    STATE_WAITING_WRITING_TASK_TYPE,
    STATE_WAITING_WRITING_TEXT,
    clear_conversation_state,
    get_context,
    get_conversation_state,
    set_conversation_state,
)
from app.services.explanation_service import explain_phrase, explain_sentence
from app.services.essay_phrase_service import build_essay_phrase_pack, is_useful_phrase_request
from app.services.intent_service import (
    IntentResult,
    detect_intent,
    extract_days_left,
    extract_task_type,
    extract_topic,
)
from app.services.mistake_service import save_mistakes_from_metadata
from app.services.openai_service import OpenAIServiceError, openai_service
from app.services.plan_service import create_plan_text, save_study_plan
from app.services.proactive_service import mini_study_keyboard
from app.services.quiz_service import build_quiz_question
from app.services.user_service import get_or_create_user
from app.services.vocab_service import TOPICS, format_vocab_messages, get_random_items, get_topic_items
from app.services.writing_service import (
    extract_feedback_metadata,
    format_task,
    random_task1,
    random_task2,
    save_writing_submission,
)

router = Router(name="natural_chat")


def clarification_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Giải thích câu", callback_data="natural_explain_sentence"),
                InlineKeyboardButton(text="Sửa writing", callback_data="natural_check_writing"),
            ],
            [
                InlineKeyboardButton(text="Nâng cấp câu", callback_data="upgrade_sentence"),
                InlineKeyboardButton(text="Tạo quiz", callback_data="quiz_start"),
            ],
            [InlineKeyboardButton(text="Học từ vựng", callback_data="vocab_daily")],
        ]
    )


@router.callback_query(F.data == "natural_explain_sentence")
async def natural_explain_sentence_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_or_create_user(session, callback.from_user)
    await set_conversation_state(
        session,
        user_id=user.id,
        current_state=STATE_WAITING_SENTENCE_TO_EXPLAIN,
        pending_intent="explain_sentence",
    )
    await callback.answer()
    if callback.message:
        await callback.message.answer("Gửi câu tiếng Anh bạn muốn mình giải thích.")


@router.callback_query(F.data == "natural_check_writing")
async def natural_check_writing_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_or_create_user(session, callback.from_user)
    await set_conversation_state(
        session,
        user_id=user.id,
        current_state=STATE_WAITING_WRITING_TASK_TYPE,
        pending_intent="check_writing",
    )
    await callback.answer()
    if callback.message:
        await callback.message.answer("Ok, đây là Task 1 hay Task 2?")


@router.message(F.text)
async def handle_natural_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not message.from_user or not message.text:
        return
    text = message.text.strip()
    if not text or text.startswith("/"):
        return

    user = await get_or_create_user(session, message.from_user)
    conversation_state = await get_conversation_state(session, user.id)
    if conversation_state.current_state != STATE_IDLE:
        await continue_state_flow(message, state, session, user.id, conversation_state.current_state)
        return

    intent = await detect_intent(text)
    if intent.confidence < 0.55:
        await message.answer(
            intent.followup_question or "Bạn muốn tôi làm gì với nội dung này?",
            reply_markup=clarification_keyboard(),
        )
        return

    await route_intent(message, state, session, user.id, user, intent)


async def continue_state_flow(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user_id: int,
    current_state: str,
) -> None:
    text = (message.text or "").strip()
    conversation_state = await get_conversation_state(session, user_id)
    context = get_context(conversation_state)

    if current_state == STATE_WAITING_WRITING_TASK_TYPE:
        task_type = extract_task_type(text.lower())
        if not task_type:
            await message.answer("Bạn nói rõ giúp mình: Task 1 hay Task 2?")
            return
        context["task_type"] = task_type
        writing_text = context.get("writing_text", "")
        if writing_text:
            await clear_conversation_state(session, user_id)
            await check_writing_text(message, session, user_id, task_type, writing_text)
            return
        await set_conversation_state(
            session,
            user_id=user_id,
            current_state=STATE_WAITING_WRITING_TEXT,
            pending_intent="check_writing",
            context=context,
        )
        await message.answer(f"Rồi, gửi bài {task_type} của bạn vào đây.")
        return

    if current_state == STATE_WAITING_WRITING_TEXT:
        task_type = context.get("task_type", "Task 2")
        if not looks_like_writing(text):
            await message.answer("Bài hơi ngắn. Bạn gửi bài Writing đầy đủ hơn để mình chấm chính xác nhé.")
            return
        await clear_conversation_state(session, user_id)
        await check_writing_text(message, session, user_id, task_type, text)
        return

    if current_state == STATE_WAITING_SENTENCE_TO_UPGRADE:
        await clear_conversation_state(session, user_id)
        await upgrade_sentence_text(message, text)
        return

    if current_state == STATE_WAITING_SENTENCE_TO_EXPLAIN:
        await clear_conversation_state(session, user_id)
        result = await explain_sentence(text)
        await send_long_message(message, result, parse_mode="HTML" if "<" in result else None)
        return

    if current_state == STATE_WAITING_VOCAB_TOPIC:
        topic = extract_topic(text.lower())
        await clear_conversation_state(session, user_id)
        await send_vocab_by_topic_or_random(message, session, topic=topic)
        return

    if current_state == STATE_WAITING_DAYS_LEFT:
        days_left = extract_days_left(text.lower())
        if days_left is None:
            await message.answer("Bạn gửi số ngày còn lại nhé. Ví dụ: còn 2 ngày nữa thi.")
            return
        await clear_conversation_state(session, user_id)
        await create_or_update_study_plan(message, session, user_id, days_left)


async def route_intent(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user_id: int,
    user,
    intent: IntentResult,
) -> None:
    if intent.intent == "vocab_request":
        if is_useful_phrase_request(message.text or ""):
            await send_long_message(message, build_essay_phrase_pack(message.text or ""), parse_mode="HTML")
            return
        await send_vocab_by_topic_or_random(message, session, topic=intent.topic)
        return

    if intent.intent == "quiz_request":
        quiz_type = intent.task_type if intent.task_type in {"meaning_vi", "write_phrase"} else None
        question = await build_quiz_question(session, quiz_type=quiz_type)
        await state.set_state(QuizState.waiting_answer)
        await state.update_data(quiz_question=question.to_dict())
        await message.answer(question.prompt)
        return

    if intent.intent == "task1_request":
        await message.answer(format_task(random_task1()))
        return

    if intent.intent == "task2_request":
        await message.answer(format_task(random_task2()))
        return

    if intent.intent == "check_writing":
        extracted = intent.extracted_text.strip()
        context = {"task_type": intent.task_type} if intent.task_type else {}
        if extracted and looks_like_writing(extracted):
            context["writing_text"] = extracted
        await set_conversation_state(
            session,
            user_id=user_id,
            current_state=STATE_WAITING_WRITING_TASK_TYPE,
            pending_intent="check_writing",
            context=context,
        )
        if intent.task_type and extracted and looks_like_writing(extracted):
            await clear_conversation_state(session, user_id)
            await check_writing_text(message, session, user_id, intent.task_type, extracted)
            return
        if intent.task_type and not extracted:
            await set_conversation_state(
                session,
                user_id=user_id,
                current_state=STATE_WAITING_WRITING_TEXT,
                pending_intent="check_writing",
                context=context,
            )
            await message.answer(f"Rồi, gửi bài {intent.task_type} của bạn vào đây.")
            return
        await message.answer("Ok, đây là Task 1 hay Task 2?")
        return

    if intent.intent == "upgrade_sentence":
        if intent.extracted_text:
            await upgrade_sentence_text(message, intent.extracted_text)
        else:
            await set_conversation_state(
                session,
                user_id=user_id,
                current_state=STATE_WAITING_SENTENCE_TO_UPGRADE,
                pending_intent="upgrade_sentence",
            )
            await message.answer("Gửi câu bạn muốn nâng cấp lên B2.")
        return

    if intent.intent == "explain_sentence":
        if intent.extracted_text:
            result = await explain_sentence(intent.extracted_text)
            await send_long_message(message, result, parse_mode="HTML" if "<" in result else None)
        else:
            await set_conversation_state(
                session,
                user_id=user_id,
                current_state=STATE_WAITING_SENTENCE_TO_EXPLAIN,
                pending_intent="explain_sentence",
            )
            await message.answer("Gửi câu tiếng Anh bạn muốn mình giải thích.")
        return

    if intent.intent == "explain_phrase":
        phrase = intent.extracted_text or message.text or ""
        result = await explain_phrase(session, phrase)
        await send_long_message(message, result, parse_mode="HTML")
        return

    if intent.intent == "study_plan":
        days_left = intent.days_left
        if days_left is None:
            await set_conversation_state(
                session,
                user_id=user_id,
                current_state=STATE_WAITING_DAYS_LEFT,
                pending_intent="study_plan",
            )
            await message.answer("Bạn còn bao nhiêu ngày nữa thi? Ví dụ: còn 2 ngày nữa thi.")
            return
        await create_or_update_study_plan(message, session, user_id, days_left)
        return

    if intent.intent == "mistake_review":
        from app.handlers.mistakes import _show_mistakes

        await _show_mistakes(message, session, telegram_user=message.from_user)
        return

    if intent.intent == "template_request":
        await message.answer(build_template_response(message.text or ""), parse_mode="HTML")
        return

    if intent.intent == "casual_motivation":
        await send_mini_study_options(message)
        return

    await general_vstep_chat(message)


async def send_vocab_by_topic_or_random(
    message: Message,
    session: AsyncSession,
    topic: str = "",
    limit: int = 10,
) -> None:
    if topic and topic in TOPICS:
        items = await get_topic_items(session, topic=topic, limit=limit)
        title = f"📘 Topic: {topic}"
    else:
        items = await get_random_items(session, limit=limit)
        title = "📘 Vocabulary hôm nay"
    for text in format_vocab_messages(items, title=title, chunk_size=5):
        await send_long_message(message, text, parse_mode="HTML")


async def check_writing_text(
    message: Message,
    session: AsyncSession,
    user_id: int,
    task_type: str,
    writing_text: str,
) -> None:
    await message.answer("Mình đang chấm bài. Đợi khoảng 20-60 giây nhé.")
    try:
        raw_feedback = await openai_service.check_writing(
            task_type=task_type,
            prompt="Submitted via natural chat.",
            essay=writing_text,
        )
    except OpenAIServiceError as exc:
        await message.answer(f"Không chấm được bài lúc này: {exc}")
        return

    feedback, metadata = extract_feedback_metadata(raw_feedback)
    await save_writing_submission(
        session=session,
        user_id=user_id,
        task_type=task_type,
        prompt="Submitted via natural chat.",
        original_text=writing_text,
        feedback=feedback,
        metadata=metadata,
    )
    await save_mistakes_from_metadata(session=session, user_id=user_id, metadata=metadata)
    await send_long_message(message, feedback)


async def upgrade_sentence_text(message: Message, sentence: str) -> None:
    await message.answer("Mình đang nâng cấp câu...")
    try:
        result = await openai_service.upgrade_sentence(sentence)
    except OpenAIServiceError as exc:
        await message.answer(f"Không nâng cấp được lúc này: {exc}")
        return
    await send_long_message(message, result)


async def create_or_update_study_plan(
    message: Message,
    session: AsyncSession,
    user_id: int,
    days_left: int,
) -> None:
    user = await get_or_create_user(session, message.from_user)
    user.days_left = days_left
    user.target_level = user.target_level or "B2"
    user.daily_minutes = user.daily_minutes or (90 if days_left <= 2 else 45)
    plan_text = create_plan_text(user)
    await save_study_plan(session, user_id=user_id, plan_text=plan_text, days=days_left)
    await send_long_message(message, plan_text)


async def general_vstep_chat(message: Message) -> None:
    text = message.text or ""
    lower = text.lower()
    if "speaking" in lower:
        await message.answer(
            "Hiện tại mình tập trung mạnh nhất vào Writing và Vocabulary. "
            "Nhưng nếu bạn muốn, mình vẫn có thể tạo câu trả lời mẫu Speaking ngắn để luyện ý."
        )
        return
    try:
        result = await openai_service.natural_chat(text)
    except OpenAIServiceError:
        result = (
            "Mình hiểu. Với VSTEP, mình hỗ trợ tốt nhất các việc này: học từ vựng, quiz, "
            "ra đề Task 1/Task 2, chấm Writing, nâng cấp câu và review lỗi sai."
        )
    await send_long_message(message, result)


async def send_mini_study_options(message: Message) -> None:
    await message.answer(
        "Hiểu. Vậy khỏi học nặng. Làm 1 viên kẹo 3 phút thôi 🍬\nChọn một cái:",
        reply_markup=mini_study_keyboard(),
    )


def looks_like_writing(text: str) -> bool:
    return len(text.split()) >= 40


def build_template_response(text: str) -> str:
    lower = text.lower()
    if "task 1" in lower or "letter" in lower or "email" in lower:
        return "\n".join(
            [
                "<b>✍️ Template Task 1</b>",
                "",
                "Dear Sir or Madam,",
                "I am writing to ...",
                "",
                "Firstly, ...",
                "In addition, ...",
                "",
                "I would appreciate it if you could ...",
                "Thank you for your consideration.",
                "",
                "Yours faithfully,",
            ]
        )
    if "kết bài" in lower or "conclusion" in lower:
        return "\n".join(
            [
                "<b>📝 Kết bài Task 2</b>",
                "",
                "In conclusion, although ... , I believe that ... because ...",
                "",
                "Công thức: <i>In conclusion + nhắc lại 2 phía + nêu rõ opinion.</i>",
            ]
        )
    return "\n".join(
        [
            "<b>📝 Mở bài Task 2</b>",
            "",
            "It is often argued that ... . While this view is understandable, I believe that ... .",
            "",
            "Công thức:",
            "• Paraphrase đề bài",
            "• Nêu opinion rõ ràng",
            "• Không viết quá dài",
            "",
            f"Ví dụ topic của bạn: <i>{escape(text[:120])}</i>",
        ]
    )
