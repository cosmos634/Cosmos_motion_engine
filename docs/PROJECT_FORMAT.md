# Cosmo Motion Engine project format

Project files are UTF-8 JSON. Unsupported keys are rejected to catch mistakes early.

## Stage 2 example

```json
{
  "version": 1,
  "project": {"width": 640, "height": 360, "fps": 24, "duration": 3, "background": "#101426"},
  "scenes": [{
    "id": "intro",
    "start": 0,
    "duration": 3,
    "elements": [{
      "type": "text",
      "text": "Hello Cosmo",
      "x": 40, "y": 100, "font_size": 32, "color": "#ffffff",
      "animations": [
        {"property": "x", "from": 0, "to": 40, "start": 0, "duration": 1, "easing": "ease_out"},
        {"property": "opacity", "from": 0, "to": 1, "start": 0, "duration": 1, "easing": "linear"}
      ]
    }]
  }]
}
```

## Project and scene rules

- `version` is 1.
- Width/height are positive integers up to 1920; FPS is a positive integer.
- Duration is in seconds. Scenes must fit inside the project duration.
- Scene `start` and animation `start` are relative to the project and scene respectively.
- Text, rect, image, and video elements are supported.
- Text fonts, image sources, video sources, and audio sources are relative to the JSON file directory and cannot escape it.
- Text font paths are relative to the JSON file's directory and cannot escape it.

## Animation tracks

Each element may contain an optional `animations` array. Each track has:
- `property`: x, y, scale, rotation, or opacity.
- `from` and `to`: numeric values.
- `start`: start time in seconds relative to its scene.
- `duration`: positive track duration in seconds.
- `easing`: linear, ease_in, ease_out, or ease_in_out.

Scale must remain positive. Opacity ranges from 0 to 1. Only one track per property is allowed on an element in this stage. Track values hold at the from/to values before and after the track, respectively.

## Scene transitions (Stage 4)

A scene may include an optional `transition_in` object. The incoming scene is composited over the previous active scene during the transition window, so arrange the scene start times to overlap by at least the transition duration. Keep scenes in the intended render order.

Supported transition types:
- `fade`: gradually changes the incoming scene opacity.
- `slide`: moves the incoming scene into frame.
- `wipe`: reveals the incoming scene with a directional mask.
- `zoom`: scales the incoming scene from 85% to its full size.

The `duration` is in seconds. The optional `direction` may be `left`, `right`, `up`, or `down`; it is used by slide and wipe. If omitted, direction defaults to `left`.

Example scene setting:

```json
"transition_in": {"type": "wipe", "duration": 0.6, "direction": "left"}
```

## Audio tracks (Stage 3)

Add an optional top-level audio array. Each track supports:
- kind: narration, music, or sfx
- source: audio file path relative to the project JSON file
- start: start offset in seconds
- duration: source segment duration in seconds
- volume: gain from 0.0 to 2.0
- fade_in / fade_out: optional fade lengths in seconds
- loop: true to loop the source when needed

Example:

```json
"audio": [
  {"kind": "narration", "source": "audio/voice_ru.wav", "start": 0, "duration": 3, "volume": 1.0, "fade_in": 0.1, "fade_out": 0.3, "loop": false},
  {"kind": "music", "source": "audio/music.mp3", "start": 0, "duration": 3, "volume": 0.22, "fade_in": 0.5, "fade_out": 0.8, "loop": true}
]
```

When audio tracks are present, the engine renders a temporary video, mixes audio with FFmpeg, and copies the video stream without re-encoding. Audio paths are restricted to the project directory.

## Install and run

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py validate projects/templates/stage1_demo.json
python main.py render projects/templates/stage1_demo.json --output output/stage3_demo.mp4
```

Frames are rendered sequentially and streamed to FFmpeg.


## Image layers (Stage 5.2)

Image elements use a project-relative `source` path and require `x` and `y`.

```json
{
  "type": "image",
  "source": "assets/cover.jpg",
  "x": 40, "y": 30,
  "width": 560, "height": 300,
  "fit": "cover",
  "animations": [
    {"property": "scale", "from": 0.9, "to": 1, "start": 0, "duration": 0.8, "easing": "ease_out"},
    {"property": "opacity", "from": 0, "to": 1, "start": 0, "duration": 0.5, "easing": "linear"}
  ]
}
```

- Width and height are optional but must be supplied together (1–1920).
- `fit` is `contain` (default), `cover`, or `stretch`.
- Without explicit dimensions, the image keeps its aspect ratio and is limited to 1920×1920.
- Image layers support x, y, scale, rotation, and opacity animation tracks.
- Image sources must exist inside the project directory. A bounded cache avoids decoding the same image for every frame.


## Video layers (Stage 5.3)

Video elements are decoded by a persistent FFmpeg process and composited one frame at a time. Frames are not loaded into memory as a full clip.

```json
{
  "type": "video",
  "id": "background_clip",
  "source": "assets/background.mp4",
  "x": 0, "y": 0,
  "width": 640, "height": 360,
  "fit": "cover",
  "start": 0,
  "duration": 3.5,
  "source_start": 1.2,
  "animations": [
    {"property": "opacity", "from": 0, "to": 1, "start": 0, "duration": 0.5, "easing": "linear"},
    {"property": "scale", "from": 1, "to": 1.08, "start": 0, "duration": 3.5, "easing": "ease_in_out"}
  ]
}
```

- `id` must be unique within its scene.
- `source` is relative to the project JSON and must stay inside its folder.
- `width` and `height` are required and range from 1 to 1920.
- `fit` supports `contain`, `cover`, and `stretch`.
- `start` is the clip's start time inside its scene (default 0).
- `duration` is optional; when set, it cannot exceed the scene's remaining duration.
- `source_start` seeks into the source file in seconds (default 0).
- Video supports x, y, scale, rotation, and opacity animations.
- Each video uses one FFmpeg decoder process, reads sequentially, and keeps only the current frame. Decoder processes are closed after rendering.
- Audio remains on the existing top-level audio timeline and is muxed after video encoding.
