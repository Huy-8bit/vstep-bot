from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import get_or_create_user, update_user_profile

router = Router(name="start")


class Onboarding(StatesGroup):
    target_level = State()
    days_left = State()
    daily_minutes = State()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📘 Vocabulary", callback_data="vocab_daily"),
                InlineKeyboardButton(text="🧠 Quiz", callback_data="quiz_start"),
            ],
            [
                InlineKeyboardButton(text="✍️ Task 1", callback_data="task1_random"),
                InlineKeyboardButton(text="📝 Task 2", callback_data="task2_random"),
            ],
            [
                InlineKeyboardButton(text="🔍 Check Writing", callback_data="check_writing"),
                InlineKeyboardButton(text="🚀 Upgrade Sentence", callback_data="upgrade_sentence"),
            ],
            [
                InlineKeyboardButton(text="❌ Mistake Book", callback_data="mistakes_recent"),
                InlineKeyboardButton(text="📅 Study Plan", callback_data="study_plan"),
            ],
        ]
    )


def target_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="B1", callback_data="target:B1"),
                InlineKeyboardButton(text="B2", callback_data="target:B2"),
            ]
        ]
    )


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not message.from_user:
        return
    await get_or_create_user(session, message.from_user)
    await state.clear()
    await state.set_state(Onboarding.target_level)
    await message.answer(
        "Chào bạn! Mình là VSTEP Writing Coach mini.\n"
        "Mình sẽ giúp bạn học vocabulary, làm quiz, luyện Task 1/Task 2 và chấm Writing.\n\n"
        "Trước hết, mục tiêu của bạn là B1 hay B2?",
        reply_markup=target_keyboard(),
    )


@router.message(Command("menu"))
async def menu_command(message: Message) -> None:
    await message.answer("Menu chính:", reply_markup=main_menu_keyboard())


@router.callback_query(Onboarding.target_level, F.data.startswith("target:"))
async def choose_target(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        return
    target_level = callback.data.split(":", 1)[1]
    await state.update_data(target_level=target_level)
    await state.set_state(Onboarding.days_left)
    await callback.answer()
    await callback.message.answer("Bạn còn bao nhiêu ngày nữa thi? Gửi một số, ví dụ: 7")


@router.message(Onboarding.days_left)
async def receive_days_left(message: Message, state: FSMContext) -> None:
    try:
        days_left = int((message.text or "").strip())
        if not 1 <= days_left <= 365:
            raise ValueError
    except ValueError:
        await message.answer("Vui lòng gửi số ngày từ 1 đến 365. Ví dụ: 14")
        return

    await state.update_data(days_left=days_left)
    await state.set_state(Onboarding.daily_minutes)
    await message.answer("Bạn muốn ôn bao nhiêu phút mỗi ngày? Ví dụ: 45")


@router.message(Onboarding.daily_minutes)
async def receive_daily_minutes(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not message.from_user:
        return
    try:
        daily_minutes = int((message.text or "").strip())
        if not 5 <= daily_minutes <= 300:
            raise ValueError
    except ValueError:
        await message.answer("Vui lòng gửi số phút từ 5 đến 300. Ví dụ: 60")
        return

    data = await state.get_data()
    user = await get_or_create_user(session, message.from_user)
    await update_user_profile(
        session=session,
        user=user,
        target_level=data["target_level"],
        days_left=data["days_left"],
        daily_minutes=daily_minutes,
    )
    await state.clear()
    await message.answer(
        "Mình đã lưu mục tiêu của bạn. Chọn tính năng để bắt đầu:",
        reply_markup=main_menu_keyboard(),
    )
