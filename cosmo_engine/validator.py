"""Strict validation for the Stage 1 JSON project format."""
from pathlib import Path
import math

TOP_KEYS = {"version", "project", "scenes"}
PROJECT_KEYS = {"width", "height", "fps", "duration", "background"}
SCENE_KEYS = {"id", "start", "duration", "elements"}
ELEMENT_KEYS = {
    "text": {"type", "text", "x", "y", "font_size", "color", "font"},
    "rect": {"type", "x", "y", "width", "height", "color"},
}
COLORS = {"black", "white", "red", "green", "blue", "yellow", "transparent"}


class ProjectValidationError(ValueError):
    """Raised when a project does not match the supported schema."""


def _keys(obj, allowed, required, where):
    if not isinstance(obj, dict):
        raise ProjectValidationError(f"{where} must be an object")
    missing = required - obj.keys()
    extra = obj.keys() - allowed
    if missing:
        raise ProjectValidationError(f"{where} missing keys: {', '.join(sorted(missing))}")
    if extra:
        raise ProjectValidationError(f"{where} has unsupported keys: {', '.join(sorted(extra))}")


def _number(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProjectValidationError(f"{name} must be a number")
    if not math.isfinite(value):
        raise ProjectValidationError(f"{name} must be finite")
    if minimum is not None and value < minimum:
        raise ProjectValidationError(f"{name} must be >= {minimum}")


def _color(value, name):
    if not isinstance(value, str) or not value:
        raise ProjectValidationError(f"{name} must be a color string")
    if value.lower() not in COLORS and not (
        len(value) in (7, 9) and value.startswith("#")
        and all(c in "0123456789abcdefABCDEF" for c in value[1:])
    ):
        raise ProjectValidationError(f"{name} must be a named basic color or #RRGGBB[AA]")


def validate_project(data, project_dir=None):
    _keys(data, TOP_KEYS, TOP_KEYS, "root")
    if data["version"] != 1:
        raise ProjectValidationError("version must be 1")

    p = data["project"]
    _keys(p, PROJECT_KEYS, PROJECT_KEYS, "project")
    for key in ("width", "height", "fps"):
        _number(p[key], f"project.{key}", 1)
        if int(p[key]) != p[key]:
            raise ProjectValidationError(f"project.{key} must be an integer")
    if p["width"] > 1920 or p["height"] > 1920:
        raise ProjectValidationError("Stage 1 maximum width and height is 1920")
    _number(p["duration"], "project.duration", 0.04)
    _color(p["background"], "project.background")
    if not isinstance(data["scenes"], list) or not data["scenes"]:
        raise ProjectValidationError("scenes must be a non-empty array")

    ids = set()
    for i, scene in enumerate(data["scenes"]):
        where = f"scenes[{i}]"
        _keys(scene, SCENE_KEYS, SCENE_KEYS, where)
        if not isinstance(scene["id"], str) or not scene["id"]:
            raise ProjectValidationError(f"{where}.id must be a non-empty string")
        if scene["id"] in ids:
            raise ProjectValidationError(f"duplicate scene id: {scene['id']}")
        ids.add(scene["id"])
        _number(scene["start"], f"{where}.start", 0)
        _number(scene["duration"], f"{where}.duration", 0.001)
        if scene["start"] + scene["duration"] > p["duration"] + 1e-6:
            raise ProjectValidationError(f"{where} extends beyond project duration")
        if not isinstance(scene["elements"], list):
            raise ProjectValidationError(f"{where}.elements must be an array")
        for j, element in enumerate(scene["elements"]):
            ewhere = f"{where}.elements[{j}]"
            if not isinstance(element, dict):
                raise ProjectValidationError(f"{ewhere} must be an object")
            etype = element.get("type")
            if etype not in ELEMENT_KEYS:
                raise ProjectValidationError(f"{ewhere}.type must be text or rect")
            required = ELEMENT_KEYS[etype] - {"font"}
            _keys(element, ELEMENT_KEYS[etype], required, ewhere)
            for key in ("x", "y"):
                _number(element[key], f"{ewhere}.{key}")
            _color(element["color"], f"{ewhere}.color")
            if etype == "text":
                if not isinstance(element["text"], str):
                    raise ProjectValidationError(f"{ewhere}.text must be a string")
                _number(element["font_size"], f"{ewhere}.font_size", 1)
                if "font" in element:
                    if not isinstance(element["font"], str):
                        raise ProjectValidationError(f"{ewhere}.font must be a string path")
                    if project_dir is not None:
                        base = Path(project_dir).resolve()
                        font_path = (base / element["font"]).resolve()
                        if base not in font_path.parents and font_path != base:
                            raise ProjectValidationError(f"{ewhere}.font path escapes project directory")
                        if not font_path.is_file():
                            raise ProjectValidationError(f"{ewhere}.font file not found")
            else:
                for key in ("width", "height"):
                    _number(element[key], f"{ewhere}.{key}", 1)
    return True
