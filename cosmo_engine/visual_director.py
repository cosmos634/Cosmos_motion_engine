"""Deterministic visual direction for generated projects."""
STYLE_PROFILES = {
    "cinematic_documentary": {"accent": "#D9B36C", "zoom": 1.10, "pan": 16, "entrance": 0.85, "title_scale": 0.97},
    "modern_motion_graphics": {"accent": "#50D8FF", "zoom": 1.07, "pan": 24, "entrance": 0.62, "title_scale": 0.90},
    "social_media": {"accent": "#B6FF4A", "zoom": 1.13, "pan": 28, "entrance": 0.48, "title_scale": 0.88},
    "historical_documentary": {"accent": "#D7A56D", "zoom": 1.08, "pan": 12, "entrance": 0.95, "title_scale": 0.98},
    "scientific_visualization": {"accent": "#55E6D0", "zoom": 1.09, "pan": 18, "entrance": 0.72, "title_scale": 0.94},
}


def infer_visual_style(prompt):
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
    """Add style-specific camera drift, title entrances and accent graphics."""
    style = project.get("visual_style")
    if style not in STYLE_PROFILES:
        style = infer_visual_style(prompt)
    project["visual_style"] = style
    if project.get("visual_director_applied") is True:
        return style

    profile = STYLE_PROFILES[style]
    width = int(project["project"]["width"])
    height = int(project["project"]["height"])

    for scene_index, scene in enumerate(project.get("scenes", [])):
        duration = float(scene["duration"])
        entrance = min(profile["entrance"], max(0.12, duration * 0.28))
        elements = scene.setdefault("elements", [])

        images = [item for item in elements if item.get("type") == "image"]
        for image_index, image in enumerate(images):
            _add_animation(image, "scale", 1.0, profile["zoom"], duration, "ease_in_out")
            direction = -1 if (scene_index + image_index) % 2 else 1
            base_x = image.get("x", 0)
            _add_animation(image, "x", base_x, base_x + direction * profile["pan"], duration, "linear")

        texts = [item for item in elements if item.get("type") == "text"]
        if not texts:
            continue

        title = texts[0]
        title_y = title.get("y", round(height * 0.56))
        title["font_size"] = min(int(title.get("font_size", 64)), round(height * 0.075))
        _add_animation(title, "opacity", 0, 1, entrance)
        _add_animation(title, "y", title_y + round(height * 0.025), title_y, entrance)
        _add_animation(title, "scale", profile["title_scale"], 1.0, entrance)

        for index, item in enumerate(texts[1:], start=1):
            item_y = item.get("y", title_y + round(height * 0.065 * index))
            delay = min(entrance + 0.18, duration)
            _add_animation(item, "opacity", 0, 1, delay)
            _add_animation(item, "y", item_y + round(height * 0.012), item_y, delay)

        accent = profile["accent"]
        rule_width = max(44, round(width * 0.075))
        rule_height = max(3, round(height * 0.004))
        already_added = any(
            item.get("type") == "rect"
            and item.get("color") == accent
            and item.get("width") == rule_width
            and item.get("height") == rule_height
            for item in elements
        )
        if not already_added:
            title_x = max(24, min(int(title.get("x", width * 0.08)), width - 120))
            rule_y = max(12, int(title_y) - max(18, round(height * 0.018)))
            rule = {
                "type": "rect", "x": title_x, "y": rule_y,
                "width": rule_width, "height": rule_height, "color": accent,
                "animations": [{
                    "property": "opacity", "from": 0, "to": 1,
                    "start": 0, "duration": entrance, "easing": "ease_out",
                }],
            }
            elements.insert(elements.index(title), rule)

    project["visual_director_applied"] = True
    return style
