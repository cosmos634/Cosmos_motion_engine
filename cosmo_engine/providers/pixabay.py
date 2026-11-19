"""Pixabay image and video search provider."""
import os
from urllib.parse import urlencode

from ..asset_models import Asset
from .base import BaseProvider


class PixabayProvider(BaseProvider):
    name = "pixabay"

    def __init__(self, api_key: str | None = None, timeout: int = 20):
        super().__init__(api_key if api_key is not None else os.getenv("PIXABAY_API_KEY", ""), timeout)

    def search(self, query: str, media_type: str = "image", limit: int = 10) -> list[Asset]:
        limit = self.positive_limit(limit, 200)
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if media_type not in {"image", "video"}:
            raise ValueError("Pixabay supports image or video search")
        endpoint = "https://pixabay.com/api/" if media_type == "image" else "https://pixabay.com/api/videos/"
        data = self.get_json(endpoint + "?" + urlencode({"key": self.api_key, "q": query.strip(), "per_page": limit}))
        items = []
        for item in data.get("hits", []):
            if media_type == "image":
                url = item.get("largeImageURL") or item.get("webformatURL")
                thumb = item.get("previewURL", "")
                width, height, duration = item.get("imageWidth", 0), item.get("imageHeight", 0), 0
            else:
                variants = item.get("videos", {})
                chosen = variants.get("large") or variants.get("medium") or variants.get("small") or {}
                url, thumb = chosen.get("url"), item.get("userImageURL", "")
                width, height, duration = chosen.get("width", 0), chosen.get("height", 0), item.get("duration", 0)
            if not url:
                continue
            items.append(Asset(
                id=str(item.get("id", "")), provider=self.name, media_type=media_type,
                title=f"Pixabay {media_type} {item.get('id', '')}", url=url,
                source_page=item.get("pageURL", ""), author=item.get("user", ""),
                thumbnail_url=thumb, license="Pixabay Content License",
                width=width, height=height, duration=duration,
            ))
        return items
