from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
import logging
import random
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import session_scope
from app.models.user import User
from app.services.mistake_service import get_recent_mistakes
from app.services.quiz_service import build_quiz_question
from app.services.vocab_service import TOPICS, format_vocab_item_html, format_vocab_messages, get_random_items, get_topic_items

logger = logging.getLogger(__name__)

MAX_MESSAGES_PER_DAY = 3
MIN_IDLE_BEFORE_PROACTIVE = timedelta(minutes=30)
PERIODIC_VOCAB_INTERVAL_MINUTES = {
    "low": 120,
    "normal": 60,
    "high": 30,
}


@dataclass
class ProactivePayload:
    text: str
    reply_markup: InlineKeyboardMarkup | None = None
    parse_mode: str | None = "HTML"


def quick_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📘 Vocab", callback_data="vocab_daily"),
                InlineKeyboardButton(text="🧠 Quiz", callback_data="quiz_start"),
            ],
            [
                InlineKeyboardButton(text="✍️ Task 1", callback_data="task1_random"),
                InlineKeyboardButton(text="📝 Task 2", callback_data="task2_random"),
            ],
            [
                InlineKeyboardButton(text="🔍 Check", callback_data="check_writing"),
                InlineKeyboardButton(text="🚀 Upgrade", callback_data="upgrade_sentence"),
            ],
            [InlineKeyboardButton(text="❌ Để sau", callback_data="proactive_snooze")],
        ]
    )


def mini_study_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📘 3 từ vựng", callback_data="mini_vocab_3"),
                InlineKeyboardButton(text="🧠 1 quiz", callback_data="quiz_start"),
            ],
            [
                InlineKeyboardButton(text="🚀 1 câu nâng cấp", callback_data="upgrade_sentence"),
                InlineKeyboardButton(text="❌ Để sau", callback_data="proactive_snooze"),
            ],
        ]
    )


def plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Tạo comeback plan", callback_data="study_plan")],
            [InlineKeyboardButton(text="❌ Để sau", callback_data="proactive_snooze")],
        ]
    )


async def send_daily_reminders(bot: Bot) -> None:
    now_utc = utc_now()
    async with session_scope() as session:
        users = await list_proactive_users(session)
        for user in users:
            local_now = to_user_local(now_utc, user)
            local_date = local_now.date().isoformat()
            if user.proactive_daily_reminder_date == local_date:
                continue
            if local_now.strftime("%H:%M") != (user.reminder_time or "20:00"):
                continue
            if not should_send_proactive_message(user, now_utc=now_utc):
                continue
            payload = await build_proactive_message(session, user, "daily_reminder")
            if await _send_payload(bot, user, payload):
                mark_proactive_sent(user, "daily_reminder", now_utc, local_date)


async def send_inactive_user_checkins(bot: Bot) -> None:
    now_utc = utc_now()
    async with session_scope() as session:
        users = await list_proactive_users(session)
        for user in users:
            local_date = to_user_local(now_utc, user).date().isoformat()
            if user.proactive_checkin_date == local_date:
                continue
            inactive_hours = get_inactive_hours(user, now_utc)
            if inactive_hours < 24:
                continue

            if inactive_hours >= 72:
                message_type = "checkin_72"
            elif inactive_hours >= 48:
                message_type = "checkin_48"
            else:
                if user.proactive_frequency == "low":
                    continue
                message_type = "checkin_24"

            if not should_send_proactive_message(user, now_utc=now_utc):
                continue
            payload = await build_proactive_message(session, user, message_type)
            if await _send_payload(bot, user, payload):
                mark_proactive_sent(user, message_type, now_utc, local_date)


async def send_morning_vocab(bot: Bot) -> None:
    now_utc = utc_now()
    async with session_scope() as session:
        users = await list_proactive_users(session)
        for user in users:
            if user.proactive_frequency not in {"normal", "high"}:
                continue
            local_date = to_user_local(now_utc, user).date().isoformat()
            if user.proactive_morning_date == local_date:
                continue
            if not should_send_proactive_message(user, now_utc=now_utc):
                continue
            payload = await build_proactive_message(session, user, "morning_vocab")
            if await _send_payload(bot, user, payload):
                mark_proactive_sent(user, "morning_vocab", now_utc, local_date)


async def send_night_review(bot: Bot) -> None:
    now_utc = utc_now()
    async with session_scope() as session:
        users = await list_proactive_users(session)
        for user in users:
            if user.proactive_frequency == "low":
                continue
            local_date = to_user_local(now_utc, user).date().isoformat()
            if user.proactive_night_date == local_date:
                continue
            if not should_send_proactive_message(user, now_utc=now_utc):
                continue
            payload = await build_proactive_message(session, user, "night_review")
            if await _send_payload(bot, user, payload):
                mark_proactive_sent(user, "night_review", now_utc, local_date)


