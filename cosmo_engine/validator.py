"""Strict validator for the Stage 5 JSON project format."""
from pathlib import Path
import math

TOP_KEYS = {"version", "project", "scenes", "audio", "voiceover", "visual_style"}
PROJECT_KEYS = {"width", "height", "fps", "duration", "background"}
SCENE_KEYS = {"id", "start", "duration", "elements", "transition_in"}
ELEMENT_KEYS = {
    "text": {"type", "text", "x", "y", "font_size", "color", "font", "animations"},
    "rect": {"type", "x", "y", "width", "height", "color", "animations"},
    "image": {"type", "source", "x", "y", "width", "height", "fit", "animations"},
    "video": {"type", "id", "source", "x", "y", "width", "height", "fit", "start", "duration", "source_start", "animations"},
}
ANIMATION_KEYS = {"property", "from", "to", "start", "duration", "easing"}
ANIMATABLE = {"x", "y", "scale", "rotation", "opacity"}
EASINGS = {"linear", "ease_in", "ease_out", "ease_in_out"}
COLORS = {"black", "white", "red", "green", "blue", "yellow", "transparent"}
AUDIO_KEYS = {"kind", "source", "start", "duration", "volume", "fade_in", "fade_out", "loop"}
AUDIO_KINDS = {"narration", "music", "sfx"}


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


