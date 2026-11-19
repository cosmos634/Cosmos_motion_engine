# Cosmo Motion Engine

A lightweight, JSON-driven video renderer designed for Python 3 and Android/Termux. This is an independent project inspired by timeline-based composition workflows; it is not the official Remotion framework.

## Development status

**Stage 1 — core rendering: complete.** Strict JSON validation, Pillow frame rendering, sequential FFmpeg encoding, CLI, and a demo project are implemented.

**Stage 2 — animation engine: implemented.** Timeline interpolation, easing, and animated position, scale, rotation, and opacity for text and rectangle layers are included.

**Stage 3 — audio engine: implemented and verified on the target Android device.** Narration, music, and sound-effect tracks can be mixed with volume, start offsets, fades, and optional looping.

**Stage 4 — transition engine: implemented, awaiting device verification.** Fade, slide, wipe, and zoom transitions are available between overlapping scenes.

**Stage 5 — Asset Manager: implemented and render-tested on Termux.** Provider adapters for Pexels, Pixabay, and Unsplash; HTTPS media downloads; size/type checks; local metadata caching; image layers; and sequential video layers are included.

**Stage 6 — AI Project Generator: initial implementation added.** Gemini is the primary provider and Groq is the automatic fallback. Text prompts become validated project JSON; generated code is never executed. See [docs/STAGE6_AI.md](docs/STAGE6_AI.md).

## Requirements

- Python 3.10+
- Pillow
- FFmpeg available on PATH

## Install (Termux)

```bash
pkg update
pkg install python ffmpeg
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Quick start

```bash
python main.py info
python main.py validate projects/templates/stage1_demo.json
python main.py render projects/templates/stage1_demo.json --output output/stage3_demo.mp4
```

The renderer processes one frame at a time and streams RGB bytes to FFmpeg. It does not retain the full video in memory.

## Asset Manager (Stage 5)

Set only the API key for the provider you want to use:

```bash
export PEXELS_API_KEY="your_key"
export PIXABAY_API_KEY="your_key"
export UNSPLASH_ACCESS_KEY="your_key"
```

Then use the Python API:

```python
from cosmo_engine.assets import AssetManager

assets = AssetManager()
results = assets.search("pexels", "mountain landscape", media_type="image", limit=5)
local_path = assets.download(results[0])
print(local_path)
```

See [docs/STAGE5_ASSETS.md](docs/STAGE5_ASSETS.md) for providers, cache layout, limits, and license notes. API keys must never be committed.

## Project format

See docs/PROJECT_FORMAT.md and the sample projects in projects/templates/.

Supported elements:
- text: text, position, font size, color, optional font path
- rect: filled rectangle, position, dimensions, color
- image: project-relative image source, fit mode, transforms, animations
- video: project-relative video source, clip timing, fit mode, transforms, animations

Audio is optional. Add audio tracks to the project JSON; see docs/PROJECT_FORMAT.md. Audio source files must be inside the project folder. Video decoding uses persistent FFmpeg readers and keeps only the current frame in memory.

Scene transitions are configured with the optional scene-level `transition_in` object. See docs/PROJECT_FORMAT.md for supported types and directions.

## Tests

```bash
python -m unittest discover -s tests -v
```

A successful local test suite does not replace a real FFmpeg render test on the target Android device.

## Safety and reliability

- AI-generated content is planned as data-only JSON; no AI output is executed as Python or shell.
- FFmpeg is launched with a fixed argument list (no shell).
- Project paths are resolved and checked before use.
- Asset downloads require HTTPS, enforce media MIME types and byte limits, and stream to disk.
- Rendering is sequential and memory-conscious.

## License

No license has been selected yet. Until one is added, do not assume the repository grants permission to reuse its code.


### Stage 5.3 — Video layers

Video elements are decoded sequentially with persistent FFmpeg readers and composited per frame. They support project-relative sources, clip start/duration, source seek, contain/cover/stretch fitting, transforms, opacity, and existing animation tracks. The encoder closes decoder processes after each render.


## AI Project Generator (Stage 6)

Configure one or both providers:

```bash
export GEMINI_API_KEY="your_gemini_key"
export GROQ_API_KEY="your_groq_key"
```

Generate a project (Gemini first, Groq fallback):

```bash
python main.py generate --prompt "Создай динамичный ролик о космосе" --output projects/generated/space.json
python main.py validate projects/generated/space.json
python main.py render projects/generated/space.json --output output/space.mp4
```

The first AI stage generates text and rectangle layers only. Real image, video, and audio assets are added through the Stage 5 workflow. No new Python package is required.


## Stage 8 — Visual Director

The Visual Director selects a visual style for each generated video and applies renderer-compatible motion design. Supported styles: cinematic documentary, modern motion graphics, social media, historical documentary, and scientific visualization. It adds slow Ken Burns movement to image layers, staggered title entrances, and restrained accent graphics without adding heavy runtime dependencies.

See [docs/STAGE8_VISUAL_DIRECTOR.md](docs/STAGE8_VISUAL_DIRECTOR.md).


## Stage 8.2 — Professional Composition

The Visual Director now builds editorial title cards from native rectangle and text layers: a translucent title panel, a style-colored vertical accent, a Russian section label, and a scene counter. These additions use the existing project schema and renderer, animate with the existing opacity track, and remain safe for sequential low-memory rendering.
