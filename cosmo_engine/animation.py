"""Timeline interpolation and easing helpers."""


def ease(progress, name="linear"):
    t = max(0.0, min(1.0, float(progress)))
    if name == "ease_in":
        return t * t
    if name == "ease_out":
        return 1 - (1 - t) * (1 - t)
    if name == "ease_in_out":
        return 2 * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 2) / 2
    return t


def animated_value(base_value, animations, property_name, scene_time):
    value = float(base_value)
    for animation in animations or []:
        if animation["property"] != property_name:
            continue
        start = animation["start"]
        end = start + animation["duration"]
        if scene_time <= start:
            value = float(animation["from"])
        elif scene_time >= end:
            value = float(animation["to"])
        else:
            progress = (scene_time - start) / animation["duration"]
            t = ease(progress, animation["easing"])
            value = animation["from"] + (animation["to"] - animation["from"]) * t
    return value
