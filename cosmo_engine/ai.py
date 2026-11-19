"""Prompt-to-project generation with Gemini primary and Groq fallback.

AI responses are treated only as untrusted JSON data. No generated code is
executed, and every project is checked by the existing project validator.
"""

import json
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
  "scenes": [
    {
      "id": "scene_1",
      "start": 0,
      "duration": 5,
      "elements": [
        {
          "type": "text",
          "text": "Example title",
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
- Use only supported project keys and element types: text and rect.
- Do not create image, video, font, or audio paths. Assets are added separately.
- Every scene must have id, start, duration, and elements.
- Every text element must have text, x, y, font_size, and color.
- Every rect must have x, y, width, height, and color.
- Colors must be #RRGGBB or a supported basic color.
- Animations are optional and may use only x, y, scale, rotation, opacity.
- Easing must be linear, ease_in, ease_out, or ease_in_out.
- A scene may use transition_in with fade, slide, wipe, or zoom and a duration.
- Scene times must fit entirely inside the requested total duration.
- Keep all positions and dimensions inside the requested canvas.
- Use concise Russian on-screen text unless the user requests another language.
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
            "Return only the project JSON."
        )
        errors = []
        for name, client in available:
            try:
                raw = client.generate_text(SYSTEM_PROMPT, user_prompt)
                project = self._parse_project(raw)
                validate_project(project)
                settings = project["project"]
                if (settings["width"], settings["height"], settings["fps"]) != (width, height, fps):
                    raise AIGenerationError("AI returned incorrect canvas dimensions or FPS")
                if abs(settings["duration"] - duration) > 0.001:
                    raise AIGenerationError("AI returned an incorrect project duration")
                return project, name
            except (AIProviderError, AIGenerationError, ProjectValidationError, KeyError, TypeError) as exc:
                errors.append(f"{name}: {exc}")
        raise AIGenerationError("All AI providers failed: " + "; ".join(errors))
