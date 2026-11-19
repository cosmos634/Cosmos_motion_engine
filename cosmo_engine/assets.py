"""Provider-agnostic asset search, safe downloads, and local metadata cache."""
import hashlib
import json
import mimetypes
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .asset_models import Asset
from .providers import PexelsProvider, PixabayProvider, UnsplashProvider
from .providers.base import ProviderError


class AssetError(RuntimeError):
    """Raised for invalid or failed asset operations."""


class AssetManager:
    MIME_EXTENSIONS = {
        "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif",
        "video/mp4": ".mp4", "video/webm": ".webm",
    }
    MEDIA_MIMES = {
        "image": {"image/jpeg", "image/png", "image/webp", "image/gif"},
        "video": {"video/mp4", "video/webm"},
    }

    def __init__(self, cache_dir=".cosmo_cache", providers=None, timeout=30,
                 max_image_bytes=20 * 1024 * 1024, max_video_bytes=100 * 1024 * 1024):
        self.cache_dir = Path(cache_dir).expanduser().resolve()
        self.timeout = timeout
        self.max_image_bytes = max_image_bytes
        self.max_video_bytes = max_video_bytes
        self.providers = providers if providers is not None else self._configured_providers()
        for folder in ("images", "videos", "metadata"):
            (self.cache_dir / folder).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _configured_providers():
        providers = {}
        for name, factory in (
            ("pexels", PexelsProvider), ("pixabay", PixabayProvider), ("unsplash", UnsplashProvider)
        ):
            try:
                providers[name] = factory()
            except ProviderError:
                continue
        return providers

    def search(self, provider: str, query: str, media_type="image", limit=10) -> list[Asset]:
        if provider not in self.providers:
            available = ", ".join(sorted(self.providers)) or "none (configure an API key)"
            raise AssetError(f"Provider '{provider}' is unavailable. Configured providers: {available}")
        try:
            return self.providers[provider].search(query, media_type, limit)
        except (ProviderError, ValueError) as exc:
            raise AssetError(str(exc)) from exc

    def download(self, asset: Asset) -> Path:
        if asset.media_type not in self.MEDIA_MIMES:
            raise AssetError("Only image and video downloads are supported")
        parsed = urlparse(asset.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise AssetError("Asset URL must use HTTPS")
        max_bytes = self.max_image_bytes if asset.media_type == "image" else self.max_video_bytes
        request = Request(asset.url, headers={"User-Agent": "CosmoMotionEngine/0.2"}, method="GET")
        temporary = None
        try:
            with urlopen(request, timeout=self.timeout) as response:
                final_url = urlparse(response.geturl())
                if final_url.scheme != "https":
                    raise AssetError("Download redirected to a non-HTTPS URL")
                content_type = response.headers.get_content_type().lower()
                if content_type not in self.MEDIA_MIMES[asset.media_type]:
                    raise AssetError(f"Unexpected content type for {asset.media_type}: {content_type}")
                length = response.headers.get("Content-Length")
                if length and int(length) > max_bytes:
                    raise AssetError(f"Asset exceeds the {max_bytes} byte download limit")
                digest = hashlib.sha256(f"{asset.provider}:{asset.id}:{asset.url}".encode()).hexdigest()[:20]
                extension = self.MIME_EXTENSIONS[content_type]
                folder = "images" if asset.media_type == "image" else "videos"
                target = self.cache_dir / folder / f"{digest}{extension}"
                if target.is_file():
                    self._write_metadata(asset, target)
                    return target
                temporary = target.with_suffix(target.suffix + ".part")
                total = 0
                with temporary.open("wb") as output:
                    while True:
                        chunk = response.read(64 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > max_bytes:
                            raise AssetError(f"Asset exceeds the {max_bytes} byte download limit")
                        output.write(chunk)
                if total == 0:
                    raise AssetError("Downloaded asset is empty")
                temporary.replace(target)
                self._write_metadata(asset, target)
                return target
        except AssetError:
            if temporary and temporary.exists():
                temporary.unlink()
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            if temporary and temporary.exists():
                temporary.unlink()
            raise AssetError(f"Download failed: {exc}") from exc

    def _write_metadata(self, asset: Asset, local_path: Path) -> Path:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", asset.id)[:80] or "asset"
        digest = hashlib.sha256(f"{asset.provider}:{asset.id}:{asset.url}".encode()).hexdigest()[:20]
        path = self.cache_dir / "metadata" / f"{digest}.json"
        payload = asset.to_dict()
        payload["local_path"] = str(local_path)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def cached_assets(self) -> list[dict]:
        records = []
        for path in sorted((self.cache_dir / "metadata").glob("*.json")):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return records
