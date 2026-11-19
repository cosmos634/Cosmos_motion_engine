import unittest
from PIL import Image

from cosmo_engine.renderer import apply_transition


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.layer = Image.new("RGBA", (20, 10), (255, 0, 0, 255))

    def test_fade_starts_transparent_and_ends_opaque(self):
        start = apply_transition(self.layer, {"type": "fade", "duration": 1}, 0)
        end = apply_transition(self.layer, {"type": "fade", "duration": 1}, 1)
        self.assertEqual(start.getpixel((10, 5))[3], 0)
        self.assertEqual(end.getpixel((10, 5))[3], 255)

    def test_slide_reaches_final_position(self):
        result = apply_transition(self.layer, {"type": "slide", "duration": 1, "direction": "left"}, 1)
        self.assertEqual(result.getpixel((10, 5)), (255, 0, 0, 255))

    def test_wipe_reveals_full_layer_at_end(self):
        result = apply_transition(self.layer, {"type": "wipe", "duration": 1, "direction": "left"}, 1)
        self.assertEqual(result.getpixel((10, 5))[3], 255)

    def test_zoom_reaches_full_frame_at_end(self):
        result = apply_transition(self.layer, {"type": "zoom", "duration": 1}, 1)
        self.assertEqual(result.size, self.layer.size)
        self.assertEqual(result.getpixel((10, 5))[3], 255)


if __name__ == "__main__":
    unittest.main()
