import unittest

from cosmo_engine.validator import ProjectValidationError, validate_project


VALID = {
    "version": 1,
    "project": {"width": 320, "height": 180, "fps": 24, "duration": 2, "background": "#000000"},
    "scenes": [{"id": "s1", "start": 0, "duration": 2, "elements": [
        {"type": "rect", "x": 0, "y": 0, "width": 50, "height": 40, "color": "red"}
    ]}],
}


class ValidatorTests(unittest.TestCase):
    def test_valid_project(self):
        self.assertTrue(validate_project(VALID))

    def test_unknown_root_key_rejected(self):
        data = {**VALID, "shell": "not allowed"}
        with self.assertRaises(ProjectValidationError):
            validate_project(data)

    def test_scene_outside_duration_rejected(self):
        data = {**VALID, "scenes": [{**VALID["scenes"][0], "duration": 3}]}
        with self.assertRaises(ProjectValidationError):
            validate_project(data)

    def test_unknown_element_type_rejected(self):
        data = {**VALID, "scenes": [{**VALID["scenes"][0], "elements": [{"type": "video"}]}]}
        with self.assertRaises(ProjectValidationError):
            validate_project(data)

    def test_valid_animation_track(self):
        scene = {**VALID["scenes"][0], "elements": [{
            "type": "rect", "x": 0, "y": 0, "width": 50, "height": 40,
            "color": "red", "animations": [{
                "property": "x", "from": 0, "to": 100, "start": 0,
                "duration": 1, "easing": "ease_out"
            }]
        }]}
        self.assertTrue(validate_project({**VALID, "scenes": [scene]}))

    def test_invalid_animation_easing_rejected(self):
        scene = {**VALID["scenes"][0], "elements": [{
            "type": "rect", "x": 0, "y": 0, "width": 50, "height": 40,
            "color": "red", "animations": [{
                "property": "x", "from": 0, "to": 100, "start": 0,
                "duration": 1, "easing": "bounce"
            }]
        }]}
        with self.assertRaises(ProjectValidationError):
            validate_project({**VALID, "scenes": [scene]})


if __name__ == "__main__":
    unittest.main()
