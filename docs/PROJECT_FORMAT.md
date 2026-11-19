# Stage 1 JSON format

The project file is UTF-8 JSON. Stage 1 accepts only the keys documented here; unknown keys are rejected to catch typos early.

```json
{
  "version": 1,
  "project": {
    "width": 640,
    "height": 360,
    "fps": 24,
    "duration": 3,
    "background": "#101426"
  },
  "scenes": [
    {
      "id": "scene-1",
      "start": 0,
      "duration": 3,
      "elements": [
        {"type": "rect", "x": 10, "y": 10, "width": 100, "height": 60, "color": "#ffffff"},
        {"type": "text", "text": "Hello", "x": 30, "y": 90, "font_size": 28, "color": "#ffffff"}
      ]
    }
  ]
}
```

## Rules

- `version` must be 1.
- Width and height are positive integers up to 1920; FPS is a positive integer.
- Duration is positive, in seconds.
- Background and element colors accept basic names (black, white, red, green, blue, yellow, transparent) or hex `#RRGGBB` / `#RRGGBBAA`.
- Scene start and duration are in seconds; scenes must fit inside the project duration.
- Stage 1 elements: `text` and `rect`.
- A text element may specify a font file path relative to the JSON project's directory. Paths outside that directory are rejected.
- There are no animations, images, transitions, audio tracks, or AI generation in Stage 1.