async def send_periodic_vocab(bot: Bot) -> None:
    now_utc = utc_now()
    async with session_scope() as session:
        users = await list_proactive_users(session)
        for user in users:
            if not should_send_periodic_vocab(user, now_utc=now_utc):
                continue
            local_date = to_user_local(now_utc, user).date().isoformat()
            payload = await build_proactive_message(session, user, "periodic_vocab")
            if await _send_payload(bot, user, payload):
                mark_proactive_sent(user, "periodic_vocab", now_utc, local_date)


async def list_proactive_users(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.proactive_enabled.is_(True))
    return list((await session.execute(stmt)).scalars().all())


def should_send_proactive_message(user: User, now_utc: datetime | None = None) -> bool:
    now = now_utc or utc_now()
    if not user.proactive_enabled:
        return False

    quiet_until = ensure_utc(user.proactive_quiet_until)
    if quiet_until and quiet_until > now:
        return False

    last_interaction = ensure_utc(user.last_interaction_at)
    if last_interaction and now - last_interaction < MIN_IDLE_BEFORE_PROACTIVE:
        return False

    daily_count = current_daily_count(user, now)
    max_daily = 1 if user.proactive_frequency == "low" else MAX_MESSAGES_PER_DAY
    if daily_count >= max_daily:
        return False

    last_sent = ensure_utc(user.last_proactive_sent_at)
    if last_sent:
        min_gap = proactive_gap(user)
        if now - last_sent < min_gap:
            return False

    return True


def should_send_periodic_vocab(user: User, now_utc: datetime | None = None) -> bool:
    now = now_utc or utc_now()
    if not user.proactive_enabled:
        return False

    quiet_until = ensure_utc(user.proactive_quiet_until)
    if quiet_until and quiet_until > now:
        return False

    last_interaction = ensure_utc(user.last_interaction_at)
    if last_interaction and now - last_interaction < MIN_IDLE_BEFORE_PROACTIVE:
        return False

    if current_daily_count(user, now) >= MAX_MESSAGES_PER_DAY:
        return False

    interval = timedelta(
        minutes=PERIODIC_VOCAB_INTERVAL_MINUTES.get(user.proactive_frequency or "normal", 60)
    )
    last_sent = ensure_utc(user.last_proactive_sent_at)
    if last_sent and now - last_sent < interval:
        return False

    return True


async def build_proactive_message(
    session: AsyncSession,
    user: User,
    message_type: str,
) -> ProactivePayload:
    if message_type == "daily_reminder":
        return ProactivePayload(
            text=(
                "📘 <b>Tới giờ ôn VSTEP rồi.</b>\n"
                "Hôm nay làm nhẹ 1 quiz từ vựng hay viết 1 đoạn Task 2?"
            ),
            reply_markup=quick_action_keyboard(),
        )

    if message_type == "checkin_24":
        return ProactivePayload(
            text=(
                "Ê, hôm nay mình làm 1 câu nhỏ thôi nhé.\n\n"
                "Dịch câu này sang tiếng Anh:\n"
                "<i>Du lịch giúp con người mở rộng tầm nhìn.</i>"
            ),
            reply_markup=mini_study_keyboard(),
        )

    if message_type == "checkin_48":
        return ProactivePayload(
            text=(
                "Bạn mất tích 2 ngày rồi đó 😤\n"
                "VSTEP không tự thương mình đâu. Làm 5 phút thôi: chọn Quiz hoặc Vocabulary?"
            ),
            reply_markup=mini_study_keyboard(),
        )

    if message_type == "checkin_72":
        return ProactivePayload(
            text=(
                "Ok, mình reset nhẹ lại nhé.\n"
                "Tôi có thể tạo cho bạn plan ôn lại trong 2 ngày. Bấm nút bên dưới."
            ),
            reply_markup=plan_keyboard(),
        )

    if message_type == "morning_vocab":
        items = await get_random_items(session, limit=1)
        if not items:
            return ProactivePayload(
                text="🌤️ <b>Morning VSTEP bite:</b> hôm nay ôn 1 cụm nhỏ nhé.",
                reply_markup=mini_study_keyboard(),
            )
        item = items[0]
        text = (
            "🌤️ <b>Morning VSTEP bite</b>\n\n"
            f"{format_vocab_item_html(item, 1)}\n\n"
            "Câu hỏi nhỏ: bạn có thể viết 1 câu mới với cụm này không?"
        )
        return ProactivePayload(text=text, reply_markup=mini_study_keyboard())

    if message_type == "night_review":
        mistakes = await get_recent_mistakes(session, user_id=user.id, limit=1)
        if mistakes:
            mistake = mistakes[0]
            return ProactivePayload(
                text=(
                    "🌙 <b>Review nhanh trước khi ngủ</b>\n\n"
                    f"Bạn từng sai cấu trúc này:\n"
                    f"Wrong: <i>{_html(mistake.original_text)}</i>\n"
                    f"Correct: <i>{_html(mistake.corrected_text)}</i>\n\n"
                    "Thử sửa câu này: <i>She want to improve her English.</i>"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="❌ Xem mistake book", callback_data="mistakes_recent")],
                        [InlineKeyboardButton(text="🔁 Tạo bài review", callback_data="mistakes_review")],
                        [InlineKeyboardButton(text="❌ Để sau", callback_data="proactive_snooze")],
                    ]
                ),
            )
        return ProactivePayload(
            text="🌙 Review nhanh trước khi ngủ: hôm nay bạn có muốn ôn lại lỗi sai gần đây không?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Mistake Book", callback_data="mistakes_recent")],
                    [InlineKeyboardButton(text="❌ Để sau", callback_data="proactive_snooze")],
                ]
            ),
        )

    if message_type == "periodic_vocab":
        topic = random.choice(TOPICS)
        count = {"low": 1, "normal": 2, "high": 3}.get(user.proactive_frequency or "normal", 2)
        items = await get_topic_items(session, topic=topic, limit=count)
        if not items:
            items = await get_random_items(session, limit=count)
            topic = "random"
        vocab_text = "\n\n".join(
            format_vocab_messages(
                items,
                title=f"📘 Vocab bite: {topic}",
                chunk_size=3,
            )
        )
        return ProactivePayload(
            text=(
                "⏱️ <b>VSTEP vocab vài phút</b>\n"
                "Mình gửi nhẹ vài cụm, đọc lướt cũng được.\n\n"
                f"{vocab_text}"
            ),
            reply_markup=mini_study_keyboard(),
        )

    return ProactivePayload(
        text="Mình có vài bài ôn VSTEP ngắn cho bạn. Chọn một cái nhé:",
        reply_markup=quick_action_keyboard(),
    )


