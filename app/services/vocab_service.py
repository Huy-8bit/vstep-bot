from html import escape

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vocabulary import VocabularyItem
from app.seed.vocabulary_seed import VOCABULARY_SEED

TOPICS = [
    "Education",
    "Technology",
    "Environment",
    "Health",
    "Work",
    "Travel",
    "Culture",
    "Family",
    "City life",
    "Social media",
]

VOCAB_DETAIL_OVERRIDES = {
    "learning environment": {
        "example_meaning_vi": (
            "Một môi trường học tập có tính hỗ trợ giúp học sinh duy trì động lực."
        ),
        "sentence_breakdown": "\n".join(
            [
                "A supportive learning environment = một môi trường học tập có tính hỗ trợ",
                "helps students = giúp học sinh",
                "stay motivated = duy trì động lực",
            ]
        ),
        "useful_pattern": "\n".join(
            [
                "A supportive [noun] helps people + V...",
                "Ví dụ: A supportive teacher helps students improve their confidence.",
            ]
        ),
    }
}


async def seed_vocabulary(session: AsyncSession) -> int:
    total = await session.scalar(select(func.count(VocabularyItem.id)))
    if total:
        await backfill_vocabulary_details(session)
        return 0

    session.add_all(VocabularyItem(**with_vocabulary_details(item)) for item in VOCABULARY_SEED)
    await session.flush()
    return len(VOCABULARY_SEED)


def with_vocabulary_details(item: dict[str, str]) -> dict[str, str]:
    enriched = dict(item)
    details = build_vocabulary_details(
        phrase=enriched["phrase"],
        meaning_vi=enriched["meaning_vi"],
        example_sentence=enriched["example_sentence"],
        writing_usage=enriched["writing_usage"],
    )
    enriched.setdefault("example_meaning_vi", details["example_meaning_vi"])
    enriched.setdefault("sentence_breakdown", details["sentence_breakdown"])
    enriched.setdefault("useful_pattern", details["useful_pattern"])
    return enriched


async def backfill_vocabulary_details(session: AsyncSession) -> int:
    stmt = select(VocabularyItem).where(
        or_(
            VocabularyItem.example_meaning_vi.is_(None),
            VocabularyItem.example_meaning_vi == "",
            VocabularyItem.sentence_breakdown.is_(None),
            VocabularyItem.sentence_breakdown == "",
            VocabularyItem.useful_pattern.is_(None),
            VocabularyItem.useful_pattern == "",
        )
    )
    items = list((await session.execute(stmt)).scalars().all())
    for item in items:
        details = build_vocabulary_details(
            phrase=item.phrase,
            meaning_vi=item.meaning_vi,
            example_sentence=item.example_sentence,
            writing_usage=item.writing_usage,
        )
        item.example_meaning_vi = item.example_meaning_vi or details["example_meaning_vi"]
        item.sentence_breakdown = item.sentence_breakdown or details["sentence_breakdown"]
        item.useful_pattern = item.useful_pattern or details["useful_pattern"]
    if items:
        await session.flush()
    return len(items)


def build_vocabulary_details(
    phrase: str,
    meaning_vi: str,
    example_sentence: str,
    writing_usage: str,
) -> dict[str, str]:
    if phrase.lower() in VOCAB_DETAIL_OVERRIDES:
        return VOCAB_DETAIL_OVERRIDES[phrase.lower()]

    sentence_breakdown = "\n".join(_build_sentence_breakdown(phrase, meaning_vi, example_sentence))
    return {
        "example_meaning_vi": (
            f"Câu ví dụ dùng cụm \"{phrase}\" với nghĩa \"{meaning_vi}\" "
            "để diễn đạt một ý rõ ràng, tự nhiên trong bài Writing."
        ),
        "sentence_breakdown": sentence_breakdown,
        "useful_pattern": _build_useful_pattern(example_sentence),
    }


def _build_sentence_breakdown(phrase: str, meaning_vi: str, example_sentence: str) -> list[str]:
    lower_sentence = example_sentence.lower()
    lower_phrase = phrase.lower()
    phrase_index = lower_sentence.find(lower_phrase)
    if phrase_index < 0:
        return [
            f"{phrase} = {meaning_vi}",
            "Main clause = phần nêu ý chính của câu",
            "Extra detail = phần giải thích tác động hoặc ví dụ cụ thể",
        ]

    before = example_sentence[:phrase_index].strip(" ,.")
    after = example_sentence[phrase_index + len(phrase) :].strip(" ,.")
    lines: list[str] = []
    if before:
        expanded_phrase = f"{before} {phrase}".strip()
        lines.append(f"{expanded_phrase} = {meaning_vi} trong ngữ cảnh cụ thể")
    else:
        lines.append(f"{phrase} = {meaning_vi}")
    if after:
        lines.append(f"{after} = phần nêu tác động, kết quả hoặc ý phát triển")
    lines.append("Full sentence = một câu mẫu có thể học cấu trúc để viết Task 1/Task 2")
    return lines


