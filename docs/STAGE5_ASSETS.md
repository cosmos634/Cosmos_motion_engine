# Stage 5 — Asset Manager

The Asset Manager is independent from the renderer. It searches public stock-media catalogs, downloads selected assets, and stores source/creator/license metadata beside a local cache copy.

## Providers

| Provider | Images | Videos | Environment variable |
|---|---:|---:|---|
| Pexels | Yes | Yes | `PEXELS_API_KEY` |
| Pixabay | Yes | Yes | `PIXABAY_API_KEY` |
| Unsplash | Yes | No | `UNSPLASH_ACCESS_KEY` |

API keys are optional until that provider is used. Keys are read from environment variables and must not be committed to the repository. Provider terms, attribution requirements, API quotas, and download permissions still apply; the engine records source metadata but does not grant a license.

## Python usage

```python
from cosmo_engine.assets import AssetManager

manager = AssetManager(cache_dir=".cosmo_cache")
results = manager.search("pexels", "mountain landscape", media_type="image", limit=5)
for index, asset in enumerate(results):
    print(index, asset.title, asset.author, asset.source_page)

local_file = manager.download(results[0])
print("Saved:", local_file)
print("Metadata:", manager.cached_assets())
```

Set a provider key in the current Termux session before running Python:

```bash
export PEXELS_API_KEY="your_key"
export PIXABAY_API_KEY="your_key"
export UNSPLASH_ACCESS_KEY="your_key"
```

Do not paste API keys into source files, project JSON, screenshots, or Git commits.

## Cache layout

```text
.cosmo_cache/
  images/
  videos/
  metadata/
```

Downloads are restricted to HTTPS, checked against expected media MIME types, streamed in chunks, and limited to 20 MiB per image and 100 MiB per video by default. Metadata records provider, source page, creator, license label, dimensions, duration, and local file path.

## Scope boundary

Stage 5 currently provides discovery, download, and metadata caching. It does not yet add image/video elements to the project JSON or renderer; that integration follows after this module is verified on-device.
