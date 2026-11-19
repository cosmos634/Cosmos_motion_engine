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
export GROQ_MODEL="llama-3.3-70b-versatile"
```

## Generate a project

```bash
python main.py generate \
  --prompt "Сделай динамичный рекламный ролик для Telegram-бота с темами Android" \
  --output projects/generated/themegram.json \
  --width 1080 --height 1920 --fps 30 --duration 20
```

The default provider mode tries Gemini first. If it is unavailable or returns invalid project JSON, the generator tries Groq. To select one provider explicitly, use `--provider gemini` or `--provider groq`.

Generated projects are validated before they are written. The model is instructed to generate only text and rectangle layers; external image/video/audio assets are deliberately not fabricated. Add real media using the Stage 5 Asset Manager and existing project format.

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
python -m unittest tests.test_ai -v
python -m unittest discover -s tests -v
```
