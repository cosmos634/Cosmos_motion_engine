"""Groq OpenAI-compatible chat-completions adapter."""

import os

from .base import AIProviderError, BaseAIProvider


class GroqProvider(BaseAIProvider):
    name = "groq"
    DEFAULT_MODEL = "openai/gpt-oss-120b"
    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key=None, model=None, timeout=45):
        super().__init__(
            api_key if api_key is not None else os.getenv("GROQ_API_KEY", ""),
            timeout,
        )
        self.model = model or os.getenv("GROQ_MODEL", self.DEFAULT_MODEL)

    def generate_text(self, system_prompt, user_prompt):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
        }
        data = self.post_json(
            self.ENDPOINT,
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
        )
        try:
            result = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("groq: response did not contain generated text") from exc
        if not isinstance(result, str) or not result.strip():
            raise AIProviderError("groq: generated text was empty")
        return result
