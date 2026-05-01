import json
import os
from collections.abc import AsyncGenerator

from google import genai

from ..base import BaseLLMAdapter
from ..config import get_model
from ..types import LLMProvider, LLMResponse


class GeminiAdapter(BaseLLMAdapter):
    provider = LLMProvider.GEMINI

    def __init__(self, model: str | None = None):
        self._api_key = os.getenv("GEMINI_API_KEY", "")
        self._model = model or get_model(LLMProvider.GEMINI)
        self._client = genai.Client(api_key=self._api_key) if self._api_key else None

    def is_available(self) -> bool:
        return bool(self._api_key and self._client)

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        contents = self._convert_messages(messages)
        response = await self._client.aio.models.generate_content(
            model=kwargs.get("model", self._model),
            contents=contents,
            config=genai.types.GenerateContentConfig(
                temperature=kwargs.get("temperature", 0.7),
                max_output_tokens=kwargs.get("max_tokens", 4096),
            ),
        )
        return LLMResponse(
            content=response.text or "",
            provider=self.provider,
            model=self._model,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            },
        )

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        contents = self._convert_messages(messages)
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=kwargs.get("model", self._model),
            contents=contents,
            config=genai.types.GenerateContentConfig(
                temperature=kwargs.get("temperature", 0.7),
                max_output_tokens=kwargs.get("max_tokens", 4096),
            ),
        ):
            if chunk.text:
                yield chunk.text

    async def structured_output(self, messages: list[dict], schema: type, **kwargs) -> dict:
        messages_with_format = [
            *messages,
            {"role": "user", "content": f"Respond ONLY with valid JSON matching: {json.dumps(schema.model_json_schema() if hasattr(schema, 'model_json_schema') else {})}"},
        ]
        response = await self.complete(messages_with_format, **kwargs)
        return json.loads(response.content)

    @staticmethod
    def _convert_messages(messages: list[dict]) -> list[genai.types.Content]:
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(genai.types.Content(role=role, parts=[genai.types.Part(text=msg["content"])]))
        return contents
