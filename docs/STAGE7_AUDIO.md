# Stage 7 — Russian Audio Engine

Stage 7 adds automatic Russian narration plus an original ambient soundtrack and scene-transition effects.

## Install

```bash
pip install -r requirements.txt
```

Edge TTS uses Microsoft's online text-to-speech service, so narration requires an internet connection during generation. The default voice is ru-RU-DmitryNeural. Select a female voice with:

```bash
export COSMO_TTS_VOICE="ru-RU-SvetlanaNeural"
```

## Generate

```bash
python main.py generate \
  --prompt "O'zbek tilida koinot haqida 20 soniyalik video yarat" \
  --output projects/generated/space_test.json \
  --width 320 --height 180 --fps 12 --duration 20
```

The AI is instructed to produce all visible text and the narration script in Russian (ru-RU), regardless of the prompt language. The engine then creates Russian narration, locally synthesized ambient music, and a soft whoosh at scene changes. FFmpeg mixes the tracks into the final MP4.

Music and effects are original procedural audio generated locally; no stock-audio API or extra audio key is required. If Edge TTS is offline or unavailable, generation continues with music and effects and prints a warning. Use --no-audio to skip audio generation.

Render as usual:

```bash
python main.py render projects/generated/space_test.json
```

Audio assets are saved under projects/generated/assets/audio/.
