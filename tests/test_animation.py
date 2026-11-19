import unittest

from cosmo_engine.animation import animated_value, ease


class AnimationTests(unittest.TestCase):
    def test_linear_interpolation(self):
        self.assertAlmostEqual(ease(0.5, "linear"), 0.5)

    def test_ease_in(self):
        self.assertAlmostEqual(ease(0.5, "ease_in"), 0.25)

    def test_ease_out(self):
        self.assertAlmostEqual(ease(0.5, "ease_out"), 0.75)

    def test_ease_in_out(self):
        self.assertAlmostEqual(ease(0.25, "ease_in_out"), 0.125)
        self.assertAlmostEqual(ease(0.75, "ease_in_out"), 0.875)

    def test_animation_before_during_after(self):
        track = [{"property": "x", "from": 10, "to": 30,
                  "start": 1, "duration": 2, "easing": "linear"}]
        self.assertEqual(animated_value(0, track, "x", 0.5), 10)
        self.assertEqual(animated_value(0, track, "x", 2), 20)
        self.assertEqual(animated_value(0, track, "x", 3.5), 30)

    def test_unmatched_property_keeps_base(self):
        self.assertEqual(animated_value(12, [], "x", 1), 12)


if __name__ == "__main__":
    unittest.main()
