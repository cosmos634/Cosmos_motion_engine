import unittest
from PIL import ImageFont

from cosmo_engine.renderer import _text_layer


class TextLayoutTests(unittest.TestCase):
    def test_long_russian_text_wraps_inside_mobile_canvas(self):
        element = {
            "type": "text",
            "text": "Почему космос до сих пор хранит множество загадок для современной науки",
            "x": 72,
            "y": 900,
            "font_size": 82,
            "color": "#FFFFFF",
        }
        layer = _text_layer(element, None, 1080, 1920)
        self.assertLessEqual(layer.width, 1080 - 72 - round(1080 * 0.055))
        self.assertGreater(layer.height, 82)

    def test_long_uzbek_text_fits_available_height(self):
        element = {
            "type": "text",
            "text": "Sun'iy intellekt kelajakdagi texnologiyalar rivojiga qanday ta'sir ko'rsatadi",
            "x": 64,
            "y": 1500,
            "font_size": 72,
            "color": "#FFFFFF",
        }
        layer = _text_layer(element, None, 1080, 1920)
        self.assertLessEqual(layer.height, 1920 - 1500 - round(1920 * 0.035))

    def test_short_text_keeps_requested_size(self):
        element = {
            "type": "text", "text": "COSMO", "x": 60, "y": 100,
            "font_size": 48, "color": "#FFFFFF",
        }
        layer = _text_layer(element, None, 1080, 1920)
        self.assertGreater(layer.width, 0)
        self.assertGreater(layer.height, 0)


if __name__ == "__main__":
    unittest.main()
