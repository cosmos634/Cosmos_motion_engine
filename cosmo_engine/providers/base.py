"""Small standard-library HTTP helpers for asset providers."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    """Raised when a provider request cannot be completed."""


class BaseProvider:
    name = "base"

    def __init__(self, api_key: str, timeout: int = 20):
        if not api_key:
            raise ProviderError(f"{self.name} API key is missing")
        self.api_key = api_key
        self.timeout = timeout

    def get_json(self, url: str, headers: dict | None = None) -> dict:
        request_headers = {"User-Agent": "CosmoMotionEngine/0.2", "Accept": "application/json"}
        request_headers.update(headers or {})
        request = Request(url, headers=request_headers, method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read(5 * 1024 * 1024 + 1)
                if len(payload) > 5 * 1024 * 1024:
                    raise ProviderError("Provider response exceeded 5 MB")
                return json.loads(payload.decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 401:
                detail = "API key was rejected"
            elif exc.code == 429:
                detail = "Provider rate limit reached"
            else:
                detail = f"HTTP {exc.code}"
            raise ProviderError(f"{self.name}: {detail}") from exc
        except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError(f"{self.name}: request failed: {exc}") from exc

    @staticmethod
    def positive_limit(value: int, maximum: int = 30) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            raise ValueError(f"limit must be between 1 and {maximum}")
        return value
