"""
Core data model and adapter interface for the multi-source OSINT pipeline.

Every source (Reddit, YouTube, GitHub, ...) implements the SourceAdapter
interface and returns results as UnifiedResult, so the runner and any
downstream analysis (e.g. feeding into an LLM) doesn't need to know the
per-platform schema.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UnifiedResult:
    source: str                     # e.g. "reddit", "github", "hackernews"
    result_id: str                  # platform-native id
    title: str
    url: str
    author: Optional[str] = None
    created_at: Optional[str] = None    # ISO 8601 string, kept as str for JSON-friendliness
    score: Optional[int] = None         # upvotes/stars/points, whatever the platform calls it
    text: Optional[str] = None          # body/description/selftext
    extra: dict = field(default_factory=dict)   # anything platform-specific worth keeping
    fetch_error: Optional[str] = None


class SourceAdapter(abc.ABC):
    """Every platform adapter implements this shape."""

    name: str = "unknown"

    @abc.abstractmethod
    def search(self, query: str, limit: int = 10) -> list[UnifiedResult]:
        """Search the platform for `query`, return up to `limit` results."""
        raise NotImplementedError

    def is_configured(self) -> bool:
        """
        Override if the adapter needs credentials (API keys, tokens).
        Return False to let the runner skip it gracefully instead of crashing.
        """
        return True


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"