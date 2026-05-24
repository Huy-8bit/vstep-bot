from aiogram import Dispatcher

from app.handlers import inline, mistakes, natural_chat, plan, proactive, quiz, reminder, start, upgrade, vocab, writing


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(inline.router)
    dp.include_router(vocab.router)
    dp.include_router(quiz.router)
    dp.include_router(writing.router)
    dp.include_router(upgrade.router)
    dp.include_router(mistakes.router)
    dp.include_router(plan.router)
    dp.include_router(reminder.router)
    dp.include_router(proactive.router)
    dp.include_router(natural_chat.router)
