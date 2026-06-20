"""
Data models for Repo-Cartographer.

Represents the lightweight, cacheable map of a codebase:
  - files → symbols (functions, classes, imports)
  - dependency edges between files
  - incremental diff support
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Symbol(BaseModel):
    """A code symbol extracted from a source file."""

    name: str
    kind: str = Field(..., description="function, class, method, import, export, variable, type")
    line: int = Field(..., ge=1)
    signature: str = Field(default="", description="Full signature string")
    parent: Optional[str] = Field(default=None, description="Parent class/namespace")
    docstring: str = Field(default="")


class FileEntry(BaseModel):
    """Metadata and symbols for a single source file."""

    path: str = Field(..., description="Relative path from repo root")
    language: str
    mtime: float = Field(..., description="Last modification timestamp")
    size_bytes: int
    symbols: list[Symbol] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list, description="Imported module names/paths")
    exports: list[str] = Field(default_factory=list, description="Exported symbols")


class RepoMap(BaseModel):
    """Complete snapshot of a repository at a point in time."""

    repo_root: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    files: dict[str, FileEntry] = Field(default_factory=dict, description="path → FileEntry")
    total_files: int = 0
    total_symbols: int = 0
    languages: dict[str, int] = Field(default_factory=dict, description="language → file count")

    def summary(self) -> str:
        return (
            f"RepoMap: {self.total_files} files, {self.total_symbols} symbols, "
            f"{len(self.languages)} languages"
        )