def _number(value, name, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ProjectValidationError(f"{name} must be a finite number")
    if minimum is not None and value < minimum:
        raise ProjectValidationError(f"{name} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ProjectValidationError(f"{name} must be <= {maximum}")


def _color(value, name):
    if not isinstance(value, str) or not value:
        raise ProjectValidationError(f"{name} must be a color string")
    if value.lower() not in COLORS and not (
        len(value) in (7, 9) and value.startswith("#")
        and all(c in "0123456789abcdefABCDEF" for c in value[1:])
    ):
        raise ProjectValidationError(f"{name} must be a named basic color or #RRGGBB[AA]")


def validate_project(data, project_dir=None):
    _keys(data, TOP_KEYS, TOP_KEYS - {"audio", "voiceover"}, "root")
    if "visual_style" in data and data["visual_style"] not in {\n        "cinematic_documentary", "modern_motion_graphics", "social_media",\n        "historical_documentary", "scientific_visualization",\n    }:\n        raise ProjectValidationError("visual_style is not supported")\n    if "voiceover" in data and (
        not isinstance(data["voiceover"], str)
        or len(data["voiceover"].strip()) > 12000
    ):
        raise ProjectValidationError("voiceover must be a string up to 12000 characters")
    if data["version"] != 1:
        raise ProjectValidationError("version must be 1")
    p = data["project"]
    _keys(p, PROJECT_KEYS, PROJECT_KEYS, "project")
    for key in ("width", "height", "fps"):
        _number(p[key], f"project.{key}", 1)
        if int(p[key]) != p[key]:
            raise ProjectValidationError(f"project.{key} must be an integer")
    if p["width"] > 1920 or p["height"] > 1920:
        raise ProjectValidationError("maximum width and height is 1920")
    _number(p["duration"], "project.duration", 0.04)
    _color(p["background"], "project.background")
    if not isinstance(data["scenes"], list) or not data["scenes"]:
        raise ProjectValidationError("scenes must be a non-empty array")

    ids = set()
    for i, scene in enumerate(data["scenes"]):
        where = f"scenes[{i}]"
        _keys(scene, SCENE_KEYS, SCENE_KEYS - {"transition_in"}, where)
        if not isinstance(scene["id"], str) or not scene["id"]:
            raise ProjectValidationError(f"{where}.id must be a non-empty string")
        if scene["id"] in ids:
            raise ProjectValidationError(f"duplicate scene id: {scene['id']}")
        ids.add(scene["id"])
        _number(scene["start"], f"{where}.start", 0)
        _number(scene["duration"], f"{where}.duration", 0.001)
        if scene["start"] + scene["duration"] > p["duration"] + 1e-6:
            raise ProjectValidationError(f"{where} extends beyond project duration")
        transition = scene.get("transition_in")
        if transition is not None:
            _keys(transition, {"type", "duration", "direction"}, {"type", "duration"}, f"{where}.transition_in")
            transition_types = {"fade", "slide", "wipe", "zoom"}
            if not isinstance(transition["type"], str) or transition["type"] not in transition_types:
                raise ProjectValidationError(f"{where}.transition_in.type must be fade, slide, wipe, or zoom")
            _number(transition["duration"], f"{where}.transition_in.duration", 0.001)
            if transition["duration"] > scene["duration"]:
                raise ProjectValidationError(f"{where}.transition_in.duration cannot exceed scene duration")
            directions = {"left", "right", "up", "down"}
            if "direction" in transition and (
                not isinstance(transition["direction"], str) or transition["direction"] not in directions
            ):
                raise ProjectValidationError(f"{where}.transition_in.direction must be left, right, up, or down")
        if not isinstance(scene["elements"], list):
            raise ProjectValidationError(f"{where}.elements must be an array")
        video_ids = set()
        for j, element in enumerate(scene["elements"]):
            ewhere = f"{where}.elements[{j}]"
            if not isinstance(element, dict):
                raise ProjectValidationError(f"{ewhere} must be an object")
            etype = element.get("type")
            if not isinstance(etype, str) or etype not in ELEMENT_KEYS:
                raise ProjectValidationError(f"{ewhere}.type must be text, rect, image, or video")
            required = ELEMENT_KEYS[etype] - {"font", "animations", "width", "height", "fit"}
            if etype in {"image", "video"}:
                required = {"type", "source", "x", "y"}
                if etype == "video":
                    required |= {"id", "width", "height"}
                if ("width" in element) != ("height" in element):
                    raise ProjectValidationError(f"{ewhere} width and height must be supplied together")
            _keys(element, ELEMENT_KEYS[etype], required, ewhere)
            for key in ("x", "y"):
                _number(element[key], f"{ewhere}.{key}")
            if etype in {"image", "video"}:
                source = element["source"]
                if not isinstance(source, str) or not source:
                    raise ProjectValidationError(f"{ewhere}.source must be a non-empty path")
                if project_dir is not None:
                    base = Path(project_dir).resolve()
                    image_path = (base / source).resolve()
                    if base not in image_path.parents:
                        raise ProjectValidationError(f"{ewhere}.source path escapes project directory")
                    if not image_path.is_file():
                        raise ProjectValidationError(f"{ewhere}.source file not found")
                if "width" in element:
                    for key in ("width", "height"):
                        _number(element[key], f"{ewhere}.{key}", 1, 1920)
                if element.get("fit", "contain") not in {"contain", "cover", "stretch"}:
                    raise ProjectValidationError(f"{ewhere}.fit must be contain, cover, or stretch")
                if etype == "video":
                    if not isinstance(element["id"], str) or not element["id"]:
                        raise ProjectValidationError(f"{ewhere}.id must be a non-empty string")
                    if element["id"] in video_ids:
                        raise ProjectValidationError(f"{ewhere}.id must be unique within its scene")
                    video_ids.add(element["id"])
                    _number(element.get("start", 0), f"{ewhere}.start", 0)
                    if "duration" in element:
                        _number(element["duration"], f"{ewhere}.duration", 0.001)
                        if element.get("start", 0) + element["duration"] > scene["duration"] + 1e-6:
                            raise ProjectValidationError(f"{ewhere} extends beyond its scene")
                    _number(element.get("source_start", 0), f"{ewhere}.source_start", 0)
            elif etype not in {"image", "video"}:
                _color(element["color"], f"{ewhere}.color")
            if etype == "text":
                if not isinstance(element["text"], str):
                    raise ProjectValidationError(f"{ewhere}.text must be a string")
                _number(element["font_size"], f"{ewhere}.font_size", 1, 512)
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
            elif etype == "rect":
                for key in ("width", "height"):
                    _number(element[key], f"{ewhere}.{key}", 1, 1920)
            animations = element.get("animations", [])
            if not isinstance(animations, list):
                raise ProjectValidationError(f"{ewhere}.animations must be an array")
            animated_properties = set()
            for k, animation in enumerate(animations):
                awhere = f"{ewhere}.animations[{k}]"
                _keys(animation, ANIMATION_KEYS, ANIMATION_KEYS, awhere)
                prop = animation["property"]
                if not isinstance(prop, str) or prop not in ANIMATABLE:
                    raise ProjectValidationError(f"{awhere}.property must be one of {', '.join(sorted(ANIMATABLE))}")
                if prop in animated_properties:
                    raise ProjectValidationError(f"{awhere}: duplicate animation property {prop}")
                animated_properties.add(prop)
                _number(animation["from"], f"{awhere}.from")
                _number(animation["to"], f"{awhere}.to")
                _number(animation["start"], f"{awhere}.start", 0)
                _number(animation["duration"], f"{awhere}.duration", 0.001)
                if animation["start"] + animation["duration"] > scene["duration"] + 1e-6:
                    raise ProjectValidationError(f"{awhere} extends beyond its scene")
                if not isinstance(animation["easing"], str) or animation["easing"] not in EASINGS:
                    raise ProjectValidationError(f"{awhere}.easing must be one of {', '.join(sorted(EASINGS))}")
                if prop == "scale" and (animation["from"] <= 0 or animation["to"] <= 0):
                    raise ProjectValidationError(f"{awhere}: scale values must be positive")
                if prop == "opacity" and (not 0 <= animation["from"] <= 1 or not 0 <= animation["to"] <= 1):
                    raise ProjectValidationError(f"{awhere}: opacity values must be between 0 and 1")
    audio = data.get("audio", [])
    if not isinstance(audio, list):
        raise ProjectValidationError("audio must be an array")
    for i, track in enumerate(audio):
        where = f"audio[{i}]"
        required = {"kind", "source", "start", "duration", "volume", "loop"}
        _keys(track, AUDIO_KEYS, required, where)
        if not isinstance(track["kind"], str) or track["kind"] not in AUDIO_KINDS:
            raise ProjectValidationError(f"{where}.kind must be narration, music, or sfx")
        if not isinstance(track["source"], str) or not track["source"]:
            raise ProjectValidationError(f"{where}.source must be a non-empty path")
        _number(track["start"], f"{where}.start", 0)
        _number(track["duration"], f"{where}.duration", 0.001)
        if track["start"] >= p["duration"]:
            raise ProjectValidationError(f"{where}.start must be before project end")
        _number(track["volume"], f"{where}.volume", 0, 2)
        for fade in ("fade_in", "fade_out"):
            if fade in track:
                _number(track[fade], f"{where}.{fade}", 0)
                if track[fade] > track["duration"]:
                    raise ProjectValidationError(f"{where}.{fade} cannot exceed track duration")
        if not isinstance(track["loop"], bool):
            raise ProjectValidationError(f"{where}.loop must be boolean")
    return True
