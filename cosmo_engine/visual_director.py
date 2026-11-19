"""Deterministic visual direction applied to AI-generated scenes.

The module upgrades static layouts with restrained, scene-aware motion while
keeping the project JSON renderer-compatible and safe for low-memory devices.
"""
import re


STYLE_PROFILES = {
    "cinematic_documentary": {
        "accent": "#D9B36C", "zoom": 1.10, "pan": 16, "entrance": 0.85,
        "title_scale": 0.97, "overlay": "#07111F99",
    },
    "modern_motion_graphics": {
        "accent": "#50D8FF", "zoom": 1.07, "pan": 24, "entrance": 0.62,
        "title_scale": 0.90, "overlay": "#07111F88",
    },
    "social_media": {
        "accent": "#B6FF4A", "zoom": 1.13, "pan": 28, "entrance": 0.48,
        "title_scale": 0.88, "overlay": "#07111F99",
    },
    "historical_documentary": {
        "accent": "#D7A56D", "zoom": 1.08, "pan": 12, "entrance": 0.95,
        "title_scale": 0.98, "overlay": "#17100BCC",
    },
    "scientific_visualization": {
        "accent": "#55E6D0", "zoom": 1.09, "pan": 18, "entrance": 0.72,
        "title_scale": 0.94, "overlay": "#06152199",
    },
}
STYLE_NAMES = set(STYLE_PROFILES)


def infer_visual_style(prompt):
    """Choose a useful visual style from the brief when AI omitted one."""
    text = str(prompt).lower()
    if any(word in text for word in ("истор", "history", "historical", "tarix", "qadim")):
        return "historical_documentary"
    if any(word in text for word in ("наук", "science", "scientific", "физик", "space", "космос", "ilm")):
        return "scientific_visualization"
    if any(word in text for word in ("shorts", "reels", "tiktok", "мотивац", "motiv", "short video")):
        return "social_media"
    if any(word in text for word in ("технолог", "technology", "design", "motion graphics", "ai", "нейросет")):
        return "modern_motion_graphics"
    return "cinematic_documentary"


def _add_animation(element, prop, start_value, end_value, duration, easing="ease_out"):
    animations = element.setdefault("animations", [])
    if any(item.get("property") == prop for item in animations):
        return
    animations.append({
        "property": prop, "from": start_value, "to": end_value,
        "start": 0, "duration": duration, "easing": easing,
    })


def apply_visual_direction(project, prompt=""):
    """Apply a visual style and tasteful motion to every scene in-place."""
    style = project.get("visual_style")
    if style not in STYLE_PROFILES:
        style = infer_visual_style(prompt)
    project["visual_style"] = style
    profile = STYLE_PROFILES[style]
    settings = project["project"]
    width, height = int(settings["width"]), int(settings["height"])

    for scene_index, scene in enumerate(project.get("scenes", [])):
        duration = float(scene["duration"])
        entrance = min(profile["entrance"], max(0.12, duration * 0.28))
        elements = scene.setdefault("elements", [])

        # Slow Ken Burns movement turns a stock still into a moving shot.
        image_layers = [item for item in elements if item.get("type") == "image"]
        for image_index, image in enumerate(image_layers):
            _add_animation(image, "scale", 1.0, profile["zoom"], duration, "ease_in_out")
            direction = -1 if (scene_index + image_index) % 2 else 1
            _add_animation(image, "x", image.get("x", 0), image.get("x", 0) + direction * profile["pan"], duration, "linear")

        text_layers = [item for item in elements if item.get("type") == "text"]
        if not text_layers:
            continue

        # The first text layer is the headline; later layers are supporting copy.
        title = text_layers[0]
        title_y = title.get("y", round(height * 0.56))
        title["font_size"] = min(int(title.get("font_size", 64)), round(height * 0.075))
        _add_animation(title, "opacity", 0, 1, entrance)
        _add_animation(title, "y", title_y + round(height * 0.025), title_y, entrance)
        _add_animation(title, "scale", profile["title_scale"], 1.0, entrance, "ease_out")

        for index, item in enumerate(text_layers[1:], start=1):
            item_y = item.get("y", title_y + round(height * 0.065 * index))
            _add_animation(item, "opacity", 0, 1, min(entrance + 0.18, duration))
            _add_animation(item, "y", item_y + round(height * 0.012), item_y, min(entrance + 0.18, duration))

        # A single accent rule gives the headline a consistent editorial anchor.
        # Mark it so applying this function twice never duplicates the layer.
        marker = f"cosmo_accent_{scene.get('id', scene_index)}"
        if not any(item.get("id") == marker for item in elements):
            title_x = max(24, min(int(title.get("x", width * 0.08)), width - 120))
            rule_y = max(12, int(title_y) - max(18, round(height * 0.018)))
            rule = {
                "type": "rect", "id": marker,
                "x": title_x, "y": rule_y, "width": max(44, round(width * 0.075)),
                "height": max(3, round(height * 0.004)),
                "color": profile["accent"],
                "animations": [{
                    "property": "opacity", "from": 0, "to": 1,
                    "start": 0, "duration": entrance, "easing": "ease_out",
                }],
            }
            # Keep it above the background but below the text.
            first_text_index = elements.index(title)
            elements.insert(first_text_index, rule)

    return style
