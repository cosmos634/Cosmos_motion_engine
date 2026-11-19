"""Per-scene Pixabay image enrichment for generated projects."""
from pathlib import Path
import re
import shutil

from .assets import AssetManager, AssetError


SCENE_KEYWORDS = (
    (("yer", "earth", "world", "земл"), "planet earth from space"),
    (("astronavt", "kosmonavt", "astronaut", "cosmonaut", "космонавт"), "astronaut in space"),
    (("oy", "moon", "lunar", "луна"), "moon surface space"),
    (("quyosh", "sun", "solar", "солнц"), "sun solar system"),
    (("mars", "марс"), "mars planet"),
    (("raketa", "rocket", "launch", "ракета"), "rocket launch space"),
    (("stansiya", "station", "iss", "станци"), "international space station"),
    (("galaktika", "galaxy", "milky way", "галактик"), "spiral galaxy milky way"),
    (("tumanlik", "nebula", "nebulae", "туманност"), "colorful nebula deep space"),
    (("yulduz", "star", "звезд"), "stars deep space"),
    (("sayyora", "planet", "планет"), "colorful planet in deep space"),
    (("o'rmon", "forest", "tabiat", "nature", "лес"), "cinematic nature forest"),
    (("dengiz", "ocean", "sea", "океан"), "cinematic ocean landscape"),
    (("shahar", "city", "urban", "город"), "cinematic modern city skyline"),
    (("texnolog", "technology", "robot", "ai", "future", "технолог"), "futuristic technology"),
)

SPACE_FALLBACKS = (
    "planet earth from space",
    "astronaut in space",
    "spiral galaxy milky way",
    "moon surface space",
    "colorful nebula deep space",
    "rocket launch space",
    "sun solar system",
    "stars deep space",
)


def _scene_text(scene):
    """Collect generated text content to match this scene's subject."""
    parts = []
    for element in scene.get("elements", []):
        if element.get("type") == "text":
            value = element.get("text", "")
            if isinstance(value, str):
                parts.append(value)
    return " ".join(parts).strip()


def _search_query(prompt, scene, index=0):
    """Prefer explicit scene subjects; rotate broad-topic fallbacks by scene."""
    scene_text = _scene_text(scene).lower()
    context = str(prompt).lower()

    # Specific words in the scene take priority over the broad video topic.
    for keywords, query in SCENE_KEYWORDS:
        if any(keyword in scene_text for keyword in keywords):
            return query

    is_space = any(word in context for word in (
        "kosmos", "koinot", "space", "planet", "galaxy", "universe", "космос", "вселен"
    ))
    if is_space:
        return SPACE_FALLBACKS[index % len(SPACE_FALLBACKS)]

    for keywords, query in SCENE_KEYWORDS:
        if any(keyword in context for keyword in keywords):
            return query

    words = re.findall(r"[a-zA-Z0-9']+", scene_text)
    if words:
        return " ".join(words[:4]) + " cinematic background"
    return "cinematic abstract background"


def add_visual_background(project, prompt, project_dir):
    """Download a distinct, scene-relevant Pixabay image for every scene.

    Search results are cached per query and asset IDs are de-duplicated across
    scenes when alternatives are available. A failed search for one scene does
    not prevent the remaining scenes or text-based project generation.
    """
    manager = AssetManager()
    if "pixabay" not in manager.providers:
        return "Pixabay is not configured; set PIXABAY_API_KEY."

    project_dir = Path(project_dir)
    asset_dir = project_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    width = project["project"]["width"]
    height = project["project"]["height"]
    searches = {}
    used_asset_ids = set()
    added = 0

    for index, scene in enumerate(project["scenes"]):
        query = _search_query(prompt, scene, index)
        try:
            if query not in searches:
                searches[query] = manager.search("pixabay", query, "image", limit=10)
            results = searches[query]
            if not results:
                continue
            asset = next((item for item in results if item.id not in used_asset_ids), results[0])
            used_asset_ids.add(asset.id)

            downloaded = manager.download(asset)
            suffix = downloaded.suffix.lower() or ".jpg"
            target = asset_dir / f"ai_background_scene_{index + 1}{suffix}"
            shutil.copy2(downloaded, target)
            relative = target.relative_to(project_dir).as_posix()

            # Remove prior auto-generated layers if this function is run again.
            scene["elements"] = [
                element for element in scene.get("elements", [])
                if not (
                    element.get("type") == "image"
                    and str(element.get("source", "")).startswith("assets/ai_background_scene_")
                )
            ]
            scene["elements"].insert(0, {
                "type": "image", "source": relative,
                "x": 0, "y": 0, "width": width, "height": height,
                "fit": "cover",
            })
            scene["elements"].insert(1, {
                "type": "rect", "x": 0, "y": 0,
                "width": width, "height": height,
                "color": "#07111F99",
            })
            added += 1
        except (AssetError, OSError, ValueError):
            continue

    if added == len(project["scenes"]):
        return f"Added Pixabay backgrounds to all {added} scenes."
    if added:
        return f"Added Pixabay backgrounds to {added}/{len(project['scenes'])} scenes."
    return "Pixabay images unavailable; continuing without stock backgrounds."
