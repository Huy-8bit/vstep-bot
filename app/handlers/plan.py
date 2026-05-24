from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.utils import send_long_message
from app.services.plan_service import create_plan_text, save_study_plan
from app.services.user_service import get_or_create_user

router = Router(name="plan")


async def _send_plan(
    message: Message,
    session: AsyncSession,
    telegram_user: TelegramUser | None = None,
) -> None:
    current_user = telegram_user or message.from_user
    if not current_user:
        return
    user = await get_or_create_user(session, current_user)
    if not user.target_level or not user.days_left or not user.daily_minutes:
        await message.answer("Bạn cần hoàn tất /start trước để mình biết mục tiêu và thời gian ôn.")
        return

    plan_text = create_plan_text(user)
    await save_study_plan(session, user_id=user.id, plan_text=plan_text, days=user.days_left)
    await send_long_message(message, plan_text)


@router.message(Command("plan"))
async def plan_command(message: Message, session: AsyncSession) -> None:
    await _send_plan(message, session)


@router.callback_query(F.data.in_({"menu:plan", "study_plan"}))
async def plan_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để tạo study plan.", show_alert=True)
        return
    await callback.answer()
    await _send_plan(callback.message, session, telegram_user=callback.from_user)
