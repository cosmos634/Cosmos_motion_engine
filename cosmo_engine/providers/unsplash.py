"""Unsplash image search provider (images only)."""
import os
from urllib.parse import urlencode

from ..asset_models import Asset
from .base import BaseProvider


class UnsplashProvider(BaseProvider):
    name = "unsplash"

    def __init__(self, api_key: str | None = None, timeout: int = 20):
        super().__init__(api_key if api_key is not None else os.getenv("UNSPLASH_ACCESS_KEY", ""), timeout)

    def search(self, query: str, media_type: str = "image", limit: int = 10) -> list[Asset]:
        limit = self.positive_limit(limit, 30)
        if media_type != "image":
            raise ValueError("Unsplash provider supports images only")
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        endpoint = "https://api.unsplash.com/search/photos?" + urlencode({"query": query.strip(), "per_page": limit})
        data = self.get_json(endpoint, {"Authorization": f"Client-ID {self.api_key}"})
        items = []
        for item in data.get("results", []):
            urls = item.get("urls", {})
            url = urls.get("regular") or urls.get("full")
            if not url:
                continue
            user = item.get("user", {})
            links = item.get("links", {})
            user_links = user.get("links", {})
            items.append(Asset(
                id=str(item.get("id", "")), provider=self.name, media_type="image",
                title=item.get("alt_description") or item.get("description") or "Unsplash photo",
                url=url, source_page=links.get("html", ""), author=user.get("name", ""),
                author_url=user_links.get("html", ""), thumbnail_url=urls.get("thumb", ""),
                license="Unsplash License", width=item.get("width", 0), height=item.get("height", 0),
            ))
        return items
