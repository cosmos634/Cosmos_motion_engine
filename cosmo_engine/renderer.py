"""Sequential Pillow frame rendering for Stage 1."""
from PIL import Image, ImageDraw, ImageFont


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


def render_frame(project, frame_index):
    settings = project["project"]
    fps = settings["fps"]
    timestamp = frame_index / fps
    background = parse_color(settings["background"])
    image = Image.new("RGBA", (settings["width"], settings["height"]), background)
    draw = ImageDraw.Draw(image)

    for scene in project["scenes"]:
        if not (scene["start"] <= timestamp < scene["start"] + scene["duration"]):
            continue
        for element in scene["elements"]:
            color = parse_color(element["color"])
            if element["type"] == "rect":
                x, y = int(element["x"]), int(element["y"])
                draw.rectangle((x, y, x + int(element["width"]) - 1,
                                y + int(element["height"]) - 1), fill=color)
            elif element["type"] == "text":
                font_path = element.get("font")
                try:
                    font = ImageFont.truetype(font_path, int(element["font_size"])) if font_path else ImageFont.load_default(size=int(element["font_size"]))
                except (OSError, TypeError):
                    font = ImageFont.load_default()
                draw.text((int(element["x"]), int(element["y"])), element["text"],
                          fill=color, font=font)
    return image.convert("RGB")
