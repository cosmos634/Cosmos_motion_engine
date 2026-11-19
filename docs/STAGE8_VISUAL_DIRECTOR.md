# Stage 8 — Visual Director

Stage 8 adds a deterministic Visual Director between AI project generation and
validation/rendering. It does not execute generated code and does not add a
runtime dependency.

## Visual styles

The AI may choose one validated style:

- `cinematic_documentary`
- `modern_motion_graphics`
- `social_media`
- `historical_documentary`
- `scientific_visualization`

If the field is absent or invalid, the local director infers a safe default
from the prompt. The style controls accent color, camera drift, background
zoom, and title entrance timing.

## Motion behavior

- Stock image backgrounds receive slow Ken Burns scale and horizontal pan.
- The headline receives opacity, vertical entrance, and subtle scale animation.
- Supporting text enters slightly later.
- A single animated accent rule provides a consistent editorial anchor.
- Applying the director twice does not duplicate its accent layer or motion
  properties.

The feature uses existing animation properties and the current Pillow renderer,
so old project files remain valid. It is designed for sequential rendering on
Android/Termux and does not retain full videos in memory.

## Verify

```bash
python -m unittest discover -s tests -v
python main.py generate --prompt "Документальный ролик о тайнах космоса"
python main.py validate projects/generated/project.json
python main.py render projects/generated/project.json
```


## Stage 8.2 — Professional composition

Each scene containing text receives a restrained editorial composition:

- A translucent dark panel sized around the headline and supporting copy
- A vertical accent bar using the selected visual style's accent color
- A Russian style label (for example, НАУЧНЫЙ ОБЗОР)
- A sequential scene counter such as 01 / 04
- Short opacity entrances using the existing animation engine

All added layers are existing rect and text element types. No renderer changes, new dependencies, or additional media decoding are required. The Visual Director's applied flag prevents duplicate composition on repeated calls.
