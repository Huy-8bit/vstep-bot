from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quiz_service import build_quiz_question, check_quiz_answer, save_quiz_result
from app.services.user_service import get_or_create_user

router = Router(name="quiz")


class QuizState(StatesGroup):
    waiting_answer = State()


async def _send_quiz(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    quiz_type: str | None = None,
) -> None:
    question = await build_quiz_question(session, quiz_type=quiz_type)
    await state.set_state(QuizState.waiting_answer)
    await state.update_data(quiz_question=question.to_dict())
    await message.answer(question.prompt)


@router.message(Command("quiz"))
async def quiz_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _send_quiz(message, state, session)


@router.message(Command("meaning_quiz"))
async def meaning_quiz_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _send_quiz(message, state, session, quiz_type="meaning_vi")


@router.message(Command("word_quiz"))
async def word_quiz_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _send_quiz(message, state, session, quiz_type="write_phrase")


@router.callback_query(F.data.in_({"menu:quiz", "quiz_start"}))
async def quiz_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để làm quiz có chấm điểm.", show_alert=True)
        return
    await callback.answer()
    await _send_quiz(callback.message, state, session)


@router.callback_query(F.data.in_({"quiz_fill_blank", "quiz_translate", "quiz_meaning", "quiz_write_word"}))
async def quiz_type_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để làm quiz có chấm điểm.", show_alert=True)
        return
    quiz_type_map = {
        "quiz_fill_blank": "fill_blank",
        "quiz_translate": "translate_vi_to_en",
        "quiz_meaning": "meaning_vi",
        "quiz_write_word": "write_phrase",
    }
    quiz_type = quiz_type_map[callback.data]
    await callback.answer()
    await _send_quiz(callback.message, state, session, quiz_type=quiz_type)


@router.message(QuizState.waiting_answer)
async def receive_quiz_answer(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not message.from_user:
        return
    if (message.text or "").startswith("/"):
        await state.clear()
        await message.answer("Mình đã hủy quiz hiện tại. Gõ lại command bạn muốn dùng nhé.")
        return

    data = await state.get_data()
    question = data.get("quiz_question")
    if not question:
        await state.clear()
        await message.answer("Quiz đã hết hạn. Gõ /quiz để làm câu mới.")
        return

    is_correct, explanation = check_quiz_answer(question, message.text or "")
    user = await get_or_create_user(session, message.from_user)
    await save_quiz_result(session, user_id=user.id, vocab_id=question["vocab_id"], is_correct=is_correct)
    await state.clear()
    prefix = "Đúng rồi." if is_correct else "Chưa đúng."
    await message.answer(f"{prefix}\n{explanation}\n\nGõ /quiz để làm câu tiếp theo.")
