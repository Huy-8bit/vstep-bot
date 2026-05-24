from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re

from app.prompts.intent_classification_prompt import build_intent_classification_messages
from app.services.openai_service import OpenAIServiceError, openai_service
from app.services.vocab_service import TOPICS

SUPPORTED_INTENTS = {
    "vocab_request",
    "quiz_request",
    "task1_request",
    "task2_request",
    "check_writing",
    "upgrade_sentence",
    "explain_sentence",
    "explain_phrase",
    "study_plan",
    "mistake_review",
    "template_request",
    "casual_motivation",
    "general_chat",
}


@dataclass
class IntentResult:
    intent: str
    confidence: float
    extracted_text: str = ""
    topic: str = ""
    task_type: str = ""
    should_ask_followup: bool = False
    followup_question: str = ""
    days_left: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


KEYWORDS: dict[str, list[str]] = {
    "vocab_request": ["học từ", "từ vựng", "vocab", "phrase", "cụm từ", "học topic"],
    "quiz_request": ["quiz", "kiểm tra", "test tôi", "đố tôi", "làm bài nhanh"],
    "task1_request": ["task 1", "task1", "viết thư", "email", "letter", "complaint", "apology"],
    "task2_request": ["task 2", "task2", "essay", "luận", "bài luận", "agree disagree"],
    "check_writing": ["chấm bài", "sửa bài", "check writing", "feedback", "xem bài này"],
    "upgrade_sentence": [
        "nâng cấp câu",
        "viết hay hơn",
        "viết lại câu này hay hơn",
        "paraphrase",
        "rewrite",
        "hay hơn",
    ],
    "explain_sentence": ["nghĩa là gì", "dịch câu", "giải thích câu", "breakdown", "câu này"],
    "explain_phrase": ["cụm", "phrase", "collocation", "dùng sao", "dùng như thế nào", "là gì"],
    "study_plan": ["kế hoạch", "plan", "mai thi", "ôn cấp tốc", "còn"],
    "mistake_review": ["lỗi sai", "mistake", "ôn lỗi", "review lỗi"],
    "template_request": ["mẫu", "template", "mở bài", "kết bài", "câu dùng được"],
    "casual_motivation": ["lười", "mệt", "chán", "không muốn học", "nản"],
}


async def detect_intent(text: str) -> IntentResult:
    rule_result = detect_intent_rule_based(text)
    if rule_result.confidence >= 0.55:
        return rule_result

    try:
        ai_result = await detect_intent_with_openai(text)
    except OpenAIServiceError:
        return rule_result

    return ai_result if ai_result.confidence > rule_result.confidence else rule_result


def detect_intent_rule_based(text: str) -> IntentResult:
    raw = text.strip()
    lower = raw.lower()
    extracted_text = extract_after_marker(raw)
    topic = extract_topic(lower)
    days_left = extract_days_left(lower)

    if "mai" in lower and "thi" in lower:
        return IntentResult("study_plan", 0.9, topic=topic, days_left=1)
    if days_left is not None and ("thi" in lower or "ôn" in lower or "plan" in lower or "kế hoạch" in lower):
        return IntentResult("study_plan", 0.92, topic=topic, days_left=days_left)

    if ("hỏi nghĩa" in lower or "nghĩa của từ" in lower or "nghĩa của cụm" in lower) and (
        "quiz" in lower or "hỏi" in lower or "đố" in lower
    ):
        return IntentResult("quiz_request", 0.9, task_type="meaning_vi")

    if ("cho nghĩa" in lower or "đưa nghĩa" in lower) and (
        "viết từ" in lower or "viết cụm" in lower or "đoán từ" in lower or "ghi từ" in lower
    ):
        return IntentResult("quiz_request", 0.9, task_type="write_phrase")

    if any(keyword in lower for keyword in KEYWORDS["check_writing"]):
        return IntentResult(
            "check_writing",
            0.9,
            extracted_text=extracted_text,
            task_type=extract_task_type(lower),
        )

    if any(keyword in lower for keyword in KEYWORDS["upgrade_sentence"]):
        return IntentResult("upgrade_sentence", 0.9, extracted_text=extracted_text)

    if _looks_like_explain_phrase(lower, raw):
        return IntentResult("explain_phrase", 0.82, extracted_text=extract_phrase(raw))

    if any(keyword in lower for keyword in KEYWORDS["explain_sentence"]):
        return IntentResult("explain_sentence", 0.82, extracted_text=extracted_text)

    if any(keyword in lower for keyword in KEYWORDS["template_request"]):
        return IntentResult("template_request", 0.86, task_type=extract_task_type(lower))

    if any(keyword in lower for keyword in KEYWORDS["task1_request"]):
        return IntentResult("task1_request", 0.88, task_type="Task 1")

    if any(keyword in lower for keyword in KEYWORDS["task2_request"]):
        return IntentResult("task2_request", 0.88, task_type="Task 2")

    if any(keyword in lower for keyword in KEYWORDS["quiz_request"]):
        return IntentResult("quiz_request", 0.86, topic=topic)

    if any(keyword in lower for keyword in KEYWORDS["mistake_review"]):
        return IntentResult("mistake_review", 0.86)

    if any(keyword in lower for keyword in KEYWORDS["casual_motivation"]):
        return IntentResult("casual_motivation", 0.86)

    if any(keyword in lower for keyword in KEYWORDS["vocab_request"]):
        return IntentResult("vocab_request", 0.82, topic=topic)

    return IntentResult(
        "general_chat",
        0.4,
        extracted_text=extracted_text,
        topic=topic,
        days_left=days_left,
        should_ask_followup=True,
        followup_question="Bạn muốn tôi làm gì với nội dung này?",
    )


