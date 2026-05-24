from dataclasses import dataclass
import json
import random
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.writing import WritingSubmission


@dataclass(frozen=True)
class WritingTask:
    task_type: str
    prompt: str
    subtype: str
    bullet_points: list[str]
    structure: list[str]
    useful_phrases: list[str]
    word_requirement: str


TASK1_PROMPTS = [
    WritingTask(
        task_type="Task 1",
        subtype="Apology letter",
        prompt="Write a letter to your neighbor to apologize for noise from your party.",
        bullet_points=[
            "describe the reason for the noise",
            "apologize",
            "explain what you will do next time",
        ],
        structure=[
            "Paragraph 1: State the purpose and apologize clearly.",
            "Paragraph 2: Explain the situation and show responsibility.",
            "Paragraph 3: Promise a solution and close politely.",
        ],
        useful_phrases=[
            "I am writing to apologize for...",
            "I understand that this may have caused...",
            "I will make sure that...",
        ],
        word_requirement="Write at least 120 words.",
    ),
    WritingTask(
        task_type="Task 1",
        subtype="Complaint letter",
        prompt="Write a letter to a store manager to complain about a faulty electronic device you bought.",
        bullet_points=[
            "describe what you bought",
            "explain the problem",
            "say what action you expect",
        ],
        structure=[
            "Paragraph 1: State why you are writing.",
            "Paragraph 2: Describe the product and the problem.",
            "Paragraph 3: Request a refund, replacement, or repair.",
        ],
        useful_phrases=[
            "I am writing to express my dissatisfaction with...",
            "The main problem is that...",
            "I would appreciate it if you could...",
        ],
        word_requirement="Write at least 120 words.",
    ),
    WritingTask(
        task_type="Task 1",
        subtype="Request letter",
        prompt="Write a letter to your course coordinator to request a change in your class schedule.",
        bullet_points=[
            "explain your current situation",
            "request a suitable change",
            "say why this change would help you",
        ],
        structure=[
            "Paragraph 1: Explain the purpose of the letter.",
            "Paragraph 2: Give reasons and details.",
            "Paragraph 3: Make a polite request and thank the reader.",
        ],
        useful_phrases=[
            "I am writing to ask whether it would be possible to...",
            "Due to...",
            "Thank you for considering my request.",
        ],
        word_requirement="Write at least 120 words.",
    ),
    WritingTask(
        task_type="Task 1",
        subtype="Invitation letter",
        prompt="Write a letter to invite an English-speaking friend to a cultural event in your city.",
        bullet_points=[
            "describe the event",
            "explain why your friend may enjoy it",
            "suggest when and where to meet",
        ],
        structure=[
            "Paragraph 1: Invite your friend and introduce the event.",
            "Paragraph 2: Give interesting details.",
            "Paragraph 3: Suggest arrangements and close warmly.",
        ],
        useful_phrases=[
            "I would like to invite you to...",
            "It would be a great chance to...",
            "Let me know if you can make it.",
        ],
        word_requirement="Write at least 120 words.",
    ),
    WritingTask(
        task_type="Task 1",
        subtype="Application letter",
        prompt="Write a letter to apply for a part-time assistant position at an English center.",
        bullet_points=[
            "state the position you are applying for",
            "describe your relevant skills",
            "explain your availability",
        ],
        structure=[
            "Paragraph 1: Say which position you want.",
            "Paragraph 2: Present skills and experience.",
            "Paragraph 3: Mention availability and close politely.",
        ],
        useful_phrases=[
            "I am writing to apply for...",
            "I believe I would be suitable for this position because...",
            "I am available for an interview at your convenience.",
        ],
        word_requirement="Write at least 120 words.",
    ),
    WritingTask(
        task_type="Task 1",
        subtype="Thank-you letter",
        prompt="Write a letter to thank a teacher who helped you improve your English writing.",
        bullet_points=[
            "say why you are grateful",
            "describe how the teacher helped you",
            "explain how this has affected your study",
        ],
        structure=[
            "Paragraph 1: Say thank you and state the reason.",
            "Paragraph 2: Give specific examples of support.",
            "Paragraph 3: Explain the positive impact and close warmly.",
        ],
        useful_phrases=[
            "I am writing to express my sincere thanks for...",
            "Your guidance helped me to...",
            "I truly appreciate your support.",
        ],
        word_requirement="Write at least 120 words.",
    ),
]

