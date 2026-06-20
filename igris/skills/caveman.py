"""
Caveman Ultra — Surgical search/replace patch tool for Commander Igris.

Per Igris spec: "Kirurgiska sök/ersätt-patchar (aldrig hela filer)"

Features:
  - Exact-match find-and-replace in source files
  - Dry-run mode (preview changes without writing)
  - Automatic backup (.bak) before patching
  - Multi-file batch patching
  - Post-patch hook system (auto-run tests after patch)
  - Diff output for every change

Usage:
  from igris.skills.caveman import CavemanUltra

  caveman = CavemanUltra()
  result = caveman.patch("src/main.py", "old code", "new code")
  # Or batch:
  results = caveman.patch_batch([
      ("src/main.py", "old1", "new1"),
      ("src/utils.py", "old2", "new2"),
  ])
"""

from __future__ import annotations

import difflib
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class PatchResult:
    """Result of a single patch operation."""

    file_path: str
    success: bool
    old_string: str
    new_string: str
    occurrences_replaced: int = 0
    diff: str = ""
    error: str = ""
    backup_path: str = ""
    duration_ms: float = 0.0
    tests_passed: int = 0
    tests_failed: int = 0


@dataclass
class BatchResult:
    """Aggregate result of a batch patch operation."""

    results: list[PatchResult] = field(default_factory=list)
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    total_replacements: int = 0

    @property
    def all_success(self) -> bool:
        return self.failed == 0


class CavemanUltra:
    """Surgical code patching — never replaces entire files.

    Designed as a tool for B-Rank and A-Rank Igris agents.
    Level 0 agents cannot use this (they get read_file/write_file only).
    """

    def __init__(
        self,
        backup: bool = True,
        backup_dir: str | Path | None = None,
        post_hook: Optional[Callable[[list[str]], dict]] = None,
    ) -> None:
        self.backup_enabled = backup
        self.backup_dir = Path(backup_dir) if backup_dir else Path(".igris/backups")
        self.post_hook = post_hook
        self.patch_history: list[PatchResult] = []

        if self.backup_enabled:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    # ─── Single-file patch ────────────────────────────────────────────────

    def patch(
        self,
        file_path: str | Path,
        old_string: str,
        new_string: str,
        dry_run: bool = False,
        replace_all: bool = False,
    ) -> PatchResult:
        """Perform a single surgical patch on one file.

        Args:
            file_path: Path to the file to patch.
            old_string: Exact text to find and replace.
            new_string: Replacement text.
            dry_run: If True, only preview changes without writing.
            replace_all: If True, replace all occurrences. If False, replace only first.

        Returns:
            PatchResult with full details.
        """
        t0 = time.time()
        file_path = Path(file_path)

        if not file_path.exists():
            return PatchResult(
                file_path=str(file_path),
                success=False,
                old_string=old_string,
                new_string=new_string,
                error=f"File not found: {file_path}",
            )

        try:
            original = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return PatchResult(
                file_path=str(file_path),
                success=False,
                old_string=old_string,
                new_string=new_string,
                error=f"Cannot read file: {e}",
            )

        # Count occurrences
        count = original.count(old_string)
        if count == 0:
            return PatchResult(
                file_path=str(file_path),
                success=False,
                old_string=old_string,
                new_string=new_string,
                error=f"old_string not found in {file_path}",
            )

        # Apply replacement
        if replace_all:
            modified = original.replace(old_string, new_string)
            occurrences = count
        else:
            modified = original.replace(old_string, new_string, 1)
            occurrences = 1

        # Generate diff
        diff = self._generate_diff(original, modified, str(file_path))

        # Backup
        backup_path = ""
        if self.backup_enabled and not dry_run:
            backup_path = self._create_backup(file_path, original)

        # Write
        if not dry_run:
            file_path.write_text(modified, encoding="utf-8")

        result = PatchResult(
            file_path=str(file_path),
            success=True,
            old_string=old_string[:100],
            new_string=new_string[:100],
            occurrences_replaced=occurrences,
            diff=diff,
            backup_path=backup_path,
            duration_ms=(time.time() - t0) * 1000,
        )

        # Post-hook
        if self.post_hook and not dry_run:
            hook_result = self.post_hook([str(file_path)])
            result.tests_passed = hook_result.get("passed", 0)
            result.tests_failed = hook_result.get("failed", 0)

        self.patch_history.append(result)
        return result

    # ─── Batch patch ──────────────────────────────────────────────────────

    def patch_batch(
        self,
        patches: list[tuple[str, str, str]],
        dry_run: bool = False,
        stop_on_first_failure: bool = False,
    ) -> BatchResult:
        """Apply multiple patches across files.

        Args:
            patches: List of (file_path, old_string, new_string) tuples.
            dry_run: Preview only.
            stop_on_first_failure: Abort batch on first error.

        Returns:
            BatchResult with per-file details.
        """
        batch = BatchResult()
        batch.total_files = len(set(p[0] for p in patches))

        for file_path, old, new in patches:
            result = self.patch(file_path, old, new, dry_run=dry_run)
            batch.results.append(result)

            if result.success:
                batch.successful += 1
                batch.total_replacements += result.occurrences_replaced
            else:
                batch.failed += 1
                if stop_on_first_failure:
                    break

        return batch

    # ─── Preview / Dry-run ────────────────────────────────────────────────

    def preview(self, file_path: str | Path, old_string: str, new_string: str) -> str:
        """Preview what a patch would do without writing. Returns the diff."""
        result = self.patch(file_path, old_string, new_string, dry_run=True)
        return result.diff

    # ─── Rollback ─────────────────────────────────────────────────────────

    def rollback_last(self) -> bool:
        """Rollback the most recent successful patch."""
        for result in reversed(self.patch_history):
            if result.success and result.backup_path:
                return self._rollback(result)
        return False

    def rollback_all(self) -> int:
        """Rollback all patches in reverse order. Returns count rolled back."""
        count = 0
        for result in reversed(self.patch_history):
            if result.success and result.backup_path:
                if self._rollback(result):
                    count += 1
        return count

    # ─── Helpers ──────────────────────────────────────────────────────────

    def _generate_diff(self, original: str, modified: str, filename: str) -> str:
        """Generate a unified diff."""
        diff_lines = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
        return "".join(diff_lines)

    def _create_backup(self, file_path: Path, content: str) -> str:
        """Create a timestamped backup of the file."""
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{ts}.bak"
        backup_path = self.backup_dir / backup_name
        backup_path.write_text(content, encoding="utf-8")
        return str(backup_path)

    def _rollback(self, result: PatchResult) -> bool:
        """Restore a file from backup."""
        backup_path = Path(result.backup_path)
        target = Path(result.file_path)
        if backup_path.exists():
            content = backup_path.read_text(encoding="utf-8")
            target.write_text(content, encoding="utf-8")
            return True
        return False


