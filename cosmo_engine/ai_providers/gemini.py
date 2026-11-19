"""Google Gemini generateContent adapter."""

import os
from urllib.parse import quote

from .base import AIProviderError, BaseAIProvider


class GeminiProvider(BaseAIProvider):
    name = "gemini"
    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key=None, model=None, timeout=45):
        super().__init__(
            api_key if api_key is not None else os.getenv("GEMINI_API_KEY", ""),
            timeout,
        )
        self.model = model or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)

    def generate_text(self, system_prompt, user_prompt):
        model = quote(self.model, safe="-.")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={quote(self.api_key, safe='')}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7,
                "maxOutputTokens": 8192,
            },
        }
        data = self.post_json(url, payload)
        try:
            parts = data["candidates"][0]["content"]["parts"]
            result = "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("gemini: response did not contain generated text") from exc
        if not result.strip():
            raise AIProviderError("gemini: generated text was empty")
        return result
