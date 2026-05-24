from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def make_async_database_url(database_url: str) -> str:
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url
    if database_url.startswith("sqlite://"):
        return database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return database_url


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    make_async_database_url(settings.database_url),
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_vocabulary_columns)
        await conn.run_sync(_ensure_user_columns)


def _ensure_vocabulary_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if not inspector.has_table("vocabulary_items"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("vocabulary_items")}
    required_columns = {
        "example_meaning_vi": "TEXT",
        "sentence_breakdown": "TEXT",
        "useful_pattern": "TEXT",
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            sync_conn.exec_driver_sql(
                f"ALTER TABLE vocabulary_items ADD COLUMN {column_name} {column_type}"
            )


def _ensure_user_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if not inspector.has_table("users"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    dialect = sync_conn.dialect.name
    if dialect == "postgresql":
        bool_true = "BOOLEAN DEFAULT TRUE NOT NULL"
        bool_false = "BOOLEAN DEFAULT FALSE NOT NULL"
        integer_zero = "INTEGER DEFAULT 0 NOT NULL"
        timestamp = "TIMESTAMP WITH TIME ZONE"
        varchar_10 = "VARCHAR(10)"
        varchar_20 = "VARCHAR(20)"
        varchar_64 = "VARCHAR(64)"
    else:
        bool_true = "BOOLEAN DEFAULT 1 NOT NULL"
        bool_false = "BOOLEAN DEFAULT 0 NOT NULL"
        integer_zero = "INTEGER DEFAULT 0 NOT NULL"
        timestamp = "DATETIME"
        varchar_10 = "VARCHAR(10)"
        varchar_20 = "VARCHAR(20)"
        varchar_64 = "VARCHAR(64)"

    required_columns = {
        "proactive_enabled": bool_true,
        "last_interaction_at": timestamp,
        "last_proactive_sent_at": timestamp,
        "proactive_frequency": f"{varchar_20} DEFAULT 'normal' NOT NULL",
        "timezone": f"{varchar_64} DEFAULT 'Asia/Ho_Chi_Minh' NOT NULL",
        "proactive_quiet_until": timestamp,
        "proactive_messages_sent_date": varchar_10,
        "proactive_messages_sent_count": integer_zero,
        "proactive_daily_reminder_date": varchar_10,
        "proactive_morning_date": varchar_10,
        "proactive_night_date": varchar_10,
        "proactive_checkin_date": varchar_10,
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            sync_conn.exec_driver_sql(
                f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
            )


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
