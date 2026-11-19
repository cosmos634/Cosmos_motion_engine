"""Shared standard-library HTTP support for AI providers."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AIProviderError(RuntimeError):
    """Raised when an AI provider cannot return a usable response."""


class BaseAIProvider:
    name = "base"

    def __init__(self, api_key, timeout=45):
        if not api_key:
            raise AIProviderError(f"{self.name} API key is missing")
        self.api_key = api_key
        self.timeout = timeout

    def post_json(self, url, payload, headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers = {
            "User-Agent": "CosmoMotionEngine/0.3",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        request_headers.update(headers or {})
        request = Request(url, data=body, headers=request_headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise AIProviderError(f"{self.name}: response exceeded 2 MB")
            try:
                return json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise AIProviderError(f"{self.name}: provider returned invalid JSON") from exc
        except HTTPError as exc:
            if exc.code == 401 or exc.code == 403:
                detail = "API key rejected or access denied"
            elif exc.code == 429:
                detail = "rate limit reached"
            elif exc.code >= 500:
                detail = "provider temporarily unavailable"
            else:
                detail = f"HTTP {exc.code}"
            raise AIProviderError(f"{self.name}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise AIProviderError(f"{self.name}: network request failed") from exc

    def generate_text(self, system_prompt, user_prompt):
        raise NotImplementedError
