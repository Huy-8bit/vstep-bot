SYSTEM_PROMPT = """
You are a VSTEP study planner.
Create a practical Vietnamese study plan for VSTEP Writing and vocabulary.
The plan should fit the user's days left, target level, and daily minutes.
Prioritize vocabulary, Task 1 templates, Task 2 outlines, quiz practice, mistake review, and mock writing.
Keep it concise and actionable.
""".strip()


def build_study_plan_messages(target_level: str, days_left: int, daily_minutes: int) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Target level: {target_level}\n"
                f"Days left: {days_left}\n"
                f"Daily minutes: {daily_minutes}"
            ),
        },
    ]

