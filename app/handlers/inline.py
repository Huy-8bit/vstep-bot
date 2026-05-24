from html import escape

from aiogram import Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from app.services.writing_service import format_task, random_task1, random_task2

router = Router(name="inline")


def _action_keyboard(callback_data: str, text: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback_data)]]
    )


def _article(
    result_id: str,
    title: str,
    description: str,
    message_text: str,
    callback_data: str,
    button_text: str,
) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=description,
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            parse_mode="HTML",
        ),
        reply_markup=_action_keyboard(callback_data, button_text),
    )


def _action_text(title: str, command: str, detail: str) -> str:
    return (
        f"<b>{escape(title)}</b>\n\n"
        f"{escape(detail)}\n\n"
        f"Trong chat riêng với bot, bạn cũng có thể dùng: <code>{escape(command)}</code>"
    )


def _default_results() -> list[InlineQueryResultArticle]:
    return [
        _article(
            "default:vocab",
            "📘 Vocabulary",
            "Học 10 cụm từ VSTEP hôm nay",
            _action_text("📘 Vocabulary", "/vocab", "Bấm nút để nhận 10 từ/cụm từ VSTEP hôm nay."),
            "vocab_daily",
            "📘 Học ngay",
        ),
        _article(
            "default:quiz",
            "🧠 Quiz",
            "Làm quiz từ vựng nhanh",
            _action_text("🧠 Quiz", "/quiz", "Bấm nút để nhận một câu quiz vocabulary."),
            "quiz_start",
            "🧠 Làm quiz",
        ),
        _article(
            "default:task1",
            "✍️ Writing Task 1",
            "Nhận đề thư VSTEP Task 1",
            _task_text("✍️ Random Writing Task 1", format_task(random_task1())),
            "task1_random",
            "✍️ Đề Task 1 khác",
        ),
        _article(
            "default:task2",
            "📝 Writing Task 2",
            "Nhận đề essay VSTEP Task 2",
            _task_text("📝 Random Writing Task 2", format_task(random_task2())),
            "task2_random",
            "📝 Đề Task 2 khác",
        ),
        _article(
            "default:check",
            "🔍 Check Writing",
            "Chấm và sửa bài Writing bằng AI",
            _action_text("🔍 Check Writing", "/check", "Bấm nút hoặc dùng /check để gửi bài Writing cần chấm."),
            "check_writing",
            "🔍 Chấm bài",
        ),
        _article(
            "default:upgrade",
            "🚀 Upgrade Sentence",
            "Nâng cấp câu đơn giản lên level B2",
            _action_text("🚀 Upgrade Sentence", "/upgrade", "Bấm nút hoặc dùng /upgrade để gửi một câu cần nâng cấp."),
            "upgrade_sentence",
            "🚀 Nâng cấp câu",
        ),
        _article(
            "default:mistakes",
            "❌ Mistake Book",
            "Xem lỗi sai cá nhân gần đây",
            _action_text("❌ Mistake Book", "/mistakes", "Bấm nút để xem các lỗi sai đã lưu gần đây."),
            "mistakes_recent",
            "❌ Xem lỗi sai",
        ),
        _article(
            "default:plan",
            "📅 Study Plan",
            "Tạo kế hoạch ôn tập theo số ngày còn lại",
            _action_text("📅 Study Plan", "/plan", "Bấm nút để tạo kế hoạch ôn tập VSTEP cá nhân."),
            "study_plan",
            "📅 Tạo plan",
        ),
    ]


def _task_text(title: str, task_text: str) -> str:
    return f"<b>{escape(title)}</b>\n\n{escape(task_text)}"


def _vocab_results() -> list[InlineQueryResultArticle]:
    topic_results = [
        _article(
            f"vocab:{topic.lower()}",
            f"📘 Học từ vựng {topic}",
            f"Nhận 10 cụm từ topic {topic}",
            _action_text(
                f"📘 Vocabulary: {topic}",
                "/vocab",
                f"Bấm nút để nhận 10 từ/cụm từ VSTEP topic {topic}.",
            ),
            f"vocab:{topic}",
            f"📘 Gửi {topic}",
        )
        for topic in ["Education", "Technology", "Environment", "Health"]
    ]
    return [
        _article(
            "vocab:daily",
            "📘 Học 10 từ vựng hôm nay",
            "Random 10 cụm từ VSTEP",
            _action_text("📘 10 từ vựng hôm nay", "/vocab", "Bấm nút để nhận 10 từ/cụm từ VSTEP hôm nay."),
            "vocab_daily",
            "📘 Học 10 từ",
        ),
        *topic_results,
    ]