def _build_useful_pattern(example_sentence: str) -> str:
    lower = example_sentence.lower()
    if " helps " in lower or " help " in lower:
        return (
            "A supportive [noun] helps people + V...\n"
            "Ví dụ: A supportive teacher helps students improve their confidence."
        )
    if " should " in lower:
        return (
            "[Subject] should + V + object + to + V...\n"
            "Ví dụ: Schools should encourage students to develop practical skills."
        )
    if " can " in lower:
        return (
            "[Subject] can + V + object/result...\n"
            "Ví dụ: Online courses can help learners study more flexibly."
        )
    if " is " in lower or " are " in lower:
        return (
            "[Noun phrase] is/are + adjective/noun phrase + for + noun...\n"
            "Ví dụ: Critical thinking is important for academic success."
        )
    return (
        "[Subject] + clear verb + object/result...\n"
        "Ví dụ: Regular practice improves students' writing accuracy."
    )


async def get_topic_items(
    session: AsyncSession,
    topic: str,
    level: str | None = None,
    limit: int = 10,
) -> list[VocabularyItem]:
    stmt = select(VocabularyItem).where(VocabularyItem.topic == topic)
    if level:
        stmt = stmt.where(VocabularyItem.level.in_([level, "B1/B2"]))
    stmt = stmt.order_by(func.random()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def get_random_items(
    session: AsyncSession,
    limit: int = 10,
    exclude_id: int | None = None,
) -> list[VocabularyItem]:
    stmt = select(VocabularyItem)
    if exclude_id is not None:
        stmt = stmt.where(VocabularyItem.id != exclude_id)
    stmt = stmt.order_by(func.random()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


def format_vocab_items(items: list[VocabularyItem]) -> str:
    if not items:
        return "Chưa có dữ liệu từ vựng cho topic này."

    blocks = ["10 từ/cụm từ VSTEP hôm nay:"]
    for index, item in enumerate(items, start=1):
        blocks.append(
            "\n".join(
                [
                    f"{index}. Phrase: {item.phrase}",
                    f"Meaning: {item.meaning_vi}",
                    f"Example: {item.example_sentence}",
                    f"Collocation: {item.collocation}",
                    f"Writing usage: {item.writing_usage}",
                ]
            )
        )
    return "\n\n".join(blocks)


def format_vocab_messages(
    items: list[VocabularyItem],
    title: str = "📘 VSTEP Vocabulary",
    chunk_size: int = 5,
) -> list[str]:
    if not items:
        return ["Chưa có dữ liệu từ vựng cho topic này."]

    messages: list[str] = []
    for offset in range(0, len(items), chunk_size):
        chunk = items[offset : offset + chunk_size]
        blocks = [
            f"<b>{escape(title)}</b>",
            f"<i>Phần {offset // chunk_size + 1}</i>",
        ]
        for index, item in enumerate(chunk, start=offset + 1):
            blocks.append(format_vocab_item_html(item, index))
        messages.append("\n\n".join(blocks))
    return messages


def format_vocab_item_html(item: VocabularyItem, index: int) -> str:
    details = build_vocabulary_details(
        phrase=item.phrase,
        meaning_vi=item.meaning_vi,
        example_sentence=item.example_sentence,
        writing_usage=item.writing_usage,
    )
    example_meaning_vi = item.example_meaning_vi or details["example_meaning_vi"]
    sentence_breakdown = item.sentence_breakdown or details["sentence_breakdown"]
    useful_pattern = item.useful_pattern or details["useful_pattern"]

    breakdown_lines = [line.strip() for line in sentence_breakdown.splitlines() if line.strip()]
    pattern_lines = [line.strip() for line in useful_pattern.splitlines() if line.strip()]

    return "\n".join(
        [
            f"📘 <b>{index}. {escape(item.phrase)}</b>",
            f"🇻🇳 <b>Nghĩa:</b> {escape(item.meaning_vi)}",
            "",
            "🧩 <b>Example:</b>",
            f"<i>{escape(item.example_sentence)}</i>",
            "",
            "💬 <b>Nghĩa câu:</b>",
            escape(example_meaning_vi),
            "",
            "🔍 <b>Breakdown:</b>",
            *[f"• {escape(line)}" for line in breakdown_lines],
            "",
            "🧠 <b>Useful pattern:</b>",
            *[escape(line) for line in pattern_lines],
            "",
            f"🔗 <b>Collocation:</b> {escape(item.collocation)}",
            "",
            "✍️ <b>Writing usage:</b>",
            escape(item.writing_usage),
            "",
            "━━━━━━━━━━━━━━",
        ]
    )
