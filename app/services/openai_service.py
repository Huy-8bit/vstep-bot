import logging

from openai import APIError, APITimeoutError, AsyncOpenAI, OpenAIError, RateLimitError

from app.config import settings
from app.prompts.check_writing_prompt import build_check_writing_messages
from app.prompts.natural_chat_prompt import build_natural_chat_messages
from app.prompts.upgrade_sentence_prompt import build_upgrade_sentence_messages

logger = logging.getLogger(__name__)


class OpenAIServiceError(RuntimeError):
    pass


class OpenAIService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def _chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        if self._client is None:
            raise OpenAIServiceError("OPENAI_API_KEY is not configured.")

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=temperature,
                timeout=60,
            )
        except (APITimeoutError, RateLimitError, APIError, OpenAIError) as exc:
            logger.exception("OpenAI API request failed")
            raise OpenAIServiceError("OpenAI API đang lỗi hoặc quá tải. Vui lòng thử lại sau.") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise OpenAIServiceError("OpenAI API không trả về nội dung.")
        return content.strip()

    async def check_writing(self, task_type: str, prompt: str, essay: str) -> str:
        messages = build_check_writing_messages(task_type=task_type, prompt=prompt, essay=essay)
        return await self._chat(messages, temperature=0.2)

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        return await self._chat(messages, temperature=temperature)

    async def natural_chat(self, text: str) -> str:
        return await self._chat(build_natural_chat_messages(text), temperature=0.4)

    async def upgrade_sentence(self, sentence: str) -> str:
        messages = build_upgrade_sentence_messages(sentence)
        return await self._chat(messages, temperature=0.35)

    async def generate_mistake_review(self, mistakes_text: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You create short VSTEP practice exercises from a learner's mistake book. "
                    "Write in Vietnamese. Create exactly 5 numbered exercises. "
                    "Each exercise should ask the learner to rewrite, fill a blank, or choose the better sentence. "
                    "Do not reveal answers immediately; add a short answer key at the end."
                ),
            },
            {"role": "user", "content": mistakes_text},
        ]
        return await self._chat(messages, temperature=0.3)


openai_service = OpenAIService()
