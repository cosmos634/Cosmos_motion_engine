"""Sequential Pillow frame renderer with per-element animation."""
from PIL import Image, ImageDraw, ImageFont
from .animation import animated_value


def parse_color(value):
    named = {
        "black": (0, 0, 0, 255), "white": (255, 255, 255, 255),
        "red": (255, 0, 0, 255), "green": (0, 128, 0, 255),
        "blue": (0, 0, 255, 255), "yellow": (255, 255, 0, 255),
        "transparent": (0, 0, 0, 0),
    }
    if value.lower() in named:
        return named[value.lower()]
    raw = value.lstrip("#")
    if len(raw) == 6:
        raw += "ff"
    return tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4, 6))


def _element_layer(element, font_path=None):
    color = parse_color(element["color"])
    if element["type"] == "rect":
        layer = Image.new("RGBA", (int(element["width"]), int(element["height"])), color)
        return layer
    try:
        font = ImageFont.truetype(font_path, int(element["font_size"])) if font_path else ImageFont.load_default(size=int(element["font_size"]))
    except (OSError, TypeError):
        font = ImageFont.load_default()
    probe = Image.new("RGBA", (1, 1))
    box = ImageDraw.Draw(probe).textbbox((0, 0), element["text"], font=font)
    width, height = max(1, box[2] - box[0]), max(1, box[3] - box[1])
    layer = Image.new("RGBA", (width + 4, height + 4), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((2 - box[0], 2 - box[1]), element["text"], fill=color, font=font)
    return layer


def render_frame(project, frame_index):
    settings = project["project"]
    timestamp = frame_index / settings["fps"]
    frame = Image.new("RGBA", (settings["width"], settings["height"]), parse_color(settings["background"]))

    for scene in project["scenes"]:
        if not (scene["start"] <= timestamp < scene["start"] + scene["duration"]):
            continue
        scene_time = timestamp - scene["start"]
        for element in scene["elements"]:
            animations = element.get("animations", [])
            x = animated_value(element["x"], animations, "x", scene_time)
            y = animated_value(element["y"], animations, "y", scene_time)
            scale = animated_value(1, animations, "scale", scene_time)
            rotation = animated_value(0, animations, "rotation", scene_time)
            opacity = animated_value(1, animations, "opacity", scene_time)

            layer = _element_layer(element, element.get("font"))
            new_size = (max(1, round(layer.width * scale)), max(1, round(layer.height * scale)))
            if new_size != layer.size:
                layer = layer.resize(new_size, Image.Resampling.BICUBIC)
            if rotation:
                before = layer.size
                layer = layer.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
                x -= (layer.width - before[0]) / 2
                y -= (layer.height - before[1]) / 2
            if opacity < 1:
                alpha = layer.getchannel("A").point(lambda a: round(a * opacity))
                layer.putalpha(alpha)
            frame.alpha_composite(layer, (round(x), round(y)))
    return frame.convert("RGB")
