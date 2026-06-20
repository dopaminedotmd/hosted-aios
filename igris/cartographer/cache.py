"""
Incremental caching layer for Repo-Cartographer.

Strategy:
  - Cache is a JSON file at <repo_root>/.igris/cartographer_cache.json
  - Each entry is keyed by relative file path
  - On rescan, compare file mtime against cached mtime
  - Only re-extract symbols for changed or new files
  - Remove entries for deleted files
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .models import FileEntry, RepoMap


CACHE_DIRNAME = ".igris"
CACHE_FILENAME = "cartographer_cache.json"


class CartographerCache:
    """Manages the persistent, incremental symbol cache."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.cache_dir = self.repo_root / CACHE_DIRNAME
        self.cache_path = self.cache_dir / CACHE_FILENAME
        self._data: dict[str, dict] = {}

    def load(self) -> None:
        """Load cache from disk. No-op if cache doesn't exist."""
        if self.cache_path.exists():
            raw = self.cache_path.read_text(encoding="utf-8")
            self._data = json.loads(raw)

    def save(self, repo_map: RepoMap) -> None:
        """Persist current RepoMap to cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_dict: dict[str, dict] = {}
        for path, entry in repo_map.files.items():
            cache_dict[path] = entry.model_dump(mode="json")
        self.cache_path.write_text(json.dumps(cache_dict, indent=2, default=str), encoding="utf-8")
        self._data = cache_dict

    def is_stale(self, relative_path: str, current_mtime: float) -> bool:
        """Check if a file needs re-extraction.

        Returns True if:
          - File is not in cache
          - File mtime differs from cached mtime
        """
        cached = self._data.get(relative_path)
        if cached is None:
            return True
        return abs(cached.get("mtime", 0) - current_mtime) > 0.01

    def get_cached(self, relative_path: str) -> Optional[FileEntry]:
        """Retrieve a cached entry if it exists and is fresh."""
        cached = self._data.get(relative_path)
        if cached is None:
            return None
        return FileEntry(**cached)

    def prune_deleted(self, current_paths: set[str]) -> int:
        """Remove cache entries for files that no longer exist. Returns count removed."""
        removed = 0
        for path in list(self._data.keys()):
            if path not in current_paths:
                del self._data[path]
                removed += 1
        return removed

    def clear(self) -> None:
        """Delete the entire cache."""
        self._data = {}
        if self.cache_path.exists():
            self.cache_path.unlink()
