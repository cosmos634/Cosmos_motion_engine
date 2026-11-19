import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from cosmo_engine.asset_models import Asset
from cosmo_engine.assets import AssetError, AssetManager


class FakeResponse:
    def __init__(self, body, content_type="image/png", final_url="https://cdn.example.test/file"):
        self.body = body
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Content-Length"] = str(len(body))
        self.final_url = final_url
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        if size < 0:
            size = len(self.body)
        chunk = self.body[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk

    def geturl(self):
        return self.final_url


class AssetManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = AssetManager(
            cache_dir=self.temp.name, providers={}, max_image_bytes=1024, max_video_bytes=2048
        )
        self.asset = Asset(
            id="123", provider="test", media_type="image", title="test image",
            url="https://cdn.example.test/file.png", source_page="https://example.test/source",
            author="Author", license="Example license",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_creates_cache_directories(self):
        for name in ("images", "videos", "metadata"):
            self.assertTrue((Path(self.temp.name) / name).is_dir())

    def test_rejects_non_https_asset_url(self):
        self.asset.url = "http://cdn.example.test/file.png"
        with self.assertRaises(AssetError):
            self.manager.download(self.asset)

    def test_download_saves_file_and_metadata(self):
        with patch("cosmo_engine.assets.urlopen", return_value=FakeResponse(b"image-bytes")):
            path = self.manager.download(self.asset)
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes(), b"image-bytes")
        records = self.manager.cached_assets()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["author"], "Author")
        self.assertEqual(records[0]["local_path"], str(path))

    def test_rejects_unexpected_content_type(self):
        with patch("cosmo_engine.assets.urlopen", return_value=FakeResponse(b"not-image", "text/html")):
            with self.assertRaises(AssetError):
                self.manager.download(self.asset)

    def test_rejects_file_larger_than_limit(self):
        with patch("cosmo_engine.assets.urlopen", return_value=FakeResponse(b"x" * 1025)):
            with self.assertRaises(AssetError):
                self.manager.download(self.asset)

    def test_search_rejects_unconfigured_provider(self):
        with self.assertRaises(AssetError):
            self.manager.search("pexels", "nature")

    def test_metadata_corruption_is_skipped(self):
        metadata = Path(self.temp.name) / "metadata" / "bad.json"
        metadata.write_text("{", encoding="utf-8")
        self.assertEqual(self.manager.cached_assets(), [])


if __name__ == "__main__":
    unittest.main()
