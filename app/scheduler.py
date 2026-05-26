import logging
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.services.proactive_service import (
    send_daily_reminders,
    send_inactive_user_checkins,
    send_morning_vocab,
    send_night_review,
    send_periodic_vocab,
)

logger = logging.getLogger(__name__)


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.bot_timezone))
    scheduler.add_job(
        send_daily_reminders,
        trigger=CronTrigger(minute="*", timezone=ZoneInfo(settings.bot_timezone)),
        id="proactive:daily-reminders",
        replace_existing=True,
        kwargs={"bot": bot},
    )
    scheduler.add_job(
        send_inactive_user_checkins,
        trigger=CronTrigger(hour="*/3", minute=5, timezone=ZoneInfo(settings.bot_timezone)),
        id="proactive:inactive-checkins",
        replace_existing=True,
        kwargs={"bot": bot},
    )
    scheduler.add_job(
        send_morning_vocab,
        trigger=CronTrigger(hour=8, minute=0, timezone=ZoneInfo(settings.bot_timezone)),
        id="proactive:morning-vocab",
        replace_existing=True,
        kwargs={"bot": bot},
    )
    scheduler.add_job(
        send_night_review,
        trigger=CronTrigger(hour=21, minute=30, timezone=ZoneInfo(settings.bot_timezone)),
        id="proactive:night-review",
        replace_existing=True,
        kwargs={"bot": bot},
    )
    scheduler.add_job(
        send_periodic_vocab,
        trigger=CronTrigger(minute=0, timezone=ZoneInfo(settings.bot_timezone)),
        id="proactive:periodic-vocab",
        replace_existing=True,
        kwargs={"bot": bot},
    )
    logger.info("Proactive scheduler configured")
    return scheduler