def mark_proactive_sent(user: User, message_type: str, now_utc: datetime, local_date: str) -> None:
    if user.proactive_messages_sent_date != local_date:
        user.proactive_messages_sent_date = local_date
        user.proactive_messages_sent_count = 0

    user.proactive_messages_sent_count = (user.proactive_messages_sent_count or 0) + 1
    user.last_proactive_sent_at = now_utc

    if message_type == "daily_reminder":
        user.proactive_daily_reminder_date = local_date
    elif message_type == "morning_vocab":
        user.proactive_morning_date = local_date
    elif message_type == "night_review":
        user.proactive_night_date = local_date
    elif message_type.startswith("checkin_"):
        user.proactive_checkin_date = local_date


def current_daily_count(user: User, now_utc: datetime) -> int:
    local_date = to_user_local(now_utc, user).date().isoformat()
    if user.proactive_messages_sent_date != local_date:
        return 0
    return user.proactive_messages_sent_count or 0


def proactive_gap(user: User) -> timedelta:
    if user.proactive_frequency == "high":
        return timedelta(hours=2)
    if user.proactive_frequency == "low":
        return timedelta(hours=8)
    return timedelta(hours=4)


def get_inactive_hours(user: User, now_utc: datetime) -> float:
    last_interaction = ensure_utc(user.last_interaction_at) or ensure_utc(user.created_at) or now_utc
    return max(0.0, (now_utc - last_interaction).total_seconds() / 3600)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_user_local(now_utc: datetime, user: User) -> datetime:
    timezone_name = user.timezone or settings.bot_timezone
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo(settings.bot_timezone)
    return now_utc.astimezone(tz)


async def quiet_user_for_hours(session: AsyncSession, user: User, hours: int = 4) -> None:
    user.proactive_quiet_until = utc_now() + timedelta(hours=hours)
    await session.flush()


async def quiet_user_until_tomorrow(session: AsyncSession, user: User) -> None:
    now = utc_now()
    local_now = to_user_local(now, user)
    tomorrow = local_now.date() + timedelta(days=1)
    local_midnight = datetime.combine(tomorrow, time.min, tzinfo=local_now.tzinfo)
    user.proactive_quiet_until = local_midnight.astimezone(timezone.utc)
    await session.flush()


async def _send_payload(bot: Bot, user: User, payload: ProactivePayload) -> bool:
    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=payload.text[:4000],
            reply_markup=payload.reply_markup,
            parse_mode=payload.parse_mode,
        )
        return True
    except (TelegramForbiddenError, TelegramBadRequest):
        logger.info("Cannot send proactive message to telegram_id=%s", user.telegram_id)
        return False
    except Exception:
        logger.exception("Unexpected proactive send failure for telegram_id=%s", user.telegram_id)
        return False


def _html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
