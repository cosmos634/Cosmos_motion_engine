"""Sequential Pillow frame renderer with per-element and scene transitions."""
from functools import lru_cache
import subprocess
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
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


@lru_cache(maxsize=3)
def _load_image(path):
    with Image.open(path) as source:
        source.seek(0)
        source.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        return source.convert("RGBA").copy()


def _image_layer(element):
    image = _load_image(element["source"]).copy()
    if "width" not in element:
        return image
    size = (int(element["width"]), int(element["height"]))
    fit = element.get("fit", "contain")
    if fit == "cover":
        return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
    if fit == "stretch":
        return image.resize(size, Image.Resampling.LANCZOS)
    result = Image.new("RGBA", size, (0, 0, 0, 0))
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    result.alpha_composite(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return result


_VIDEO_READERS = {}


class _VideoReader:
    """One persistent FFmpeg decoder per video layer; keeps only a single raw frame."""
    def __init__(self, element, fps):
        self.width = int(element["width"])
        self.height = int(element["height"])
        fit = element.get("fit", "contain")
        if fit == "cover":
            vf = f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height},fps={fps}"
        elif fit == "stretch":
            vf = f"scale={self.width}:{self.height},fps={fps}"
        else:
            vf = f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,fps={fps}"
        command = ["ffmpeg", "-v", "error"]
        if element.get("source_start", 0):
            command += ["-ss", str(element["source_start"])]
        command += ["-i", element["source"], "-an", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1"]
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.frame_bytes = self.width * self.height * 4
        self.index = -1
        self.last_raw = None
        self.ended = False

    def _read_frame(self):
        chunks = []
        remaining = self.frame_bytes
        while remaining:
            chunk = self.process.stdout.read(remaining)
            if not chunk:
                self.ended = True
                return None
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def frame_at(self, index):
        if self.ended or index < self.index:
            return None
        raw = None
        while self.index < index:
            raw = self._read_frame()
            if raw is None:
                return None
            self.index += 1
            self.last_raw = raw
        if raw is None:
            raw = self.last_raw
        return Image.frombytes("RGBA", (self.width, self.height), raw)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        if self.process.stdout:
            self.process.stdout.close()


def close_video_readers():
    for reader in _VIDEO_READERS.values():
        reader.close()
    _VIDEO_READERS.clear()


def _video_layer(element, scene, scene_time, fps):
    key = (scene["id"], element["id"])
    reader = _VIDEO_READERS.get(key)
    if reader is None:
        reader = _VideoReader(element, fps)
        _VIDEO_READERS[key] = reader
    if scene_time < element.get("start", 0):
        return Image.new("RGBA", (element["width"], element["height"]), (0, 0, 0, 0))
    local_time = scene_time - element.get("start", 0)
    if "duration" in element and local_time >= element["duration"]:
        return Image.new("RGBA", (element["width"], element["height"]), (0, 0, 0, 0))
    frame = reader.frame_at(round(local_time * fps))
    return frame if frame is not None else Image.new("RGBA", (element["width"], element["height"]), (0, 0, 0, 0))


def _element_layer(element, font_path=None, scene=None, scene_time=0, fps=24):
    if element["type"] == "image":
        return _image_layer(element)
    if element["type"] == "video":
        return _video_layer(element, scene, scene_time, fps)
    color = parse_color(element["color"])
    if element["type"] == "rect":
        return Image.new("RGBA", (int(element["width"]), int(element["height"])), color)
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


def apply_transition(layer, transition, progress):
    """Apply an incoming scene transition to a full-frame RGBA layer."""
    if not transition:
        return layer
    width, height = layer.size
    progress = max(0.0, min(1.0, float(progress)))
    kind = transition["type"]
    direction = transition.get("direction", "left")

    if kind == "fade":
        result = layer.copy()
        alpha = result.getchannel("A").point(lambda value: round(value * progress))
        result.putalpha(alpha)
        return result

    if kind == "slide":
        offsets = {
            "left": (-round(width * (1 - progress)), 0),
            "right": (round(width * (1 - progress)), 0),
            "up": (0, -round(height * (1 - progress))),
            "down": (0, round(height * (1 - progress))),
        }
        result = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        result.alpha_composite(layer, offsets[direction])
        return result

    if kind == "wipe":
        mask = Image.new("L", layer.size, 0)
        draw = ImageDraw.Draw(mask)
        if direction == "left":
            draw.rectangle((0, 0, round(width * progress), height), fill=255)
        elif direction == "right":
            edge = round(width * (1 - progress))
            draw.rectangle((edge, 0, width, height), fill=255)
        elif direction == "up":
            edge = round(height * (1 - progress))
            draw.rectangle((0, 0, width, edge), fill=255)
        else:  # down
            draw.rectangle((0, round(height * (1 - progress)), width, height), fill=255)
        result = layer.copy()
        result.putalpha(ImageChops.multiply(result.getchannel("A"), mask))
        return result

    if kind == "zoom":
        scale = 0.85 + 0.15 * progress
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        resized = layer.resize(size, Image.Resampling.BICUBIC)
        result = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        result.alpha_composite(resized, ((width - size[0]) // 2, (height - size[1]) // 2))
        return result

    return layer


def render_frame(project, frame_index):
    settings = project["project"]
    width, height = settings["width"], settings["height"]
    timestamp = frame_index / settings["fps"]
    frame = Image.new("RGBA", (width, height), parse_color(settings["background"]))

    for scene in project["scenes"]:
        if not (scene["start"] <= timestamp < scene["start"] + scene["duration"]):
            continue

        scene_time = timestamp - scene["start"]
        scene_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        for element in scene["elements"]:
            animations = element.get("animations", [])
            x = animated_value(element["x"], animations, "x", scene_time)
            y = animated_value(element["y"], animations, "y", scene_time)
            scale = animated_value(1, animations, "scale", scene_time)
            rotation = animated_value(0, animations, "rotation", scene_time)
            opacity = animated_value(1, animations, "opacity", scene_time)

            layer = _element_layer(element, element.get("font"), scene, scene_time, settings["fps"])
            new_size = (max(1, round(layer.width * scale)), max(1, round(layer.height * scale)))
            if new_size != layer.size:
                layer = layer.resize(new_size, Image.Resampling.BICUBIC)
            if rotation:
                before = layer.size
                layer = layer.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
                x -= (layer.width - before[0]) / 2
                y -= (layer.height - before[1]) / 2
            if opacity < 1:
                alpha = layer.getchannel("A").point(lambda value: round(value * opacity))
                layer.putalpha(alpha)
            scene_layer.alpha_composite(layer, (round(x), round(y)))

        transition = scene.get("transition_in")
        if transition:
            progress = min(1.0, scene_time / transition["duration"])
            scene_layer = apply_transition(scene_layer, transition, progress)
        frame.alpha_composite(scene_layer)

    return frame.convert("RGB")
