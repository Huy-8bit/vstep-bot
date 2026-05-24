from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mistake import MistakeBook

VALID_MISTAKE_TYPES = {"grammar", "vocabulary", "coherence", "task_response"}


async def save_mistakes_from_metadata(
    session: AsyncSession,
    user_id: int,
    metadata: dict,
) -> list[MistakeBook]:
    mistakes = metadata.get("mistakes") or []
    saved: list[MistakeBook] = []
    for item in mistakes[:5]:
        original = str(item.get("original_text") or "").strip()
        corrected = str(item.get("corrected_text") or "").strip()
        explanation = str(item.get("explanation_vi") or "").strip()
        mistake_type = str(item.get("mistake_type") or "grammar").strip()
        if mistake_type not in VALID_MISTAKE_TYPES:
            mistake_type = "grammar"
        if not original or not corrected or not explanation:
            continue

        mistake = MistakeBook(
            user_id=user_id,
            original_text=original,
            corrected_text=corrected,
            explanation_vi=explanation,
            mistake_type=mistake_type,
        )
        session.add(mistake)
        saved.append(mistake)

    if saved:
        await session.flush()
    return saved


async def get_recent_mistakes(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> list[MistakeBook]:
    stmt = (
        select(MistakeBook)
        .where(MistakeBook.user_id == user_id)
        .order_by(desc(MistakeBook.created_at))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


def format_recent_mistakes(mistakes: list[MistakeBook]) -> str:
    if not mistakes:
        return "Bạn chưa có lỗi sai nào được lưu. Hãy dùng /check để chấm một bài Writing trước."

    lines = ["Your recent mistakes:"]
    for index, mistake in enumerate(mistakes, start=1):
        lines.extend(
            [
                "",
                f"{index}. {mistake.mistake_type.replace('_', ' ').title()}",
                f"Wrong: {mistake.original_text}",
                f"Correct: {mistake.corrected_text}",
                f"Reason: {mistake.explanation_vi}",
            ]
        )
    lines.append("")
    lines.append("Gõ /review_mistakes để luyện lại từ các lỗi này.")
    return "\n".join(lines)


def build_mistakes_text(mistakes: list[MistakeBook]) -> str:
    return "\n".join(
        (
            f"{index}. Type: {mistake.mistake_type}\n"
            f"Wrong: {mistake.original_text}\n"
            f"Correct: {mistake.corrected_text}\n"
            f"Reason: {mistake.explanation_vi}"
        )
        for index, mistake in enumerate(mistakes, start=1)
    )


def build_local_review_exercises(mistakes: list[MistakeBook]) -> str:
    if not mistakes:
        return "Chưa có lỗi để tạo bài review. Hãy dùng /check trước."

    selected = mistakes[:5]
    lines = ["5 bài tập review lỗi sai của bạn:"]
    answer_key = ["", "Answer key:"]
    for index, mistake in enumerate(selected, start=1):
        lines.append(f"{index}. Rewrite this sentence correctly:\n{mistake.original_text}")
        answer_key.append(f"{index}. {mistake.corrected_text}")
    return "\n\n".join(lines + answer_key)

