"""Shared asset metadata models for Stage 5."""
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Asset:
    id: str
    provider: str
    media_type: str
    title: str
    url: str
    source_page: str
    author: str = ""
    author_url: str = ""
    thumbnail_url: str = ""
    license: str = "Check provider terms"
    width: int = 0
    height: int = 0
    duration: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
