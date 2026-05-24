from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.writing import StudyPlan


def create_plan_text(user: User) -> str:
    days = max(1, user.days_left or 7)
    daily_minutes = user.daily_minutes or 45
    target_level = user.target_level or "B2"

    header = (
        f"Kế hoạch ôn VSTEP cấp tốc\n"
        f"Target: {target_level}\n"
        f"Thời gian: {days} ngày, khoảng {daily_minutes} phút/ngày\n"
    )

    if days <= 2:
        body = [
            "Day 1:",
            "- 50 useful phrases theo Education, Technology, Environment, Work, Health.",
            "- Làm 2 đề Task 1: complaint + apology.",
            "- Viết 1 bài Task 2 full essay, ưu tiên organization rõ.",
            "- Review common grammar mistakes: subject-verb agreement, articles, tense.",
            "",
            "Day 2:",
            "- Review templates mở bài/kết bài Task 1 và Task 2.",
            "- Làm 1 mock Writing test đủ thời gian.",
            "- Sửa lại personal mistakes trong /mistakes.",
            "- Memorize opening/conclusion phrases và 20 collocations hay dùng.",
        ]
    elif days <= 7:
        body = []
        focus = [
            "Vocabulary + quiz",
            "Task 1 letters",
            "Task 2 opinion essay",
            "Task 2 problem-solution",
            "Review mistakes",
            "Mock Writing test",
            "Light review + templates",
        ]
        for day in range(1, days + 1):
            body.extend(
                [
                    f"Day {day}:",
                    f"- Main focus: {focus[(day - 1) % len(focus)]}.",
                    "- 10-20 VSTEP phrases + 1 quick quiz.",
                    "- Write one paragraph or one full task depending on your time.",
                    "- Save and review at least 3 mistakes.",
                    "",
                ]
            )
    elif days <= 14:
        body = []
        for day in range(1, days + 1):
            if day in {4, 8, 12}:
                focus = "Spaced repetition: review old vocabulary and mistake book."
            elif day % 2 == 0:
                focus = "Task 2 outline + one body paragraph."
            else:
                focus = "Task 1 letter + useful phrases."
            body.extend(
                [
                    f"Day {day}:",
                    f"- {focus}",
                    "- 10 phrases theo 1 topic.",
                    "- 1 quiz nhanh.",
                    "- 10 phút sửa lỗi cá nhân.",
                    "",
                ]
            )
    else:
        body = []
        for day in range(1, days + 1):
            focus = "Vocabulary + mistake review"
            if day % 3 == 1:
                focus = "Task 1 practice"
            elif day % 3 == 2:
                focus = "Task 2 planning and paragraph writing"
            if day % 7 == 0:
                focus = "Weekly mock test + deep correction"
            body.extend(
                [
                    f"Day {day}:",
                    f"- {focus}.",
                    "- 10 VSTEP phrases with spaced repetition.",
                    "- 1 short quiz or sentence upgrade.",
                    "",
                ]
            )

    return header + "\n" + "\n".join(body).strip()


async def save_study_plan(
    session: AsyncSession,
    user_id: int,
    plan_text: str,
    days: int,
) -> StudyPlan:
    plan = StudyPlan(user_id=user_id, plan_text=plan_text, days=days)
    session.add(plan)
    await session.flush()
    return plan

