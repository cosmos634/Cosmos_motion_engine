# Stage 6 — AI Project Generator

Stage 6 adds text-to-project generation. Gemini is the primary provider and Groq is the automatic backup. Both integrations use Python's standard library; no additional package is required.

## Configure providers

Add keys to the Termux shell environment. Keep keys private and never commit them.

```bash
export GEMINI_API_KEY="your_gemini_key"
export GROQ_API_KEY="your_groq_key"
export PIXABAY_API_KEY="your_pixabay_key"
```

Optional model overrides:

```bash
export GEMINI_MODEL="gemini-2.5-flash"
export GROQ_MODEL="openai/gpt-oss-120b"
```

## Automatic Pixabay visuals and design

AI generation uses a visual-design brief (hierarchy, spacing, contrast, restrained palette). When `PIXABAY_API_KEY` is configured, the generator searches Pixabay separately for each scene, using that scene's text to identify a subject where possible. It downloads the selected images through the Stage 5 Asset Manager, stores them beside the generated JSON under `assets/`, and adds one image per scene with a dark readability overlay.

For broad topics such as space, scenes without a specific subject rotate through different search themes (Earth, astronauts, galaxies, the Moon, nebulae, rockets, the Sun, and stars). Search results are de-duplicated across scenes when alternatives are available. If an individual search or download fails, the remaining scenes continue; generation still succeeds without stock backgrounds if Pixabay is unavailable. Use `--no-visuals` to skip stock-image search.

## Generate a project

```bash
python main.py generate \
  --prompt "Сделай динамичный рекламный ролик для Telegram-бота с темами Android" \
  --output projects/generated/themegram.json \
  --width 1080 --height 1920 --fps 30 --duration 20
```

The default provider mode tries Gemini first. If it is unavailable or returns invalid project JSON, the generator tries Groq. To select one provider explicitly, use `--provider gemini` or `--provider groq`.

Generated projects are validated before they are written. The model generates text and shape layers; optional stock backgrounds are added by the Stage 5 Asset Manager rather than by fabricated AI file paths.

## Reliability and safety

- AI output is treated as untrusted JSON data.
- No generated Python, shell, or other code is executed.
- The existing strict project validator checks every generated project.
- API calls use HTTPS, bounded response reads, and request timeouts.
- API keys are read from environment variables and are never written into project files.
- The renderer remains sequential; AI generation does not load media or video frames into memory.
- Provider failures trigger fallback in automatic mode. Explicit provider selection does not silently switch providers.

## Tests

```bash
python -m unittest discover -s tests -p 'test_ai.py' -v
python -m unittest discover -s tests -v
```
