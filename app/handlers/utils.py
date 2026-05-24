from aiogram.types import Message

MAX_MESSAGE_LENGTH = 3900


async def send_long_message(message: Message, text: str, parse_mode: str | None = None) -> None:
    if len(text) <= MAX_MESSAGE_LENGTH:
        await message.answer(text, parse_mode=parse_mode)
        return

    chunk = []
    current_length = 0
    for paragraph in text.split("\n\n"):
        next_length = current_length + len(paragraph) + 2
        if chunk and next_length > MAX_MESSAGE_LENGTH:
            await message.answer("\n\n".join(chunk), parse_mode=parse_mode)
            chunk = [paragraph]
            current_length = len(paragraph)
        else:
            chunk.append(paragraph)
            current_length = next_length
    if chunk:
        await message.answer("\n\n".join(chunk), parse_mode=parse_mode)
