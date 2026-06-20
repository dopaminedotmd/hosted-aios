"""
Repo-Cartographer: main scanner.

Walks a directory tree, detects languages, extracts symbols,
and maintains an incremental cache for fast rescans.

Usage:
    cartographer = RepoCartographer("/path/to/repo")
    repo_map = cartographer.scan()          # full scan
    repo_map = cartographer.scan_incremental()  # only changed files
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .cache import CartographerCache
from .extractors import detect_language, extract_symbols, EXTENSION_MAP
from .models import FileEntry, RepoMap, Symbol


# Patterns/files to skip during scanning
SKIP_PATTERNS: set[str] = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "dist", "build", ".next", ".nuxt", ".cache", "target",
    ".igris",  # our own cache
    ".idea", ".vscode",  # IDE dirs (optional, but noisy)
}

SKIP_EXTENSIONS: set[str] = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".ttf", ".woff", ".woff2", ".eot",
    ".lock",  # package-lock.json, yarn.lock etc still scanned as text
}


class RepoCartographer:
    """Incremental codebase scanner and symbol mapper."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()
        if not self.repo_root.exists():
            raise FileNotFoundError(f"Repo root not found: {self.repo_root}")
        self.cache = CartographerCache(self.repo_root)
        self.cache.load()

    # ─── Public API ───────────────────────────────────────────────────────

    def scan(self, force_full: bool = False) -> RepoMap:
        """Scan the entire repo. Uses incremental cache unless force_full=True."""
        if force_full:
            self.cache.clear()
            return self._full_scan()

        return self._incremental_scan()

    def scan_incremental(self) -> RepoMap:
        """Scan only changed/new files. Falls back to full scan if no cache."""
        return self._incremental_scan()

    def scan_full(self) -> RepoMap:
        """Force a full re-scan, ignoring cache."""
        self.cache.clear()
        return self._full_scan()

    # ─── Internal ─────────────────────────────────────────────────────────

    def _full_scan(self) -> RepoMap:
        """Full scan: walk every file and extract symbols."""
        repo_map = RepoMap(repo_root=str(self.repo_root))
        current_paths: set[str] = set()

        for root, dirs, files in os.walk(self.repo_root):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS and not d.startswith(".")]

            for filename in files:
                filepath = Path(root) / filename
                rel_path = str(filepath.relative_to(self.repo_root))

                # Skip binary/extensions we don't care about
                ext = filepath.suffix.lower()
                if ext in SKIP_EXTENSIONS:
                    continue

                current_paths.add(rel_path)

                try:
                    entry = self._process_file(filepath, rel_path)
                    if entry:
                        repo_map.files[rel_path] = entry
                except (OSError, UnicodeDecodeError):
                    continue  # skip unreadable files

        # Finalize
        self._finalize_map(repo_map)
        self.cache.prune_deleted(current_paths)
        self.cache.save(repo_map)
        return repo_map

    def _incremental_scan(self) -> RepoMap:
        """Incremental scan: only process changed files, reuse cached entries."""
        repo_map = RepoMap(repo_root=str(self.repo_root))
        current_paths: set[str] = set()

        # If cache is empty, do full scan
        if not self.cache._data:
            return self._full_scan()

        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS and not d.startswith(".")]

            for filename in files:
                filepath = Path(root) / filename
                rel_path = str(filepath.relative_to(self.repo_root))

                ext = filepath.suffix.lower()
                if ext in SKIP_EXTENSIONS:
                    continue

                current_paths.add(rel_path)

                try:
                    mtime = filepath.stat().st_mtime

                    if self.cache.is_stale(rel_path, mtime):
                        # Changed or new — re-extract
                        entry = self._process_file(filepath, rel_path)
                        if entry:
                            repo_map.files[rel_path] = entry
                    else:
                        # Fresh — use cached
                        cached = self.cache.get_cached(rel_path)
                        if cached:
                            repo_map.files[rel_path] = cached
                except (OSError, UnicodeDecodeError):
                    continue

        # Prune deleted files from cache
        self.cache.prune_deleted(current_paths)

        # If incremental picked up nothing new but cache had data, restore all cached
        if not repo_map.files and self.cache._data:
            for path, data in self.cache._data.items():
                if path in current_paths:
                    repo_map.files[path] = FileEntry(**data)

        self._finalize_map(repo_map)
        self.cache.save(repo_map)
        return repo_map

    def _process_file(self, filepath: Path, rel_path: str) -> Optional[FileEntry]:
        """Read a file and extract its symbols."""
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

        language = detect_language(rel_path)
        stat = filepath.stat()

        symbols: list[Symbol] = []
        imports: list[str] = []
        exports: list[str] = []

        if language != "unknown":
            symbols = extract_symbols(source, language)
            imports = [s.name for s in symbols if s.kind == "import"]
            exports = [s.name for s in symbols if s.kind == "export"]

        return FileEntry(
            path=rel_path,
            language=language,
            mtime=stat.st_mtime,
            size_bytes=stat.st_size,
            symbols=symbols,
            imports=imports,
            exports=exports,
        )

    def _finalize_map(self, repo_map: RepoMap) -> None:
        """Compute aggregate stats for the map."""
        repo_map.total_files = len(repo_map.files)
        repo_map.total_symbols = sum(len(f.symbols) for f in repo_map.files.values())
        repo_map.languages = {}
        for entry in repo_map.files.values():
            lang = entry.language
            repo_map.languages[lang] = repo_map.languages.get(lang, 0) + 1
        repo_map.generated_at = datetime.now(timezone.utc)


# ─── Convenience function ────────────────────────────────────────────────────

def scan_repo(path: str | Path, incremental: bool = True) -> RepoMap:
    """One-liner to scan a repo."""
    cartographer = RepoCartographer(path)
    return cartographer.scan_incremental() if incremental else cartographer.scan_full()
