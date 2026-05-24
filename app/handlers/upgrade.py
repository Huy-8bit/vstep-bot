from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.handlers.utils import send_long_message
from app.services.openai_service import OpenAIServiceError, openai_service

router = Router(name="upgrade")


class UpgradeState(StatesGroup):
    waiting_sentence = State()


async def _ask_sentence(message: Message, state: FSMContext) -> None:
    await state.set_state(UpgradeState.waiting_sentence)
    await message.answer("Gửi một câu tiếng Anh đơn giản. Mình sẽ nâng cấp lên level B2.")


@router.message(Command("upgrade"))
async def upgrade_command(message: Message, state: FSMContext) -> None:
    await _ask_sentence(message, state)


@router.callback_query(F.data.in_({"menu:upgrade", "upgrade_sentence"}))
async def upgrade_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer("Mở chat riêng với bot và dùng /upgrade để nâng cấp câu.", show_alert=True)
        return
    await callback.answer()
    await _ask_sentence(callback.message, state)


@router.message(UpgradeState.waiting_sentence)
async def receive_sentence(message: Message, state: FSMContext) -> None:
    sentence = (message.text or "").strip()
    if sentence.startswith("/"):
        await state.clear()
        await message.answer("Mình đã hủy flow nâng cấp câu. Gõ lại command bạn muốn dùng nhé.")
        return
    if len(sentence.split()) > 80:
        await message.answer("Bạn gửi một câu ngắn hơn nhé. Tính năng này dùng để nâng cấp từng câu.")
        return

    await message.answer("Mình đang nâng cấp câu...")
    try:
        result = await openai_service.upgrade_sentence(sentence)
    except OpenAIServiceError as exc:
        await message.answer(f"Không nâng cấp được lúc này: {exc}")
        return

    await state.clear()
    await send_long_message(message, result)
