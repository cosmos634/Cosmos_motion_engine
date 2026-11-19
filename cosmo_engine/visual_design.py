"""Optional Pixabay stock-photo enrichment for generated projects."""
from pathlib import Path
import shutil

from .assets import AssetManager, AssetError


def _search_query(prompt):
    text = prompt.lower()
    if any(word in text for word in ("kosmos", "space", "planet", "galaxy", "koinot", "sayyora")):
        return "deep space nebula planet stars"
    if any(word in text for word in ("tabiat", "nature", "forest", "ocean", "dengiz")):
        return "cinematic nature landscape"
    if any(word in text for word in ("texnolog", "technology", "ai", "robot", "future")):
        return "abstract futuristic technology"
    if any(word in text for word in ("shahar", "city", "urban")):
        return "cinematic modern city skyline"
    return "cinematic abstract background"


def add_visual_background(project, prompt, project_dir):
    """Download a Pixabay image and place it behind every scene.

    Pixabay is the only provider used here. A missing key or failed request
    never prevents text-based project generation.
    """
    manager = AssetManager()
    if "pixabay" not in manager.providers:
        return "Pixabay is not configured; set PIXABAY_API_KEY."
    query = _search_query(prompt)
    try:
        results = manager.search("pixabay", query, "image", limit=5)
        if not results:
            return f"No Pixabay images found for: {query}"
        downloaded = manager.download(results[0])
        project_dir = Path(project_dir)
        asset_dir = project_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        suffix = downloaded.suffix.lower() or ".jpg"
        target = asset_dir / f"ai_background{suffix}"
        shutil.copy2(downloaded, target)
        relative = target.relative_to(project_dir).as_posix()
        width = project["project"]["width"]
        height = project["project"]["height"]
        for scene in project["scenes"]:
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
        return "Background image added from Pixabay."
    except (AssetError, OSError, ValueError) as exc:
        return f"Pixabay image unavailable: {exc}"
