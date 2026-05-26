# VSTEP Telegram Bot

Telegram bot MVP hỗ trợ ôn VSTEP vocabulary và Writing. Bot dùng `aiogram` async, SQLAlchemy ORM, SQLite cho MVP và OpenAI API cho chấm/sửa Writing.

## Tính năng

- `/start`: onboarding mục tiêu B1/B2, số ngày còn lại, số phút học mỗi ngày.
- `/vocab`: học 10 cụm từ theo topic.
- `/quiz`: quiz vocabulary gồm multiple choice, fill in the blank, translate Vietnamese to English.
- `/meaning_quiz`: bot đưa từ/cụm tiếng Anh, bạn trả lời nghĩa tiếng Việt.
- `/word_quiz`: bot đưa nghĩa tiếng Việt, bạn viết lại từ/cụm tiếng Anh.
- `/task1`: random Writing Task 1 letter prompt.
- `/task2`: random Writing Task 2 essay prompt.
- `/check`: gửi bài Writing để AI chấm, sửa và lưu lỗi sai cá nhân.
- `/upgrade`: nâng cấp một câu đơn giản lên level B2.
- `/mistakes`: xem mistake book gần đây.
- `/review_mistakes`: tạo 5 bài tập dựa trên lỗi cũ.
- `/plan`: tạo kế hoạch ôn tập theo số ngày còn lại.
- `/reminder_on`, `/reminder_off`, `/set_reminder 20:00`: nhắc học hằng ngày.
- `/proactive_on`, `/proactive_off`: bật/tắt study coach chủ động.
- `/frequency low|normal|high`: chỉnh tần suất proactive messages.
- `/quiet`: tắt nhắc trong ngày hôm nay.
- Inline Mode: gõ `@bot_username vocab`, `@bot_username quiz`, `@bot_username task`, `@bot_username mistakes`, `@bot_username plan` trong Telegram để chọn nhanh tính năng.
- Natural chat: nhắn tự nhiên như `hôm nay học từ vựng đi`, `cho tao quiz đi`, `ra đề task 1`, `nâng cấp câu này: traveling is good`.

## Tạo bot Telegram

1. Mở Telegram và tìm `@BotFather`.
2. Gửi `/newbot`.
3. Đặt tên bot và username bot.
4. Copy token BotFather trả về vào biến `TELEGRAM_BOT_TOKEN`.

## Bật Inline Mode

Để gọi nhanh bot bằng `@bot_username`, bật Inline Mode trong BotFather:

1. Mở `@BotFather`.
2. Gửi `/setinline`.
3. Chọn bot của bạn.
4. Set placeholder:

```text
Search VSTEP features...
```

Sau khi bật, bạn có thể mở bất kỳ chat Telegram nào và gõ:

```text
@bot_username vocab
@bot_username quiz
@bot_username task
@bot_username task1
@bot_username task2
@bot_username check
@bot_username upgrade
@bot_username mistakes
@bot_username plan
```

Nếu query rỗng, ví dụ chỉ gõ `@bot_username`, bot sẽ hiện menu mặc định gồm Vocabulary, Quiz, Task 1, Task 2, Check Writing, Upgrade Sentence, Mistake Book, Study Plan.

Lưu ý: Inline results có thể insert nội dung vào chat. Với các flow cần lưu state như `/check`, `/upgrade`, `/quiz`, nên bấm nút trong chat riêng với bot để bot nhận câu trả lời và lưu tiến độ chính xác.

## Hiện danh sách khi gõ `/`

Bot tự đăng ký command menu khi startup bằng Bot API `setMyCommands`. Sau khi chạy bot, mở chat với bot và gõ `/`, Telegram sẽ hiện danh sách tính năng như:

