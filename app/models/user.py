from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    days_left: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_time: Mapped[str] = mapped_column(String(5), default="20:00", nullable=False)
    proactive_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_proactive_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proactive_frequency: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Ho_Chi_Minh", nullable=False)
    proactive_quiet_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proactive_messages_sent_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    proactive_messages_sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    proactive_daily_reminder_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    proactive_morning_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    proactive_night_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    proactive_checkin_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    writing_submissions = relationship(
        "WritingSubmission",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mistakes = relationship("MistakeBook", back_populates="user", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    conversation_state = relationship(
        "ConversationState",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
