from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.utils import send_long_message
from app.services.proactive_service import (
    mini_study_keyboard,
    quiet_user_for_hours,
    quiet_user_until_tomorrow,
)
from app.services.user_service import get_or_create_user
from app.services.vocab_service import format_vocab_messages, get_random_items

router = Router(name="proactive")


@router.message(Command("proactive_on"))
async def proactive_on(message: Message, session: AsyncSession) -> None:
    if not message.from_user:
        return
    user = await get_or_create_user(session, message.from_user)
    user.proactive_enabled = True
    user.reminder_enabled = True
    user.proactive_quiet_until = None
    await session.flush()
    await message.answer(
        f"Đã bật study coach chủ động. Mình sẽ nhắc nhẹ, tối đa 3 lần/ngày. Giờ chính: {user.reminder_time}."
    )


@router.message(Command("proactive_off"))
async def proactive_off(message: Message, session: AsyncSession) -> None:
    if not message.from_user:
        return
    user = await get_or_create_user(session, message.from_user)
    user.proactive_enabled = False
    user.reminder_enabled = False
    await session.flush()
    await message.answer("Đã tắt proactive messages. Slash commands và inline mode vẫn hoạt động bình thường.")


@router.message(Command("frequency"))
async def set_frequency(message: Message, command: CommandObject, session: AsyncSession) -> None:
    if not message.from_user:
        return
    frequency = (command.args or "").strip().lower()
    if frequency not in {"low", "normal", "high"}:
        await message.answer("Cú pháp đúng: /frequency low | /frequency normal | /frequency high")
        return
    user = await get_or_create_user(session, message.from_user)
    user.proactive_frequency = frequency
    user.proactive_enabled = True
    await session.flush()
    labels = {
        "low": "ít nhắc",
        "normal": "vừa phải",
        "high": "tích cực hơn nhưng vẫn tối đa 3 lần/ngày",
    }
    await message.answer(f"Đã đặt tần suất proactive: {frequency} ({labels[frequency]}).")


@router.message(Command("quiet"))
async def quiet_today(message: Message, session: AsyncSession) -> None:
    if not message.from_user:
        return
    user = await get_or_create_user(session, message.from_user)
    await quiet_user_until_tomorrow(session, user)
    await message.answer("Ok, hôm nay mình im lặng. Ngày mai nhắc tiếp nhẹ nhàng.")


@router.callback_query(F.data == "proactive_snooze")
async def proactive_snooze(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_or_create_user(session, callback.from_user)
    await quiet_user_for_hours(session, user, hours=4)
    await callback.answer("Ok, mình sẽ để bạn yên vài giờ.", show_alert=False)


@router.callback_query(F.data == "mini_vocab_3")
async def mini_vocab_3(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để học mini vocab.", show_alert=True)
        return
    items = await get_random_items(session, limit=3)
    await callback.answer()
    for text in format_vocab_messages(items, title="📘 3 từ vựng nhanh", chunk_size=3):
        await send_long_message(callback.message, text, parse_mode="HTML")


async def send_mini_study_options(message: Message) -> None:
    await message.answer(
        "Hiểu. Vậy khỏi học nặng. Làm 1 viên kẹo 3 phút thôi 🍬\nChọn một cái:",
        reply_markup=mini_study_keyboard(),
    )

