from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.utils import send_long_message
from app.services.user_service import get_or_create_user
from app.services.vocab_service import TOPICS, format_vocab_messages, get_random_items, get_topic_items

router = Router(name="vocab")


def topics_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="📘 10 từ hôm nay", callback_data="vocab_daily")]]
    for index in range(0, len(TOPICS), 2):
        rows.append(
            [
                InlineKeyboardButton(text=topic, callback_data=f"vocab:{topic}")
                for topic in TOPICS[index : index + 2]
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("vocab"))
async def vocab_command(message: Message) -> None:
    await message.answer("Chọn topic vocabulary:", reply_markup=topics_keyboard())


@router.callback_query(F.data == "menu:vocab")
async def vocab_menu(callback: CallbackQuery) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để dùng tính năng này.", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer("Chọn topic vocabulary:", reply_markup=topics_keyboard())


@router.callback_query(F.data == "vocab_daily")
async def send_daily_vocab(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để dùng tính năng này.", show_alert=True)
        return

    items = await get_random_items(session, limit=10)
    await callback.answer()
    for text in format_vocab_messages(items, title="📘 10 từ/cụm từ VSTEP hôm nay", chunk_size=5):
        await send_long_message(callback.message, text, parse_mode="HTML")


@router.callback_query(F.data.startswith("vocab:"))
async def send_vocab_topic(callback: CallbackQuery, session: AsyncSession) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot để dùng tính năng này.", show_alert=True)
        return
    topic = callback.data.split(":", 1)[1]
    if topic not in TOPICS:
        await callback.answer("Topic không hợp lệ.")
        return

    target_level = None
    if callback.from_user:
        user = await get_or_create_user(session, callback.from_user)
        target_level = user.target_level

    items = await get_topic_items(session, topic=topic, level=target_level, limit=10)
    if len(items) < 10:
        items = await get_topic_items(session, topic=topic, limit=10)

    await callback.answer()
    for text in format_vocab_messages(items, title=f"📘 Topic: {topic}", chunk_size=5):
        await send_long_message(callback.message, text, parse_mode="HTML")