```text
/start - Bắt đầu và thiết lập mục tiêu học
/menu - Mở menu chính của VSTEP coach
/vocab - Học từ vựng VSTEP theo topic
/quiz - Làm quiz từ vựng nhanh
/meaning_quiz - Bot hỏi nghĩa tiếng Việt của từ/cụm
/word_quiz - Bot cho nghĩa, bạn viết từ/cụm tiếng Anh
/task1 - Nhận đề Writing Task 1
/task2 - Nhận đề Writing Task 2
/check - Chấm và sửa bài Writing
/upgrade - Nâng cấp câu tiếng Anh lên B2
/mistakes - Xem lỗi sai cá nhân gần đây
/review_mistakes - Ôn lại lỗi sai bằng bài tập
/plan - Tạo kế hoạch ôn tập VSTEP
/proactive_on - Bật nhắc học chủ động
/proactive_off - Tắt nhắc học chủ động
/set_reminder - Đặt giờ nhắc học, ví dụ 20:00
/frequency - Đặt tần suất nhắc: low/normal/high
/quiet - Tắt nhắc học trong hôm nay
```

Nếu Telegram chưa hiện ngay, restart app Telegram hoặc đợi vài phút để client refresh cache.

Bạn cũng có thể set thủ công trong BotFather:

1. Gửi `/setcommands`.
2. Chọn bot.
3. Dán danh sách command theo format:

```text
start - Bắt đầu và thiết lập mục tiêu học
menu - Mở menu chính của VSTEP coach
vocab - Học từ vựng VSTEP theo topic
quiz - Làm quiz từ vựng nhanh
meaning_quiz - Bot hỏi nghĩa tiếng Việt của từ/cụm
word_quiz - Bot cho nghĩa, bạn viết từ/cụm tiếng Anh
task1 - Nhận đề Writing Task 1
task2 - Nhận đề Writing Task 2
check - Chấm và sửa bài Writing
upgrade - Nâng cấp câu tiếng Anh lên B2
mistakes - Xem lỗi sai cá nhân gần đây
review_mistakes - Ôn lại lỗi sai bằng bài tập
plan - Tạo kế hoạch ôn tập VSTEP
proactive_on - Bật nhắc học chủ động
proactive_off - Tắt nhắc học chủ động
set_reminder - Đặt giờ nhắc học, ví dụ 20:00
frequency - Đặt tần suất nhắc: low/normal/high
quiet - Tắt nhắc học trong hôm nay
```

## Chạy local

```bash
cd vstep_telegram_bot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data
```

Sửa `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite+aiosqlite:///./data/vstep_bot.db
BOT_TIMEZONE=Asia/Ho_Chi_Minh
```

Chạy bot:

```bash
python -m app.main
```

Lần chạy đầu tiên sẽ tự tạo bảng và seed 100 vocabulary phrases.

Khi nâng cấp từ bản cũ, app sẽ tự thêm các cột vocabulary mới nếu thiếu:

- `example_meaning_vi`
- `sentence_breakdown`
- `useful_pattern`

App cũng tự thêm các cột proactive mới vào bảng `users` nếu thiếu:

- `proactive_enabled`
- `last_interaction_at`
- `last_proactive_sent_at`
- `proactive_frequency`
- `timezone`
- `proactive_quiet_until`
- các field đếm/chặn gửi lặp trong ngày

Và tạo bảng `conversation_states` để nhớ flow ngắn hạn như đang chờ bài Writing, chờ câu cần nâng cấp, chờ câu cần giải thích.

## Proactive Study Coach

Bot có thể tự gửi tin nhắn học nhẹ nếu user bật proactive:

```bash
/proactive_on
/set_reminder 20:00
/frequency normal
```

Tắt:

```bash
/proactive_off
```

Tắt nhắc trong ngày:

```bash
/quiet
```

Các loại tin nhắn chủ động:

- Daily reminder đúng giờ `reminder_time`.
- Hourly vocab: mỗi 1 tiếng trong khung 07:00-23:00 gửi 1-3 cụm theo một topic, dùng đúng format vocabulary hiện tại và kèm một writing bite ngắn về Task 1 letter hoặc Task 2 essay.
- Check-in nếu user không tương tác 24h, 48h, 72h.
- Morning vocabulary lúc 08:00 với frequency `normal` hoặc `high`.
- Night review lúc 21:30.
- Mistake review nếu user có lỗi trong mistake book.

Chống spam:

- Không gửi nếu `proactive_enabled=false`.
- Không gửi quá 3 proactive messages/ngày.
- Không gửi nếu user vừa tương tác trong 30 phút.
- Nút `❌ Để sau` sẽ snooze vài giờ.
- Frequency `low` nhắc ít hơn.
- Hourly vocab không bị giới hạn 3 tin/ngày; nó dùng bộ đếm riêng để có thể gửi đều mỗi giờ. `/quiet` và nút `❌ Để sau` vẫn chặn hourly vocab.

