from datetime import datetime, timezone

from aiogram.types import User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create_user(session: AsyncSession, telegram_user: TelegramUser) -> User:
    stmt = select(User).where(User.telegram_id == telegram_user.id)
    user = (await session.execute(stmt)).scalars().first()
    if user:
        user.username = telegram_user.username
        user.proactive_enabled = True if user.proactive_enabled is None else user.proactive_enabled
        user.proactive_frequency = user.proactive_frequency or "normal"
        user.timezone = user.timezone or "Asia/Ho_Chi_Minh"
        return user

    user = User(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
    )
    session.add(user)
    await session.flush()
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    return (await session.execute(stmt)).scalars().first()


async def update_user_profile(
    session: AsyncSession,
    user: User,
    target_level: str,
    days_left: int,
    daily_minutes: int,
) -> User:
    user.target_level = target_level
    user.days_left = days_left
    user.daily_minutes = daily_minutes
    await session.flush()
    return user


async def list_users_with_reminders(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.reminder_enabled.is_(True))
    return list((await session.execute(stmt)).scalars().all())


async def touch_user_interaction(session: AsyncSession, telegram_user: TelegramUser) -> User:
    user = await get_or_create_user(session, telegram_user)
    user.last_interaction_at = datetime.now(timezone.utc)
    await session.flush()
    return user
