import tempfile
import unittest
from pathlib import Path

from PIL import Image

from cosmo_engine.renderer import render_frame
from cosmo_engine.validator import ProjectValidationError, validate_project


BASE = {
    "version": 1,
    "project": {"width": 80, "height": 60, "fps": 1, "duration": 1, "background": "#000000"},
    "scenes": [{"id": "s1", "start": 0, "duration": 1, "elements": []}],
}


class ImageLayerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        Image.new("RGBA", (20, 10), (255, 0, 0, 255)).save(self.root / "sample.png")

    def tearDown(self):
        self.temp.cleanup()

    def project(self, element):
        return {**BASE, "scenes": [{**BASE["scenes"][0], "elements": [element]}]}

    def test_valid_image_element(self):
        element = {"type": "image", "source": "sample.png", "x": 0, "y": 0}
        self.assertTrue(validate_project(self.project(element), self.root))

    def test_missing_image_rejected(self):
        element = {"type": "image", "source": "missing.png", "x": 0, "y": 0}
        with self.assertRaises(ProjectValidationError):
            validate_project(self.project(element), self.root)

    def test_path_escape_rejected(self):
        element = {"type": "image", "source": "../outside.png", "x": 0, "y": 0}
        with self.assertRaises(ProjectValidationError):
            validate_project(self.project(element), self.root)

    def test_dimensions_must_be_paired(self):
        element = {"type": "image", "source": "sample.png", "x": 0, "y": 0, "width": 20}
        with self.assertRaises(ProjectValidationError):
            validate_project(self.project(element), self.root)

    def test_render_image_layer(self):
        element = {"type": "image", "source": str(self.root / "sample.png"), "x": 5, "y": 7}
        frame = render_frame(self.project(element), 0)
        self.assertEqual(frame.getpixel((10, 10)), (255, 0, 0))
        self.assertEqual(frame.getpixel((0, 0)), (0, 0, 0))

    def test_image_fit_and_animation_validation(self):
        element = {
            "type": "image", "source": "sample.png", "x": 0, "y": 0,
            "width": 40, "height": 40, "fit": "contain",
            "animations": [{
                "property": "opacity", "from": 0, "to": 1,
                "start": 0, "duration": 1, "easing": "linear"
            }]
        }
        self.assertTrue(validate_project(self.project(element), self.root))


if __name__ == "__main__":
    unittest.main()
