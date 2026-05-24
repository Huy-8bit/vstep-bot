import asyncio
import logging

from app.bot import create_bot, create_dispatcher
from app.database import init_db, session_scope
from app.scheduler import create_scheduler
from app.seed.vocabulary_seed import VOCABULARY_SEED
from app.services.command_menu_service import setup_bot_command_menu
from app.services.vocab_service import seed_vocabulary

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    await init_db()
    async with session_scope() as session:
        seeded = await seed_vocabulary(session)
        logger.info("Vocabulary seed complete: %s new rows, %s rows available", seeded, len(VOCABULARY_SEED))

    bot = create_bot()
    dp = create_dispatcher()
    scheduler = create_scheduler(bot)
    scheduler.start()
    logger.info("Proactive scheduler started")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await setup_bot_command_menu(bot)
        logger.info("Bot polling started")
        await dp.start_polling(bot, scheduler=scheduler)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
