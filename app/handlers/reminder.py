from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reminder_service import parse_reminder_time
from app.services.user_service import get_or_create_user

router = Router(name="reminder")


@router.message(Command("reminder_on"))
async def reminder_on(
    message: Message,
    session: AsyncSession,
) -> None:
    if not message.from_user:
        return
    user = await get_or_create_user(session, message.from_user)
    user.reminder_enabled = True
    user.proactive_enabled = True
    user.reminder_time = user.reminder_time or "20:00"
    await session.flush()
    await message.answer(f"Đã bật nhắc học hằng ngày lúc {user.reminder_time}.")


@router.message(Command("reminder_off"))
async def reminder_off(
    message: Message,
    session: AsyncSession,
) -> None:
    if not message.from_user:
        return
    user = await get_or_create_user(session, message.from_user)
    user.reminder_enabled = False
    user.proactive_enabled = False
    await session.flush()
    await message.answer("Đã tắt nhắc học chủ động. Bật lại bằng /proactive_on hoặc /reminder_on.")


@router.message(Command("set_reminder"))
async def set_reminder(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    if not message.from_user:
        return
    reminder_time = (command.args or "").strip()
    try:
        parse_reminder_time(reminder_time)
    except Exception:
        await message.answer("Cú pháp đúng: /set_reminder 20:00")
        return

    user = await get_or_create_user(session, message.from_user)
    user.reminder_enabled = True
    user.proactive_enabled = True
    user.reminder_time = reminder_time
    await session.flush()
    await message.answer(f"Đã đặt nhắc học hằng ngày lúc {reminder_time}.")
