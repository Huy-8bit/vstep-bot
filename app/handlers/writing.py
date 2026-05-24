from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.utils import send_long_message
from app.services.mistake_service import save_mistakes_from_metadata
from app.services.openai_service import OpenAIServiceError, openai_service
from app.services.user_service import get_or_create_user
from app.services.writing_service import (
    extract_feedback_metadata,
    format_task,
    random_task1,
    random_task2,
    save_writing_submission,
)

router = Router(name="writing")


class CheckState(StatesGroup):
    choosing_task_type = State()
    waiting_essay = State()


def check_task_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Task 1", callback_data="check_task:Task 1"),
                InlineKeyboardButton(text="Task 2", callback_data="check_task:Task 2"),
            ]
        ]
    )


async def _send_task1(message: Message, state: FSMContext) -> None:
    task = random_task1()
    await state.update_data(last_task_type=task.task_type, last_prompt=task.prompt)
    await message.answer(format_task(task))


async def _send_task2(message: Message, state: FSMContext) -> None:
    task = random_task2()
    await state.update_data(last_task_type=task.task_type, last_prompt=task.prompt)
    await message.answer(format_task(task))


@router.message(Command("task1"))
async def task1_command(message: Message, state: FSMContext) -> None:
    await _send_task1(message, state)


@router.callback_query(F.data.in_({"menu:task1", "task1_random"}))
async def task1_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để nhận đề Task 1.", show_alert=True)
        return
    await callback.answer()
    await _send_task1(callback.message, state)


@router.message(Command("task2"))
async def task2_command(message: Message, state: FSMContext) -> None:
    await _send_task2(message, state)


@router.callback_query(F.data.in_({"menu:task2", "task2_random"}))
async def task2_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để nhận đề Task 2.", show_alert=True)
        return
    await callback.answer()
    await _send_task2(callback.message, state)


@router.message(Command("check"))
async def check_command(message: Message, state: FSMContext) -> None:
    await state.set_state(CheckState.choosing_task_type)
    await message.answer("Bạn muốn chấm bài Task 1 hay Task 2?", reply_markup=check_task_keyboard())


@router.callback_query(F.data.in_({"menu:check", "check_writing"}))
async def check_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot và dùng /check để chấm bài.", show_alert=True)
        return
    await callback.answer()
    await state.set_state(CheckState.choosing_task_type)
    await callback.message.answer("Bạn muốn chấm bài Task 1 hay Task 2?", reply_markup=check_task_keyboard())


@router.callback_query(CheckState.choosing_task_type, F.data.startswith("check_task:"))
async def choose_check_task(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        return
    task_type = callback.data.split(":", 1)[1]
    data = await state.get_data()
    prompt = data.get("last_prompt") if data.get("last_task_type") == task_type else None
    await state.update_data(
        check_task_type=task_type,
        check_prompt=prompt or "Submitted via /check without a specific prompt.",
    )
    await state.set_state(CheckState.waiting_essay)
    await callback.answer()
    await callback.message.answer(
        f"Gửi bài viết {task_type} của bạn trong một tin nhắn. "
        "Mình sẽ chấm theo tiêu chí VSTEP và lưu lỗi sai cá nhân."
    )


@router.message(CheckState.waiting_essay)
async def receive_writing(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not message.from_user:
        return
    essay = (message.text or "").strip()
    if essay.startswith("/"):
        await state.clear()
        await message.answer("Mình đã hủy flow chấm bài. Gõ lại command bạn muốn dùng nhé.")
        return
    if len(essay.split()) < 40:
        await message.answer("Bài hơi ngắn. Bạn gửi bài đầy đủ hơn để mình chấm chính xác nhé.")
        return

    data = await state.get_data()
    task_type = data.get("check_task_type", "Task 2")
    prompt = data.get("check_prompt", "Submitted via /check without a specific prompt.")
    user = await get_or_create_user(session, message.from_user)

    await message.answer("Mình đang chấm bài. Quá trình này có thể mất khoảng 20-60 giây.")
    try:
        raw_feedback = await openai_service.check_writing(task_type=task_type, prompt=prompt, essay=essay)
    except OpenAIServiceError as exc:
        await message.answer(f"Không chấm được bài lúc này: {exc}")
        return

    feedback, metadata = extract_feedback_metadata(raw_feedback)
    await save_writing_submission(
        session=session,
        user_id=user.id,
        task_type=task_type,
        prompt=prompt,
        original_text=essay,
        feedback=feedback,
        metadata=metadata,
    )
    await save_mistakes_from_metadata(session=session, user_id=user.id, metadata=metadata)
    await state.clear()
    await send_long_message(message, feedback)
