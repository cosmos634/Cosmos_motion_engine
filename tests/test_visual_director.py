import unittest

from cosmo_engine.visual_director import apply_visual_direction, infer_visual_style


def sample_project():
    return {
        "version": 1,
        "project": {"width": 1080, "height": 1920, "fps": 30, "duration": 8, "background": "#101426"},
        "scenes": [{
            "id": "scene_1", "start": 0, "duration": 8,
            "elements": [
                {"type": "image", "source": "assets/bg.jpg", "x": 0, "y": 0, "width": 1080, "height": 1920, "fit": "cover"},
                {"type": "rect", "x": 0, "y": 0, "width": 1080, "height": 1920, "color": "#07111F99"},
                {"type": "text", "text": "Тайны космоса", "x": 86, "y": 1050, "font_size": 82, "color": "#FFFFFF"},
                {"type": "text", "text": "Что скрывает Вселенная?", "x": 86, "y": 1170, "font_size": 38, "color": "#FFFFFF"},
            ],
        }],
    }


class VisualDirectorTests(unittest.TestCase):
    def test_infers_styles(self):
        self.assertEqual(infer_visual_style("История древнего Рима"), "historical_documentary")
        self.assertEqual(infer_visual_style("Научный ролик о космосе"), "scientific_visualization")
        self.assertEqual(infer_visual_style("Create a TikTok motivation short"), "social_media")

    def test_adds_camera_motion_and_text_entrances(self):
        project = sample_project()
        style = apply_visual_direction(project, "A documentary about space")
        self.assertEqual(style, "scientific_visualization")
        image = project["scenes"][0]["elements"][0]
        self.assertEqual({a["property"] for a in image["animations"]}, {"scale", "x", "y"})
        title = next(e for e in project["scenes"][0]["elements"] if e.get("text") == "Тайны космоса")
        self.assertEqual({a["property"] for a in title["animations"]}, {"opacity", "y", "scale"})
        self.assertTrue(any(e.get("type") == "rect" and e.get("color") == "#55E6D0" for e in project["scenes"][0]["elements"]))

    def test_is_idempotent(self):
        project = sample_project()
        apply_visual_direction(project, "cinematic")
        first_count = len(project["scenes"][0]["elements"])
        apply_visual_direction(project, "cinematic")
        self.assertEqual(len(project["scenes"][0]["elements"]), first_count)
        image = project["scenes"][0]["elements"][0]
        self.assertEqual(\n            {animation["property"] for animation in image["animations"]},\n            {"scale", "x", "y"},\n        )\n        self.assertEqual(len(image["animations"]), 3)

    def test_preserves_existing_animation_properties(self):
        project = sample_project()
        image = project["scenes"][0]["elements"][0]
        image["animations"] = [{
            "property": "scale", "from": 1, "to": 1.05,
            "start": 0, "duration": 8, "easing": "linear",
        }]
        apply_visual_direction(project, "cinematic")
        self.assertEqual(len([a for a in image["animations"] if a["property"] == "scale"]), 1)


if __name__ == "__main__":
    unittest.main()