async def detect_intent_with_openai(text: str) -> IntentResult:
    response = await openai_service.chat(build_intent_classification_messages(text), temperature=0.0)
    data = _extract_json(response)
    intent = data.get("intent", "general_chat")
    if intent not in SUPPORTED_INTENTS:
        intent = "general_chat"
    confidence = _safe_float(data.get("confidence"), 0.4)
    return IntentResult(
        intent=intent,
        confidence=max(0.0, min(1.0, confidence)),
        extracted_text=str(data.get("extracted_text") or ""),
        topic=str(data.get("topic") or ""),
        task_type=str(data.get("task_type") or ""),
        should_ask_followup=bool(data.get("should_ask_followup", confidence < 0.55)),
        followup_question=str(data.get("followup_question") or ""),
        days_left=extract_days_left(text.lower()),
    )


def extract_after_marker(text: str) -> str:
    markers = [
        ":",
        "：",
        "giúp tôi",
        "giùm tôi",
        "câu này",
        "bài này",
        "này",
    ]
    for marker in markers:
        if marker in text:
            candidate = text.split(marker, 1)[1].strip()
            if candidate:
                return candidate.strip("\"'“”")
    return ""


def extract_topic(lower_text: str) -> str:
    topic_aliases = {
        "education": "Education",
        "school": "Education",
        "học": "Education",
        "technology": "Technology",
        "công nghệ": "Technology",
        "environment": "Environment",
        "môi trường": "Environment",
        "health": "Health",
        "sức khỏe": "Health",
        "work": "Work",
        "công việc": "Work",
        "travel": "Travel",
        "du lịch": "Travel",
        "culture": "Culture",
        "văn hóa": "Culture",
        "family": "Family",
        "gia đình": "Family",
        "city": "City life",
        "thành phố": "City life",
        "social media": "Social media",
        "mạng xã hội": "Social media",
    }
    for keyword, topic in topic_aliases.items():
        if keyword in lower_text and topic in TOPICS:
            return topic
    return ""


def extract_task_type(lower_text: str) -> str:
    if "task 1" in lower_text or "task1" in lower_text or "letter" in lower_text or "viết thư" in lower_text:
        return "Task 1"
    if "task 2" in lower_text or "task2" in lower_text or "essay" in lower_text or "bài luận" in lower_text:
        return "Task 2"
    return ""


def extract_days_left(lower_text: str) -> int | None:
    if "mai" in lower_text and "thi" in lower_text:
        return 1
    match = re.search(r"còn\s+(\d{1,3})\s+ngày", lower_text)
    if not match:
        match = re.search(r"(\d{1,3})\s+ngày\s+nữa", lower_text)
    if match:
        days = int(match.group(1))
        return max(1, min(365, days))
    return None


def _looks_like_explain_phrase(lower_text: str, raw: str) -> bool:
    if "cụm" in lower_text or "collocation" in lower_text:
        return True
    if " là gì" in lower_text and len(raw.split()) <= 12:
        return True
    return False


def extract_phrase(text: str) -> str:
    patterns = [
        r"giải thích cụm\s+(.+)",
        r"cụm\s+(.+?)\s+(?:là gì|dùng sao|dùng như thế nào)",
        r"(.+?)\s+là gì",
    ]
    lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lower, re.IGNORECASE)
        if match:
            return match.group(1).strip(" :?\"'“”")
    extracted = extract_after_marker(text)
    return extracted or text.strip()


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _safe_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
