from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.utils import send_long_message
from app.services.mistake_service import (
    build_local_review_exercises,
    build_mistakes_text,
    format_recent_mistakes,
    get_recent_mistakes,
)
from app.services.openai_service import OpenAIServiceError, openai_service
from app.services.user_service import get_or_create_user

router = Router(name="mistakes")


async def _show_mistakes(
    message: Message,
    session: AsyncSession,
    telegram_user: TelegramUser | None = None,
) -> None:
    current_user = telegram_user or message.from_user
    if not current_user:
        return
    user = await get_or_create_user(session, current_user)
    mistakes = await get_recent_mistakes(session, user_id=user.id, limit=10)
    await send_long_message(message, format_recent_mistakes(mistakes))


async def _review_mistakes(
    message: Message,
    session: AsyncSession,
    telegram_user: TelegramUser | None = None,
) -> None:
    current_user = telegram_user or message.from_user
    if not current_user:
        return
    user = await get_or_create_user(session, current_user)
    mistakes = await get_recent_mistakes(session, user_id=user.id, limit=10)
    if not mistakes:
        await message.answer("Bạn chưa có lỗi sai nào. Hãy dùng /check để tạo mistake book trước.")
        return

    mistakes_text = build_mistakes_text(mistakes)
    await message.answer("Mình đang tạo bài review từ lỗi sai của bạn...")
    try:
        result = await openai_service.generate_mistake_review(mistakes_text)
    except OpenAIServiceError:
        result = build_local_review_exercises(mistakes)
    await send_long_message(message, result)


@router.message(Command("mistakes"))
async def mistakes_command(message: Message, session: AsyncSession) -> None:
    await _show_mistakes(message, session)


@router.callback_query(F.data.in_({"menu:mistakes", "mistakes_recent"}))
async def mistakes_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để xem mistake book.", show_alert=True)
        return
    await callback.answer()
    await _show_mistakes(callback.message, session, telegram_user=callback.from_user)


@router.callback_query(F.data.in_({"mistakes_review", "mistakes_exercises"}))
async def review_mistakes_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot và dùng /review_mistakes.", show_alert=True)
        return
    await callback.answer()
    await _review_mistakes(callback.message, session, telegram_user=callback.from_user)


@router.message(Command("review_mistakes"))
async def review_mistakes_command(message: Message, session: AsyncSession) -> None:
    await _review_mistakes(message, session)
