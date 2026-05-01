import json
import os
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from ..base import BaseLLMAdapter
from ..config import get_model
from ..types import LLMProvider, LLMResponse


class OpenRouterAdapter(BaseLLMAdapter):
    """OpenRouter adapter biased toward `:free` model variants by default.

    Free models route to community providers and are subject to per-account
    rate limits. Override per-call with `kwargs={"model": "..."}` to use a
    paid model when you have credits.
    """

    provider = LLMProvider.OPENROUTER

    def __init__(self, model: str | None = None):
        self._api_key = os.getenv("OPENROUTER_API_KEY", "")
        self._model = model or get_model(LLMProvider.OPENROUTER)
        self._client = (
            AsyncOpenAI(
                api_key=self._api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://agentos.dev"),
                    "X-Title": os.getenv("OPENROUTER_APP_NAME", "AgentOS"),
                },
            )
            if self._api_key
            else None
        )

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
            model=response.model or self._model,
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
            {"role": "user", "content": f"Respond ONLY with valid JSON matching: {json.dumps(schema.model_json_schema() if hasattr(schema, 'model_json_schema') else {})}"},
        ]
        response = await self.complete(messages_with_format, **kwargs)
        return json.loads(response.content)
