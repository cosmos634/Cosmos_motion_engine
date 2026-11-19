"""Prompt-to-project generation with Gemini primary and Groq fallback.

AI responses are treated only as untrusted JSON data. No generated code is
executed, and every project is checked by the existing project validator.
"""

import json
import math
import os

from .ai_providers import GeminiProvider, GroqProvider
from .ai_providers.base import AIProviderError
from .validator import ProjectValidationError, validate_project


SYSTEM_PROMPT = """You are the storyboard and project-JSON generator for Cosmo Motion Engine.
Return exactly one valid JSON object and nothing else. Never return Markdown,
Python, shell commands, HTML, explanations, or code.

The JSON must follow this schema:
{
  "version": 1,
  "project": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "duration": 20,
    "background": "#101426"
  },
  "voiceover": "Полный связный текст дикторской речи на русском языке.",
  "visual_style": "cinematic_documentary",
  "scenes": [
    {
      "id": "scene_1",
      "start": 0,
      "duration": 5,
      "elements": [
        {
          "type": "text",
          "text": "Тайны космоса",
          "x": 80,
          "y": 300,
          "font_size": 72,
          "color": "#FFFFFF",
          "animations": [
            {
              "property": "opacity",
              "from": 0,
              "to": 1,
              "start": 0,
              "duration": 0.7,
              "easing": "ease_out"
            }
          ]
        },
        {
          "type": "rect",
          "x": 60,
          "y": 250,
          "width": 960,
          "height": 240,
          "color": "#202D50"
        }
      ]
    }
  ]
}

Strict rules:
- Use only supported project keys and element types: text and rect. A real photo background is added automatically by the Asset Manager after generation.
- Set visual_style to exactly one of: cinematic_documentary, modern_motion_graphics, social_media, historical_documentary, scientific_visualization.
- Do not create image, video, font, or audio paths.
- Every scene must have id, start, duration, and elements.
- Every text element must have text, x, y, font_size, and color.
- Every rect must have x, y, width, height, and color.
- Colors must be #RRGGBB or a supported basic color.
- Animations are optional and may use only x, y, scale, rotation, opacity.
- Easing must be linear, ease_in, ease_out, or ease_in_out.
- A scene may use transition_in with fade, slide, wipe, or zoom and a duration.
- Scene times must fit entirely inside the requested total duration.
- Keep all positions and dimensions inside the requested canvas.
- Follow professional motion-design principles: strong visual hierarchy, generous negative space, consistent alignment, readable contrast, and a restrained 2–3 color palette.
- Choose visual_style from the brief: cinematic_documentary for cinematic stories, modern_motion_graphics for technology/design, social_media for fast short-form content, historical_documentary for history, scientific_visualization for science/space.
- Compose each scene as a designed frame, not a stack of centered labels: use intentional asymmetry, clear headline/supporting-copy hierarchy, and consistent margins.
- Use a bold short headline, one supporting line at most, and avoid filling the whole frame with text.
- Use purposeful geometric accents, subtle panels, and layered depth; avoid random rectangles and clutter.
- Place important text within the central 80% safe area and never let text touch the edges.
- Use a dark cinematic palette with one bright accent unless the brief requests another mood.
- IMPORTANT: The complete video language is Russian (ru-RU), regardless of the language used in the user's prompt.
- Write every on-screen text element in natural Russian.
- Include a "voiceover" field containing a coherent, natural Russian narration script for the full video. It must be suitable for spoken delivery, not just a list of titles. Do not include stage directions or sound descriptions.
- Make a coherent sequence with a clear hook, progression, and ending.
- Do not invent external media filenames or pretend that assets already exist.
"""


class AIGenerationError(RuntimeError):
    """Raised when no configured AI provider can create a valid project."""


