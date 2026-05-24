from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VocabularyItem(Base):
    __tablename__ = "vocabulary_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    phrase: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    meaning_vi: Mapped[str] = mapped_column(Text, nullable=False)
    example_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    example_meaning_vi: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentence_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    useful_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    collocation: Mapped[str] = mapped_column(String(255), nullable=False)
    writing_usage: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(10), index=True, nullable=False)

    quiz_results = relationship("QuizResult", back_populates="vocab")