def _quiz_results() -> list[InlineQueryResultArticle]:
    return [
        _article(
            "quiz:quick",
            "🧠 Quiz từ vựng nhanh",
            "Random quiz vocabulary",
            _action_text("🧠 Quiz từ vựng nhanh", "/quiz", "Bấm nút để nhận một câu quiz random."),
            "quiz_start",
            "🧠 Start quiz",
        ),
        _article(
            "quiz:fill",
            "🧩 Fill in the blank",
            "Điền cụm từ còn thiếu",
            _action_text("🧩 Fill in the blank", "/quiz", "Bấm nút để nhận một câu fill in the blank."),
            "quiz_fill_blank",
            "🧩 Làm dạng này",
        ),
        _article(
            "quiz:translate",
            "🇻🇳 Translate Vietnamese to English",
            "Dịch nghĩa tiếng Việt sang cụm từ tiếng Anh",
            _action_text(
                "🇻🇳 Translate Vietnamese to English",
                "/quiz",
                "Bấm nút để nhận một câu dịch từ tiếng Việt sang cụm từ tiếng Anh.",
            ),
            "quiz_translate",
            "🇻🇳 Làm dạng này",
        ),
        _article(
            "quiz:meaning",
            "📘 Hỏi nghĩa của từ/cụm",
            "Bot đưa phrase tiếng Anh, bạn trả lời nghĩa tiếng Việt",
            _action_text("📘 Hỏi nghĩa của từ/cụm", "/meaning_quiz", "Bấm nút để nhận một câu hỏi nghĩa từ."),
            "quiz_meaning",
            "📘 Hỏi nghĩa",
        ),
        _article(
            "quiz:write-word",
            "✍️ Cho nghĩa, viết từ",
            "Bot đưa nghĩa tiếng Việt, bạn viết phrase tiếng Anh",
            _action_text("✍️ Cho nghĩa, viết từ", "/word_quiz", "Bấm nút để luyện nhớ lại phrase tiếng Anh."),
            "quiz_write_word",
            "✍️ Viết từ",
        ),
    ]


def _writing_results() -> list[InlineQueryResultArticle]:
    return [
        _article(
            "writing:task1",
            "✍️ Random Writing Task 1",
            "Request, complaint, apology, invitation...",
            _task_text("✍️ Random Writing Task 1", format_task(random_task1())),
            "task1_random",
            "✍️ Đề Task 1 khác",
        ),
        _article(
            "writing:task2",
            "📝 Random Writing Task 2",
            "Opinion, advantages/disadvantages, problem-solution...",
            _task_text("📝 Random Writing Task 2", format_task(random_task2())),
            "task2_random",
            "📝 Đề Task 2 khác",
        ),
        _article(
            "writing:check",
            "🔍 Check my writing",
            "Gửi bài để AI chấm/sửa",
            _action_text("🔍 Check my writing", "/check", "Bấm nút hoặc dùng /check trong chat riêng với bot."),
            "check_writing",
            "🔍 Check Writing",
        ),
        _article(
            "writing:upgrade",
            "🚀 Upgrade my sentence",
            "Nâng cấp câu lên B2",
            _action_text("🚀 Upgrade my sentence", "/upgrade", "Bấm nút hoặc dùng /upgrade trong chat riêng với bot."),
            "upgrade_sentence",
            "🚀 Upgrade",
        ),
    ]


def _mistake_results() -> list[InlineQueryResultArticle]:
    return [
        _article(
            "mistakes:recent",
            "❌ Xem lỗi sai gần đây",
            "Mở mistake book cá nhân",
            _action_text("❌ Xem lỗi sai gần đây", "/mistakes", "Bấm nút để xem các lỗi sai gần đây."),
            "mistakes_recent",
            "❌ Xem lỗi sai",
        ),
        _article(
            "mistakes:review",
            "🔁 Ôn lại lỗi sai",
            "Review mistake book",
            _action_text("🔁 Ôn lại lỗi sai", "/review_mistakes", "Bấm nút để tạo bài review từ lỗi sai cũ."),
            "mistakes_review",
            "🔁 Review",
        ),
        _article(
            "mistakes:exercises",
            "🧪 Tạo bài tập từ lỗi sai",
            "5 bài tập cá nhân hóa",
            _action_text(
                "🧪 Tạo bài tập từ lỗi sai",
                "/review_mistakes",
                "Bấm nút để tạo 5 bài tập dựa trên mistake book.",
            ),
            "mistakes_exercises",
            "🧪 Tạo bài tập",
        ),
    ]


@router.inline_query()
async def inline_features(inline_query: InlineQuery) -> None:
    query = (inline_query.query or "").strip().lower()

    if not query:
        results = _default_results()
    elif query.startswith("vocab"):
        results = _vocab_results()
    elif query.startswith("quiz"):
        results = _quiz_results()
    elif query.startswith(("writing", "task")):
        results = _writing_results()
    elif query.startswith("check"):
        results = [_writing_results()[2]]
    elif query.startswith("upgrade"):
        results = [_writing_results()[3]]
    elif query.startswith("mistakes"):
        results = _mistake_results()
    elif query.startswith("plan"):
        results = [_default_results()[-1]]
    else:
        results = _default_results()

    await inline_query.answer(results=results, cache_time=1, is_personal=True)
