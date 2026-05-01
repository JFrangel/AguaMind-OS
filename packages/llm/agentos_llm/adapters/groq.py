import json
import os
from collections.abc import AsyncGenerator

from groq import AsyncGroq

from ..base import BaseLLMAdapter
from ..config import get_model
from ..types import LLMProvider, LLMResponse


class GroqAdapter(BaseLLMAdapter):
    provider = LLMProvider.GROQ

    def __init__(self, model: str | None = None):
        self._api_key = os.getenv("GROQ_API_KEY", "")
        self._model = model or get_model(LLMProvider.GROQ)
        self._client = AsyncGroq(api_key=self._api_key) if self._api_key else None

    def is_available(self) -> bool:
        return bool(self._api_key and self._client)

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            provider=self.provider,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        stream = await self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def structured_output(self, messages: list[dict], schema: type, **kwargs) -> dict:
        messages_with_format = [
            *messages,
            {"role": "user", "content": f"Respond ONLY with valid JSON matching this schema: {json.dumps(schema.model_json_schema() if hasattr(schema, 'model_json_schema') else {})}"},
        ]
        response = await self.complete(messages_with_format, **kwargs)
        return json.loads(response.content)
