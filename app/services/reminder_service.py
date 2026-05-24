from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import session_scope
from app.models.user import User
from app.services.quiz_service import build_quiz_question
from app.services.user_service import get_user_by_telegram_id, list_users_with_reminders
from app.services.vocab_service import format_vocab_items, get_random_items
from app.services.writing_service import random_task1, random_task2


def reminder_job_id(telegram_id: int) -> str:
    return f"daily-reminder:{telegram_id}"


def parse_reminder_time(value: str) -> tuple[int, int]:
    hour_text, minute_text = value.split(":", 1)
    hour = int(hour_text)
    minute = int(minute_text)
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("Invalid reminder time.")
    return hour, minute


async def send_daily_reminder(bot: Bot, telegram_id: int) -> None:
    async with session_scope() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if not user or not user.reminder_enabled:
            return

        vocab_items = await get_random_items(session, limit=5)
        quiz = await build_quiz_question(session)
        task = random_task1() if telegram_id % 2 == 0 else random_task2()

        text = "\n\n".join(
            [
                "Nhắc học VSTEP hôm nay:",
                format_vocab_items(vocab_items).replace("10 từ/cụm từ VSTEP hôm nay:", "5 từ/cụm từ nhanh:"),
                f"Quick quiz:\n{quiz.prompt}\n\nĐáp án tự kiểm tra: {quiz.correct_answer}",
                f"Mini writing task:\n{task.prompt}",
            ]
        )
        await bot.send_message(chat_id=telegram_id, text=text[:4000])


def schedule_user_reminder(scheduler: AsyncIOScheduler, bot: Bot, user: User) -> None:
    hour, minute = parse_reminder_time(user.reminder_time)
    scheduler.add_job(
        send_daily_reminder,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=ZoneInfo(settings.bot_timezone)),
        id=reminder_job_id(user.telegram_id),
        replace_existing=True,
        kwargs={"bot": bot, "telegram_id": user.telegram_id},
    )


def unschedule_user_reminder(scheduler: AsyncIOScheduler, telegram_id: int) -> None:
    job_id = reminder_job_id(telegram_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


async def restore_reminders(scheduler: AsyncIOScheduler, bot: Bot) -> int:
    async with session_scope() as session:
        users = await list_users_with_reminders(session)
        for user in users:
            schedule_user_reminder(scheduler, bot, user)
        return len(users)