class ProjectGenerator:
    def __init__(self, gemini=None, groq=None):
        self.gemini = gemini
        self.groq = groq

    @staticmethod
    def _configured_providers():
        providers = []
        if os.getenv("GEMINI_API_KEY"):
            providers.append(("gemini", GeminiProvider()))
        if os.getenv("GROQ_API_KEY"):
            providers.append(("groq", GroqProvider()))
        return providers

    @staticmethod
    def _parse_project(raw):
        if not isinstance(raw, str):
            raise AIGenerationError("AI response must be text")
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            project = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise AIGenerationError("AI did not return a JSON project")
            try:
                project = json.loads(text[start:end + 1])
            except json.JSONDecodeError as exc:
                raise AIGenerationError("AI returned malformed project JSON") from exc
        if not isinstance(project, dict):
            raise AIGenerationError("AI project must be a JSON object")
        return project

    @staticmethod
    def _normalize_animation_timing(project):
        """Keep valid numeric animations inside their scene boundaries."""
        scenes = project.get("scenes", [])
        if not isinstance(scenes, list):
            return
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            scene_duration = scene.get("duration")
            if (
                isinstance(scene_duration, bool)
                or not isinstance(scene_duration, (int, float))
                or not math.isfinite(scene_duration)
                or scene_duration < 0.001
            ):
                continue
            elements = scene.get("elements", [])
            if not isinstance(elements, list):
                continue
            for element in elements:
                if not isinstance(element, dict):
                    continue
                animations = element.get("animations", [])
                if not isinstance(animations, list):
                    continue
                for animation in animations:
                    if not isinstance(animation, dict):
                        continue
                    start = animation.get("start")
                    duration = animation.get("duration")
                    if (
                        isinstance(start, bool)
                        or isinstance(duration, bool)
                        or not isinstance(start, (int, float))
                        or not isinstance(duration, (int, float))
                        or not math.isfinite(start)
                        or not math.isfinite(duration)
                        or start < 0
                        or duration <= 0
                    ):
                        continue
                    if start >= scene_duration:
                        start = max(0, scene_duration - 0.001)
                    animation["start"] = start
                    animation["duration"] = max(
                        0.001, min(duration, scene_duration - start)
                    )

    def generate(self, prompt, provider="auto", width=1080, height=1920, fps=30, duration=20):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must not be empty")
        if provider not in {"auto", "gemini", "groq"}:
            raise ValueError("provider must be auto, gemini, or groq")
        if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= 1920:
            raise ValueError("width must be an integer from 1 to 1920")
        if isinstance(height, bool) or not isinstance(height, int) or not 1 <= height <= 1920:
            raise ValueError("height must be an integer from 1 to 1920")
        if isinstance(fps, bool) or not isinstance(fps, int) or not 1 <= fps <= 60:
            raise ValueError("fps must be an integer from 1 to 60")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 0.04 <= duration <= 600:
            raise ValueError("duration must be between 0.04 and 600 seconds")

        if self.gemini is not None or self.groq is not None:
            available = []
            if self.gemini is not None:
                available.append(("gemini", self.gemini))
            if self.groq is not None:
                available.append(("groq", self.groq))
        else:
            available = self._configured_providers()

        if provider == "gemini":
            available = [item for item in available if item[0] == "gemini"]
        elif provider == "groq":
            available = [item for item in available if item[0] == "groq"]
        else:
            available.sort(key=lambda item: 0 if item[0] == "gemini" else 1)

        if not available:
            key_name = "GEMINI_API_KEY" if provider == "gemini" else "GROQ_API_KEY" if provider == "groq" else "GEMINI_API_KEY or GROQ_API_KEY"
            raise AIGenerationError(f"No selected AI provider is configured. Set {key_name}.")

        user_prompt = (
            f"Create a video project from this brief:\n{prompt.strip()}\n\n"
            f"Required canvas: {width}x{height}. FPS: {fps}. "
            f"Total duration: exactly {duration} seconds. "
            "The complete video must be in Russian (ru-RU): all visible text and the voiceover script. "
            "Include a natural Russian voiceover in the top-level voiceover field. "
            "Return only the project JSON."
        )
        errors = []
        for name, client in available:
            try:
                raw = client.generate_text(SYSTEM_PROMPT, user_prompt)
                project = self._parse_project(raw)
                self._normalize_animation_timing(project)
                validate_project(project)
                settings = project["project"]
                if (settings["width"], settings["height"], settings["fps"]) != (width, height, fps):
                    raise AIGenerationError("AI returned incorrect canvas dimensions or FPS")
                if abs(settings["duration"] - duration) > 0.001:
                    raise AIGenerationError("AI returned an incorrect project duration")
                return project, name
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        raise AIGenerationError("All AI providers failed: " + "; ".join(errors))
