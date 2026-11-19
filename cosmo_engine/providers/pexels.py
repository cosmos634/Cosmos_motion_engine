"""Pexels photo and video search provider."""
import os
from urllib.parse import urlencode

from ..asset_models import Asset
from .base import BaseProvider


class PexelsProvider(BaseProvider):
    name = "pexels"

    def __init__(self, api_key: str | None = None, timeout: int = 20):
        super().__init__(api_key if api_key is not None else os.getenv("PEXELS_API_KEY", ""), timeout)

    def search(self, query: str, media_type: str = "image", limit: int = 10) -> list[Asset]:
        limit = self.positive_limit(limit)
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if media_type not in {"image", "video"}:
            raise ValueError("Pexels supports image or video search")
        endpoint = "https://api.pexels.com/v1/search" if media_type == "image" else "https://api.pexels.com/videos/search"
        data = self.get_json(endpoint + "?" + urlencode({"query": query.strip(), "per_page": limit}),
                             {"Authorization": self.api_key})
        items = []
        for item in data.get("photos" if media_type == "image" else "videos", []):
            if media_type == "image":
                source = item.get("src", {})
                url = source.get("large") or source.get("original")
                thumb = source.get("medium") or source.get("small") or ""
                author = item.get("photographer", "")
                author_url = item.get("photographer_url", "")
                width, height, duration = item.get("width", 0), item.get("height", 0), 0
            else:
                candidates = [
                    f for f in item.get("video_files", [])
                    if f.get("file_type") == "video/mp4" and f.get("link")
                ]
                if not candidates:
                    continue
                suitable = [
                    f for f in candidates
                    if max(f.get("width", 0), f.get("height", 0)) <= 1920
                ]
                chosen = max(
                    suitable or candidates,
                    key=lambda f: f.get("width", 0) * f.get("height", 0),
                )
                url = chosen["link"]
                thumb = item.get("image", "")
                author = item.get("user", {}).get("name", "")
                author_url = item.get("user", {}).get("url", "")
                width, height, duration = chosen.get("width", 0), chosen.get("height", 0), item.get("duration", 0)
            if not url:
                continue
            items.append(Asset(
                id=str(item.get("id", "")), provider=self.name, media_type=media_type,
                title=f"Pexels {media_type} {item.get('id', '')}", url=url,
                source_page=item.get("url", ""), author=author, author_url=author_url,
                thumbnail_url=thumb, license="Pexels License",
                width=width, height=height, duration=duration,
            ))
        return items