# ─── Post-Write Hook factory ─────────────────────────────────────────────────

def create_test_hook(test_command: str = "pytest", cwd: str | Path | None = None) -> Callable:
    """Create a post-patch hook that runs tests.

    Usage:
        hook = create_test_hook("pytest tests/ -q", cwd="myproject")
        caveman = CavemanUltra(post_hook=hook)
    """

    def run_tests(files: list[str]) -> dict:
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(cwd) if cwd else None,
                timeout=120,
            )
            # Parse pytest-style output for passed/failed counts
            passed = 0
            failed = 0
            for line in result.stdout.split("\n") + result.stderr.split("\n"):
                if "passed" in line.lower():
                    import re
                    m = re.search(r"(\d+)\s+passed", line)
                    if m:
                        passed = int(m.group(1))
                    m = re.search(r"(\d+)\s+failed", line)
                    if m:
                        failed = int(m.group(1))

            return {
                "passed": passed,
                "failed": failed,
                "exit_code": result.returncode,
                "output": result.stdout[:500] + result.stderr[:500],
            }
        except Exception as e:
            return {"passed": 0, "failed": 0, "error": str(e)}

    return run_tests


# ─── Convenience ─────────────────────────────────────────────────────────────

def surgical_patch(file_path: str, old_string: str, new_string: str) -> PatchResult:
    """One-liner for a quick surgical patch."""
    caveman = CavemanUltra()
    return caveman.patch(file_path, old_string, new_string)
