"""
Igris Agent Skills — tools that agents can be equipped with.

Structure:
  skills/
  ├── caveman.py           Igris-native Caveman Ultra (surgical patches)
  ├── core/                Caveman skills (7 st)
  ├── superpowers/         Superpowers skills (14 st — TDD, code review, etc.)
  ├── security/            Cybersakerhetsskills (754 st)
  └── agents/              Agent-definitioner (3 st)

Skills are assigned based on agent rank:
  Level 0: read_file, write_file, terminal, search_files
  B-Rank:  + patch (Caveman Ultra)
  A-Rank:  + full tool access
"""

from .caveman import CavemanUltra, PatchResult, BatchResult, surgical_patch, create_test_hook

__all__ = [
    "CavemanUltra",
    "PatchResult",
    "BatchResult",
    "surgical_patch",
    "create_test_hook",
]
