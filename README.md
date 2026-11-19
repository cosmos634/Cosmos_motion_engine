# Cosmo Motion Engine

A lightweight, JSON-driven video renderer designed for Python 3 and Android/Termux. This is an independent project inspired by timeline-based composition workflows; it is not the official Remotion framework.

## Development status

**Stage 1 — core rendering: complete.** Strict JSON validation, Pillow frame rendering, sequential FFmpeg encoding, CLI, and a demo project are implemented.

**Stage 2 — animation engine: implemented, awaiting device verification.** Timeline interpolation, easing, and animated position, scale, rotation, and opacity for text and rectangle layers are included.

Later stages will add timeline animations, transitions, audio, asset providers, and Gemini/Groq project generation. These features are not implemented yet.

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
python main.py render projects/templates/stage1_demo.json --output output/stage2_demo.mp4
```

The renderer processes one frame at a time and streams RGB bytes to FFmpeg. It does not retain the full video in memory.

## Stage 1 project format

See docs/PROJECT_FORMAT.md and the sample project at projects/templates/stage1_demo.json.

Supported elements:
- text: text, position, font size, color, optional font path
- rect: filled rectangle, position, dimensions, color

Unsupported keys and element types are rejected during validation. Stage 1 intentionally does not yet implement animation, images, transitions, or audio.

## Tests

```bash
python -m unittest discover -s tests -v
```

A successful local test suite does not replace a real FFmpeg render test on the target Android device.

## Safety and reliability

- AI-generated content is planned as data-only JSON; no AI output is executed as Python or shell.
- FFmpeg is launched with a fixed argument list (no shell).
- Project paths are resolved and checked before use.
- Rendering is sequential and memory-conscious.

## License

No license has been selected yet. Until one is added, do not assume the repository grants permission to reuse its code.