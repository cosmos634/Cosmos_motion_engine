"""Optional stock-photo enrichment for generated projects."""
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
    """Download one licensed-provider image and place it behind every scene.

    Returns a short status string. Missing provider keys never prevent rendering.
    """
    manager = AssetManager()
    if not manager.providers:
        return "No stock provider configured; set PEXELS_API_KEY, PIXABAY_API_KEY, or UNSPLASH_ACCESS_KEY."
    query = _search_query(prompt)
    errors = []
    for provider_name in ("pexels", "pixabay", "unsplash"):
        if provider_name not in manager.providers:
            continue
        try:
            results = manager.search(provider_name, query, "image", limit=5)
            if not results:
                continue
            asset = results[0]
            downloaded = manager.download(asset)
            asset_dir = Path(project_dir) / "assets"
            asset_dir.mkdir(parents=True, exist_ok=True)
            suffix = downloaded.suffix.lower() or ".jpg"
            target = asset_dir / f"ai_background{suffix}"
            shutil.copy2(downloaded, target)
            relative = target.relative_to(Path(project_dir)).as_posix()
            for scene in project["scenes"]:
                scene["elements"].insert(0, {
                    "type": "image", "source": relative,
                    "x": 0, "y": 0,
                    "width": project["project"]["width"],
                    "height": project["project"]["height"],
                    "fit": "cover",
                })
                scene["elements"].insert(1, {
                    "type": "rect", "x": 0, "y": 0,
                    "width": project["project"]["width"],
                    "height": project["project"]["height"],
                    "color": "#07111F99",
                })
            return f"Background image added from {provider_name}."
        except (AssetError, OSError, ValueError) as exc:
            errors.append(f"{provider_name}: {exc}")
    return "No stock image could be downloaded" + (": " + "; ".join(errors) if errors else ".")
