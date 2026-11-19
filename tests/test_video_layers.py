import tempfile
import unittest
from pathlib import Path
from PIL import Image

from cosmo_engine.renderer import render_frame
from cosmo_engine.validator import ProjectValidationError, validate_project


BASE = {"version": 1, "project": {"width": 80, "height": 60, "fps": 2, "duration": 2, "background": "#000000"},
        "scenes": [{"id": "scene1", "start": 0, "duration": 2, "elements": []}]}


class FakeReader:
    def __init__(self, element, fps):
        self.size = (element["width"], element["height"])

    def frame_at(self, index):
        return Image.new("RGBA", self.size, (0, 255, 0, 255))


class VideoLayerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "clip.mp4").write_bytes(b"fake video placeholder")

    def tearDown(self):
        self.temp.cleanup()

    def project(self, element):
        return {**BASE, "scenes": [{**BASE["scenes"][0], "elements": [element]}]}

    def element(self):
        return {"type": "video", "id": "clip1", "source": "clip.mp4", "x": 10, "y": 5,
                "width": 20, "height": 10, "fit": "contain", "start": 0, "duration": 1}

    def test_video_schema_and_local_file(self):
        self.assertTrue(validate_project(self.project(self.element()), self.root))

    def test_video_path_escape_rejected(self):
        item = {**self.element(), "source": "../outside.mp4"}
        with self.assertRaises(ProjectValidationError):
            validate_project(self.project(item), self.root)

    def test_video_requires_id_and_dimensions(self):
        item = {k: v for k, v in self.element().items() if k != "id"}
        with self.assertRaises(ProjectValidationError):
            validate_project(self.project(item), self.root)

    def test_video_layer_composites_in_expected_position(self):
        import cosmo_engine.renderer as renderer
        key = ("scene1", "clip1")
        original = renderer._VIDEO_READERS.get(key)
        renderer._VIDEO_READERS[key] = FakeReader(self.element(), 2)
        try:
            item = {**self.element(), "source": str(self.root / "clip.mp4")}
            frame = render_frame(self.project(item), 0)
            self.assertEqual(frame.getpixel((15, 8)), (0, 255, 0))
            self.assertEqual(frame.getpixel((0, 0)), (0, 0, 0))
        finally:
            if original is None:
                renderer._VIDEO_READERS.pop(key, None)
            else:
                renderer._VIDEO_READERS[key] = original


if __name__ == "__main__":
    unittest.main()