Scheduler nằm ở `app/scheduler.py`, dùng APScheduler với 4 job:

- every minute: check daily reminders theo `reminder_time`.
- every hour: gửi 1-3 vocabulary phrases theo topic + một writing bite ngắn nếu đủ điều kiện.
- every 3 hours: inactive user check-ins.
- 08:00: morning vocabulary.
- 21:30: night review.

## Natural Chat

Ngoài slash commands và inline mode, bot hiểu tin nhắn thường:

```text
hôm nay học từ vựng đi
cho tao quiz đi
hỏi nghĩa của từ đi
cho nghĩa rồi tôi viết từ
ra đề task 1 cho tôi
ra đề task 2
chấm bài này giúp tôi: ...
nâng cấp câu này: traveling is good
câu này nghĩa là gì: A supportive learning environment helps students stay motivated
giải thích cụm broaden one's horizons
cho tôi mẫu mở bài task 2
tôi lười quá
mai tôi thi rồi
tôi còn 2 ngày nữa thi
```

Intent detection nằm ở `app/services/intent_service.py`: rule-based trước, fallback OpenAI nếu chưa chắc. Nếu confidence thấp, bot hỏi lại bằng menu ngắn thay vì đoán bừa.

## Chạy bằng Docker

```bash
cd vstep_telegram_bot
cp .env.example .env
mkdir -p data
docker compose up --build -d
```

Xem log:

```bash
docker compose logs -f vstep-bot
```

## Cách thêm vocabulary mới

Mở `app/seed/vocabulary_seed.py`, thêm tuple mới vào đúng topic:

```python
(
    "new phrase",
    "nghĩa tiếng Việt",
    "Example sentence with the new phrase.",
    "common collocation",
    "Cách dùng trong Writing.",
    "B2",
)
```

Các phần `example_meaning_vi`, `sentence_breakdown`, `useful_pattern` sẽ được service tự tạo mặc định nếu seed item chưa khai báo. Nếu muốn nội dung tự nhiên hơn cho một cụm cụ thể, thêm override trong `app/services/vocab_service.py`.

Seed hiện chỉ tự chạy khi bảng `vocabulary_items` trống. Nếu database đã có dữ liệu cũ, app sẽ backfill các field giải thích còn thiếu khi startup.

## Cách test Inline Mode

1. Chạy bot bằng local hoặc Docker.
2. Vào `@BotFather` và bật `/setinline`.
3. Mở một chat Telegram bất kỳ.
4. Gõ `@bot_username vocab`.
5. Chọn một result như `Học 10 từ vựng hôm nay` hoặc `Học từ vựng Education`.
6. Gõ thử `@bot_username quiz`, `@bot_username task`, `@bot_username mistakes`, `@bot_username plan`.

## Cách chỉnh prompt chấm bài

Prompt chính nằm ở `app/prompts/check_writing_prompt.py`.

Bạn có thể chỉnh:

- tiêu chí chấm VSTEP;
- độ dài feedback;
- mức độ học thuật của bản rewrite;
- JSON metadata để backend parse `estimated_level`, `estimated_score`, `mistakes`, `improved_version`.

Lưu ý: nếu đổi schema JSON, cập nhật parser trong `app/services/writing_service.py` và logic lưu lỗi ở `app/services/mistake_service.py`.

## Deploy lên VPS

1. Cài Docker và Docker Compose plugin trên VPS.
2. Clone hoặc copy thư mục `vstep_telegram_bot` lên VPS.
3. Tạo `.env` thật với token Telegram và OpenAI API key.
4. Chạy:

```bash
docker compose up --build -d
```

5. Kiểm tra log:

```bash
docker compose logs -f vstep-bot
```

Bot dùng Telegram long polling nên không cần domain hoặc webhook cho MVP. Nếu sau này cần scale nhiều instance, nên chuyển sang webhook và PostgreSQL.

## Đổi sang PostgreSQL sau này

Đổi `DATABASE_URL`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/vstep
```

Models đang dùng SQLAlchemy ORM nên có thể bổ sung Alembic migrations khi bước sang production.
# vstep-bot
