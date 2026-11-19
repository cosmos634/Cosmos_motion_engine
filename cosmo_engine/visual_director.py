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


STYLE_LABELS = {
    "cinematic_documentary": "ДОКУМЕНТАЛЬНЫЙ ФИЛЬМ",
    "modern_motion_graphics": "ТЕХНОЛОГИИ И ДИЗАЙН",
    "social_media": "КОРОТКО И ЯСНО",
    "historical_documentary": "ИСТОРИЧЕСКИЙ ОЧЕРК",
    "scientific_visualization": "НАУЧНЫЙ ОБЗОР",
}


def _fade(element, duration, target=1):
    element["animations"] = [{
        "property": "opacity", "from": 0, "to": target,
        "start": 0, "duration": duration, "easing": "ease_out",
    }]


def _add_scene_composition(elements, texts, width, height, accent, label, scene_number, scene_count, entrance):
    """Build a restrained editorial title card using existing rect/text layers."""
    title = texts[0]
    title_y = int(title.get("y", round(height * 0.56)))
    margin = max(8, round(width * 0.055))
    title_x = int(title.get("x", margin + 12))
    panel_x = max(0, min(title_x - max(12, round(width * 0.025)), width - margin))
    panel_width = max(1, width - margin - panel_x)

    text_bottom = title_y + int(title.get("font_size", 24) * 1.35)
    for item in texts[1:3]:
        item_y = int(item.get("y", text_bottom))
        text_bottom = max(text_bottom, item_y + int(item.get("font_size", 20) * 1.4))

    panel_top = max(0, title_y - max(24, round(height * 0.075)))
    panel_bottom = min(height, max(text_bottom + max(12, round(height * 0.025)), panel_top + max(72, round(height * 0.16))))
    panel_height = max(1, panel_bottom - panel_top)

    panel = {
        "type": "rect", "x": panel_x, "y": panel_top,
        "width": panel_width, "height": panel_height,
        "color": "#071321E8",
    }
    _fade(panel, entrance, 0.92)

    bar_width = max(3, round(width * 0.008))
    accent_bar = {
        "type": "rect", "x": panel_x, "y": panel_top,
        "width": bar_width, "height": panel_height, "color": accent,
    }
    _fade(accent_bar, entrance)

    additions = [panel, accent_bar]
    if height >= 480:
        small_size = max(12, min(28, round(height * 0.014)))
        top_pad = max(12, round(height * 0.018))
        kicker = {
            "type": "text", "text": label,
            "x": panel_x + max(14, round(width * 0.025)),
            "y": panel_top + top_pad,
            "font_size": small_size, "color": accent,
        }
        _fade(kicker, entrance)
        additions.append(kicker)

        counter_text = f"{scene_number:02d} / {scene_count:02d}"
        counter_width = max(64, round(width * 0.12))
        counter = {
            "type": "text", "text": counter_text,
            "x": max(panel_x + bar_width + 8, panel_x + panel_width - counter_width),
            "y": panel_top + top_pad,
            "font_size": small_size, "color": "#FFFFFF",
        }
        _fade(counter, entrance)
        additions.append(counter)

    insert_at = elements.index(title)
    if insert_at and elements[insert_at - 1].get("type") == "rect":
        previous = elements[insert_at - 1]
        if previous.get("color") == accent and previous.get("height", 0) <= max(4, round(height * 0.006)):
            insert_at -= 1
    elements[insert_at:insert_at] = additions


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
            base_x = image.get("x", 0) - round(width * (profile["zoom"] - 1) / 2)
            base_y = image.get("y", 0) - round(height * (profile["zoom"] - 1) / 2)
            _add_animation(image, "x", base_x, base_x + direction * profile["pan"], duration, "linear")
            _add_animation(image, "y", base_y, base_y - direction * round(profile["pan"] * 0.55), duration, "linear")

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
        _add_scene_composition(
            elements, texts, width, height, accent,
            STYLE_LABELS[style], scene_index + 1, len(project.get("scenes", [])), entrance,
        )
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
