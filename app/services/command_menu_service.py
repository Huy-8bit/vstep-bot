import logging

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonCommands

logger = logging.getLogger(__name__)


BOT_COMMANDS = [
    BotCommand(command="start", description="Bắt đầu và thiết lập mục tiêu học"),
    BotCommand(command="menu", description="Mở menu chính của VSTEP coach"),
    BotCommand(command="vocab", description="Học từ vựng VSTEP theo topic"),
    BotCommand(command="quiz", description="Làm quiz từ vựng nhanh"),
    BotCommand(command="meaning_quiz", description="Bot hỏi nghĩa tiếng Việt của từ/cụm"),
    BotCommand(command="word_quiz", description="Bot cho nghĩa, bạn viết từ/cụm tiếng Anh"),
    BotCommand(command="task1", description="Nhận đề Writing Task 1"),
    BotCommand(command="task2", description="Nhận đề Writing Task 2"),
    BotCommand(command="check", description="Chấm và sửa bài Writing"),
    BotCommand(command="upgrade", description="Nâng cấp câu tiếng Anh lên B2"),
    BotCommand(command="mistakes", description="Xem lỗi sai cá nhân gần đây"),
    BotCommand(command="review_mistakes", description="Ôn lại lỗi sai bằng bài tập"),
    BotCommand(command="plan", description="Tạo kế hoạch ôn tập VSTEP"),
    BotCommand(command="proactive_on", description="Bật nhắc học chủ động"),
    BotCommand(command="proactive_off", description="Tắt nhắc học chủ động"),
    BotCommand(command="set_reminder", description="Đặt giờ nhắc học, ví dụ 20:00"),
    BotCommand(command="frequency", description="Đặt tần suất nhắc: low/normal/high"),
    BotCommand(command="quiet", description="Tắt nhắc học trong hôm nay"),
]


async def setup_bot_command_menu(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    logger.info("Telegram command menu configured with %s commands", len(BOT_COMMANDS))
