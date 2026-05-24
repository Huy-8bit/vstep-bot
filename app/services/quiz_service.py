from dataclasses import asdict, dataclass
import random
import re
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizResult
from app.models.vocabulary import VocabularyItem
from app.services.vocab_service import get_random_items

QUIZ_TYPES = ["multiple_choice", "fill_blank", "translate_vi_to_en", "meaning_vi", "write_phrase"]
OPTION_LABELS = ["A", "B", "C", "D"]


@dataclass
class QuizQuestion:
    quiz_type: str
    vocab_id: int
    prompt: str
    correct_answer: str
    explanation: str
    options: dict[str, str] | None = None
    correct_option: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


async def build_quiz_question(session: AsyncSession, quiz_type: str | None = None) -> QuizQuestion:
    items = await get_random_items(session, limit=5)
    if len(items) < 4:
        raise ValueError("Not enough vocabulary items to create a quiz.")

    answer = items[0]
    quiz_type = quiz_type if quiz_type in QUIZ_TYPES else random.choice(QUIZ_TYPES)
    if quiz_type == "multiple_choice":
        return _build_multiple_choice(answer, items[1:4])
    if quiz_type == "fill_blank":
        return _build_fill_blank(answer)
    if quiz_type == "meaning_vi":
        return _build_meaning_vi(answer)
    if quiz_type == "write_phrase":
        return _build_write_phrase(answer)
    return _build_translate(answer)


def _build_multiple_choice(answer: VocabularyItem, distractors: list[VocabularyItem]) -> QuizQuestion:
    options = [answer.phrase, *(item.phrase for item in distractors)]
    random.shuffle(options)
    option_map = dict(zip(OPTION_LABELS, options, strict=True))
    correct_option = next(label for label, phrase in option_map.items() if phrase == answer.phrase)
    options_text = "\n".join(f"{label}. {phrase}" for label, phrase in option_map.items())
    prompt = (
        f"Multiple choice:\nChoose the best English phrase for this meaning:\n"
        f"{answer.meaning_vi}\n\n{options_text}\n\nReply A, B, C, D or the phrase."
    )
    return QuizQuestion(
        quiz_type="multiple_choice",
        vocab_id=answer.id,
        prompt=prompt,
        correct_answer=answer.phrase,
        correct_option=correct_option,
        options=option_map,
        explanation=f"Đáp án đúng là {answer.phrase}: {answer.writing_usage}",
    )


def _build_fill_blank(answer: VocabularyItem) -> QuizQuestion:
    pattern = re.compile(re.escape(answer.phrase), re.IGNORECASE)
    if pattern.search(answer.example_sentence):
        blank_sentence = pattern.sub("____", answer.example_sentence, count=1)
    else:
        blank_sentence = f"Use a phrase meaning '{answer.meaning_vi}' in this sentence: ____."

    prompt = f"Fill in the blank:\n{blank_sentence}\n\nReply with the missing word/phrase."
    return QuizQuestion(
        quiz_type="fill_blank",
        vocab_id=answer.id,
        prompt=prompt,
        correct_answer=answer.phrase,
        explanation=f"Cụm đúng là {answer.phrase}. Collocation: {answer.collocation}.",
    )


def _build_translate(answer: VocabularyItem) -> QuizQuestion:
    prompt = (
        "Translate Vietnamese to English:\n"
        f"{answer.meaning_vi}\n\nReply with a suitable VSTEP phrase."
    )


def _build_meaning_vi(answer: VocabularyItem) -> QuizQuestion:
    prompt = (
        "Hỏi nghĩa của từ/cụm:\n"
        f"{answer.phrase}\n\n"
        "Cụm này nghĩa là gì trong tiếng Việt? Reply bằng nghĩa ngắn gọn."
    )
    return QuizQuestion(
        quiz_type="meaning_vi",
        vocab_id=answer.id,
        prompt=prompt,
        correct_answer=answer.meaning_vi,
        explanation=(
            f"{answer.phrase} = {answer.meaning_vi}.\n"
            f"Example: {answer.example_sentence}\n"
            f"Writing usage: {answer.writing_usage}"
        ),
    )


def _build_write_phrase(answer: VocabularyItem) -> QuizQuestion:
    prompt = (
        "Cho nghĩa, viết từ/cụm tiếng Anh:\n"
        f"{answer.meaning_vi}\n\n"
        "Reply bằng word/phrase tiếng Anh phù hợp."
    )
    return QuizQuestion(
        quiz_type="write_phrase",
        vocab_id=answer.id,
        prompt=prompt,
        correct_answer=answer.phrase,
        explanation=(
            f"Cụm đúng là {answer.phrase}.\n"
            f"Example: {answer.example_sentence}\n"
            f"Collocation: {answer.collocation}"
        ),
    )
    return QuizQuestion(
        quiz_type="translate_vi_to_en",
        vocab_id=answer.id,
        prompt=prompt,
        correct_answer=answer.phrase,
        explanation=f"Cách diễn đạt tự nhiên: {answer.phrase}. Example: {answer.example_sentence}",
    )


def normalize_answer(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"^[\s.:\-]+|[\s.:\-]+$", "", normalized)
    return normalized


def normalize_vi(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = normalized.replace("đ", "d")
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def is_vi_meaning_close(user_answer: str, correct_answer: str) -> bool:
    user_tokens = set(normalize_vi(user_answer).split())
    correct_tokens = set(normalize_vi(correct_answer).split())
    if not user_tokens or not correct_tokens:
        return False
    overlap = user_tokens & correct_tokens
    return len(overlap) >= max(1, min(2, len(correct_tokens)))


def check_quiz_answer(question: dict, user_answer: str) -> tuple[bool, str]:
    user_answer_clean = normalize_answer(user_answer)
    correct_answer = question["correct_answer"]
    correct_clean = normalize_answer(correct_answer)

    if question.get("quiz_type") == "multiple_choice":
        option = user_answer_clean.upper()
        correct_option = question.get("correct_option")
        if option == correct_option:
            return True, question["explanation"]
        chosen_phrase = (question.get("options") or {}).get(option)
        if chosen_phrase and normalize_answer(chosen_phrase) == correct_clean:
            return True, question["explanation"]

    if question.get("quiz_type") == "meaning_vi":
        if is_vi_meaning_close(user_answer, correct_answer):
            return True, question["explanation"]
        return False, f"Chưa đúng lắm. Nghĩa gợi ý: {correct_answer}.\n{question['explanation']}"

    if user_answer_clean == correct_clean:
        return True, question["explanation"]

    return False, f"Chưa đúng. Đáp án gợi ý: {correct_answer}. {question['explanation']}"


async def save_quiz_result(
    session: AsyncSession,
    user_id: int,
    vocab_id: int,
    is_correct: bool,
) -> QuizResult:
    result = QuizResult(user_id=user_id, vocab_id=vocab_id, is_correct=is_correct)
    session.add(result)
    await session.flush()
    return result
