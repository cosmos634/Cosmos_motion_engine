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
- Text and rect elements are supported. Images, video, audio and transitions are not implemented yet.
- Text font paths are relative to the JSON file's directory and cannot escape it.

## Animation tracks

Each element may contain an optional `animations` array. Each track has:
- `property`: x, y, scale, rotation, or opacity.
- `from` and `to`: numeric values.
- `start`: start time in seconds relative to its scene.
- `duration`: positive track duration in seconds.
- `easing`: linear, ease_in, ease_out, or ease_in_out.

Scale must remain positive. Opacity ranges from 0 to 1. Only one track per property is allowed on an element in this stage. Track values hold at the from/to values before and after the track, respectively.

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
