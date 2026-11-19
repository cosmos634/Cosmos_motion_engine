import json
import unittest

from cosmo_engine.ai import AIGenerationError, ProjectGenerator


def valid_project():
    return {
        "version": 1,
        "project": {
            "width": 1080, "height": 1920, "fps": 30,
            "duration": 20, "background": "#101426",
        },
        "scenes": [{
            "id": "intro", "start": 0, "duration": 20,
            "elements": [{
                "type": "text", "text": "Привет", "x": 80, "y": 300,
                "font_size": 72, "color": "#FFFFFF",
            }],
        }],
    }


class FakeProvider:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def generate_text(self, system_prompt, user_prompt):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


class ProjectGeneratorTests(unittest.TestCase):
    def test_parse_plain_json(self):
        project = valid_project()
        self.assertEqual(ProjectGenerator._parse_project(json.dumps(project)), project)

    def test_parse_json_markdown_fence(self):
        project = valid_project()
        raw = " ```json\n" + json.dumps(project, ensure_ascii=False) + "\n``` "
        self.assertEqual(ProjectGenerator._parse_project(raw), project)

    def test_rejects_non_object_json(self):
        with self.assertRaises(AIGenerationError):
            ProjectGenerator._parse_project("[]")

    def test_gemini_is_primary(self):
        gemini = FakeProvider(response=json.dumps(valid_project(), ensure_ascii=False))
        groq = FakeProvider(response=json.dumps(valid_project(), ensure_ascii=False))
        result, used = ProjectGenerator(gemini=gemini, groq=groq).generate("demo")
        self.assertEqual(used, "gemini")
        self.assertEqual(gemini.calls, 1)
        self.assertEqual(groq.calls, 0)
        self.assertEqual(result["project"]["width"], 1080)

    def test_falls_back_to_groq_when_gemini_fails(self):
        gemini = FakeProvider(error=RuntimeError("offline"))
        groq = FakeProvider(response=json.dumps(valid_project(), ensure_ascii=False))
        result, used = ProjectGenerator(gemini=gemini, groq=groq).generate("demo")
        self.assertEqual(used, "groq")
        self.assertEqual(gemini.calls, 1)
        self.assertEqual(groq.calls, 1)

    def test_invalid_project_falls_back(self):
        gemini = FakeProvider(response='{"invalid": true}')
        groq = FakeProvider(response=json.dumps(valid_project(), ensure_ascii=False))
        _, used = ProjectGenerator(gemini=gemini, groq=groq).generate("demo")
        self.assertEqual(used, "groq")

    def test_animation_timing_is_clamped_to_scene(self):
        project = valid_project()
        project["scenes"][0]["duration"] = 5
        project["scenes"][0]["elements"][0]["animations"] = [{
            "property": "opacity", "from": 0, "to": 1,
            "start": 4.5, "duration": 2, "easing": "ease_out",
        }]
        provider = FakeProvider(response=json.dumps(project))
        result, used = ProjectGenerator(groq=provider).generate("demo")
        animation = result["scenes"][0]["elements"][0]["animations"][0]
        self.assertEqual(used, "groq")
        self.assertEqual(animation["start"], 4.5)
        self.assertEqual(animation["duration"], 0.5)

    def test_animation_start_after_scene_is_shifted_inside(self):
        project = valid_project()
        project["scenes"][0]["duration"] = 5
        project["scenes"][0]["elements"][0]["animations"] = [{
            "property": "opacity", "from": 0, "to": 1,
            "start": 8, "duration": 1, "easing": "ease_out",
        }]
        provider = FakeProvider(response=json.dumps(project))
        result, _ = ProjectGenerator(groq=provider).generate("demo")
        animation = result["scenes"][0]["elements"][0]["animations"][0]
        self.assertEqual(animation["start"], 4.999)
        self.assertEqual(animation["duration"], 0.001)

    def test_invalid_prompt_is_rejected(self):
        with self.assertRaises(ValueError):
            ProjectGenerator(gemini=FakeProvider()).generate("  ")

    def test_selected_provider_does_not_fallback(self):
        gemini = FakeProvider(error=RuntimeError("offline"))
        groq = FakeProvider(response=json.dumps(valid_project(), ensure_ascii=False))
        with self.assertRaises(AIGenerationError):
            ProjectGenerator(gemini=gemini, groq=groq).generate("demo", provider="gemini")
        self.assertEqual(groq.calls, 0)


if __name__ == "__main__":
    unittest.main()
