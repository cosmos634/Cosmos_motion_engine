# Stage 6 — AI Project Generator

Stage 6 adds text-to-project generation. Gemini is the primary provider and Groq is the automatic backup. Both integrations use Python's standard library; no additional package is required.

## Configure providers

Add keys to the Termux shell environment. Keep keys private and never commit them.

```bash
export GEMINI_API_KEY="your_gemini_key"
export GROQ_API_KEY="your_groq_key"
```

Optional model overrides:

```bash
export GEMINI_MODEL="gemini-2.5-flash"
export GROQ_MODEL="openai/gpt-oss-120b"
```

## Automatic stock visuals and design

AI generation now uses a stronger visual-design brief (hierarchy, spacing, contrast, restrained palette). To add a real full-frame background automatically, configure at least one Stage 5 image provider:

```bash
export PEXELS_API_KEY="your_pexels_key"
# or PIXABAY_API_KEY / UNSPLASH_ACCESS_KEY
```

The generator searches a relevant stock image, downloads it through the Stage 5 Asset Manager, stores it beside the generated JSON under `assets/`, and adds it behind each scene with a dark readability overlay. If no provider key is configured or search fails, generation still succeeds without a background. Use `--no-visuals` to skip stock-image search.

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