TASK2_PROMPTS = [
    WritingTask(
        task_type="Task 2",
        subtype="Opinion essay",
        prompt="Some people believe that students should study online instead of attending traditional classes. What is your opinion?",
        bullet_points=[],
        structure=[
            "Introduction: Paraphrase the topic and state your opinion.",
            "Body 1: Give the first reason with an example.",
            "Body 2: Give the second reason or discuss a limitation.",
            "Conclusion: Summarize your opinion clearly.",
        ],
        useful_phrases=[
            "In my opinion, ...",
            "One major reason is that...",
            "For example, ...",
            "In conclusion, ...",
        ],
        word_requirement="Write about 250 words.",
    ),
    WritingTask(
        task_type="Task 2",
        subtype="Advantages and disadvantages",
        prompt="Many people now work from home. Discuss the advantages and disadvantages of this trend.",
        bullet_points=[],
        structure=[
            "Introduction: Introduce the trend.",
            "Body 1: Discuss advantages.",
            "Body 2: Discuss disadvantages.",
            "Conclusion: Give a balanced summary.",
        ],
        useful_phrases=[
            "One clear advantage is...",
            "On the other hand, ...",
            "This can lead to...",
            "Overall, ...",
        ],
        word_requirement="Write about 250 words.",
    ),
    WritingTask(
        task_type="Task 2",
        subtype="Discuss both views",
        prompt="Some people think children should spend more time studying, while others believe they need more time for sports and hobbies. Discuss both views and give your opinion.",
        bullet_points=[],
        structure=[
            "Introduction: Paraphrase both views and state your position.",
            "Body 1: Explain why studying is important.",
            "Body 2: Explain why sports and hobbies matter.",
            "Conclusion: Give your balanced opinion.",
        ],
        useful_phrases=[
            "Some people argue that...",
            "However, others believe that...",
            "From my perspective, ...",
            "A balanced approach would be...",
        ],
        word_requirement="Write about 250 words.",
    ),
    WritingTask(
        task_type="Task 2",
        subtype="Problem and solution",
        prompt="In many cities, traffic congestion is becoming more serious. What problems does this cause, and what solutions can be suggested?",
        bullet_points=[],
        structure=[
            "Introduction: Introduce the issue.",
            "Body 1: Explain main problems.",
            "Body 2: Suggest practical solutions.",
            "Conclusion: Summarize the key points.",
        ],
        useful_phrases=[
            "This issue can cause several problems.",
            "A practical solution would be to...",
            "The government should...",
            "If these measures are taken, ...",
        ],
        word_requirement="Write about 250 words.",
    ),
    WritingTask(
        task_type="Task 2",
        subtype="Cause and effect",
        prompt="More young people are spending a lot of time on social media. What are the causes and effects of this trend?",
        bullet_points=[],
        structure=[
            "Introduction: Present the trend.",
            "Body 1: Discuss causes.",
            "Body 2: Discuss effects.",
            "Conclusion: Summarize and add a final comment.",
        ],
        useful_phrases=[
            "There are several reasons why...",
            "As a result, ...",
            "This may have a negative impact on...",
            "To some extent, ...",
        ],
        word_requirement="Write about 250 words.",
    ),
    WritingTask(
        task_type="Task 2",
        subtype="Agree or disagree",
        prompt="Some people say that protecting the environment is the responsibility of the government, not individuals. To what extent do you agree or disagree?",
        bullet_points=[],
        structure=[
            "Introduction: State your level of agreement.",
            "Body 1: Explain the role of government.",
            "Body 2: Explain the role of individuals.",
            "Conclusion: Restate your view.",
        ],
        useful_phrases=[
            "I partly agree with this view because...",
            "Governments can...",
            "Individuals also have a responsibility to...",
            "Therefore, ...",
        ],
        word_requirement="Write about 250 words.",
    ),
]


def random_task1() -> WritingTask:
    return random.choice(TASK1_PROMPTS)


def random_task2() -> WritingTask:
    return random.choice(TASK2_PROMPTS)


def format_task(task: WritingTask) -> str:
    lines = [
        f"{task.task_type} - {task.subtype}",
        "",
        task.prompt,
        "",
    ]
    if task.bullet_points:
        lines.append("You should:")
        lines.extend(f"- {point}" for point in task.bullet_points)
        lines.append("")
    lines.append("Suggested structure:")
    lines.extend(f"- {item}" for item in task.structure)
    lines.append("")
    lines.append("Useful phrases:")
    lines.extend(f"- {phrase}" for phrase in task.useful_phrases)
    lines.append("")
    lines.append(task.word_requirement)
    return "\n".join(lines)


METADATA_RE = re.compile(r"METADATA_JSON:\s*```json\s*(\{.*?\})\s*```", re.DOTALL)


def extract_feedback_metadata(raw_feedback: str) -> tuple[str, dict]:
    match = METADATA_RE.search(raw_feedback)
    if not match:
        return raw_feedback.strip(), {}

    json_text = match.group(1)
    human_feedback = METADATA_RE.sub("", raw_feedback).strip()
    try:
        metadata = json.loads(json_text)
    except json.JSONDecodeError:
        metadata = {}
    return human_feedback, metadata


def parse_score(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else None


async def save_writing_submission(
    session: AsyncSession,
    user_id: int,
    task_type: str,
    prompt: str,
    original_text: str,
    feedback: str,
    metadata: dict,
) -> WritingSubmission:
    submission = WritingSubmission(
        user_id=user_id,
        task_type=task_type,
        prompt=prompt,
        original_text=original_text,
        feedback=feedback,
        estimated_level=metadata.get("estimated_level"),
        estimated_score=parse_score(metadata.get("estimated_score")),
        improved_version=metadata.get("improved_version"),
    )
    session.add(submission)
    await session.flush()
    return submission

