from html import escape

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vocabulary import VocabularyItem
from app.prompts.explain_sentence_prompt import build_explain_sentence_messages
from app.services.openai_service import OpenAIServiceError, openai_service
from app.services.vocab_service import build_vocabulary_details


async def explain_sentence(sentence: str) -> str:
    try:
        return await openai_service.chat(
            build_explain_sentence_messages(sentence, item_type="sentence"),
            temperature=0.2,
        )
    except OpenAIServiceError:
        return explain_sentence_fallback(sentence)


async def explain_phrase(session: AsyncSession, phrase: str) -> str:
    vocab_item = await find_vocabulary_phrase(session, phrase)
    if vocab_item:
        details = build_vocabulary_details(
            phrase=vocab_item.phrase,
            meaning_vi=vocab_item.meaning_vi,
            example_sentence=vocab_item.example_sentence,
            writing_usage=vocab_item.writing_usage,
        )
        example_meaning = vocab_item.example_meaning_vi or details["example_meaning_vi"]
        breakdown = vocab_item.sentence_breakdown or details["sentence_breakdown"]
        pattern = vocab_item.useful_pattern or details["useful_pattern"]
        return "\n".join(
            [
                f"📘 <b>{escape(vocab_item.phrase)}</b>",
                f"🇻🇳 <b>Nghĩa:</b> {escape(vocab_item.meaning_vi)}",
                "",
                "🧩 <b>Example:</b>",
                f"<i>{escape(vocab_item.example_sentence)}</i>",
                "",
                f"💬 <b>Nghĩa câu:</b> {escape(example_meaning)}",
                "",
                "🔍 <b>Breakdown:</b>",
                *[f"• {escape(line)}" for line in breakdown.splitlines() if line.strip()],
                "",
                "🧠 <b>Pattern:</b>",
                *[escape(line) for line in pattern.splitlines() if line.strip()],
                "",
                f"✍️ <b>Writing usage:</b> {escape(vocab_item.writing_usage)}",
            ]
        )

    try:
        result = await openai_service.chat(
            build_explain_sentence_messages(phrase, item_type="phrase"),
            temperature=0.2,
        )
        return escape(result)
    except OpenAIServiceError:
        return explain_phrase_fallback(phrase)


async def find_vocabulary_phrase(session: AsyncSession, phrase: str) -> VocabularyItem | None:
    normalized = phrase.strip().lower()
    if not normalized:
        return None
    stmt = select(VocabularyItem).where(VocabularyItem.phrase.ilike(normalized)).limit(1)
    item = (await session.execute(stmt)).scalars().first()
    if item:
        return item
    stmt = select(VocabularyItem).where(VocabularyItem.phrase.ilike(f"%{normalized}%")).limit(1)
    return (await session.execute(stmt)).scalars().first()


def explain_sentence_fallback(sentence: str) -> str:
    if sentence.strip().lower().rstrip(".") == "a supportive learning environment helps students stay motivated":
        return "\n".join(
            [
                "📘 <b>Nghĩa câu:</b>",
                "Một môi trường học tập có tính hỗ trợ giúp học sinh duy trì động lực.",
                "",
                "🔍 <b>Breakdown:</b>",
                "• A supportive learning environment = một môi trường học tập có tính hỗ trợ",
                "• helps students = giúp học sinh",
                "• stay motivated = duy trì động lực",
                "",
                "🧠 <b>Pattern hay:</b>",
                "A supportive + noun + helps + someone + V",
                "",
                "✍️ <b>Câu tương tự:</b>",
                "A supportive teacher helps students improve their confidence.",
            ]
        )
    safe_sentence = escape(sentence.strip())
    return "\n".join(
        [
            "📘 <b>Nghĩa câu:</b>",
            "Mình chưa gọi được AI để dịch thật tự nhiên, nhưng có thể tách câu theo hướng này:",
            "",
            "🔍 <b>Breakdown:</b>",
            f"• <i>{safe_sentence}</i> = câu chính cần hiểu theo chủ ngữ + động từ + ý bổ sung",
            "• Xác định subject trước, sau đó tìm verb chính, rồi đọc phần còn lại như kết quả/chi tiết.",
            "",
            "🧠 <b>Pattern hay:</b>",
            "Subject + verb + object/result.",
        ]
    )


def explain_phrase_fallback(phrase: str) -> str:
    return "\n".join(
        [
            f"📘 <b>{escape(phrase.strip())}</b>",
            "Mình chưa có cụm này trong vocabulary seed và hiện không gọi được AI.",
            "Bạn có thể gửi cả câu chứa cụm này, mình sẽ breakdown theo ngữ cảnh.",
        ]
    )
