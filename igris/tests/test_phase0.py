"""
Tests for Repo-Cartographer — Phase 0.

Covers:
  - Language detection
  - Symbol extraction (Python, TS, Go)
  - Incremental caching
  - Full vs incremental scan
"""

import os
import time
from pathlib import Path

import pytest

from igris.cartographer import RepoCartographer, detect_language, extract_symbols
from igris.cartographer.models import FileEntry, RepoMap, Symbol
from igris.cartographer.scanner import SKIP_PATTERNS


# ─── Language detection ──────────────────────────────────────────────────────

class TestLanguageDetection:
    def test_python(self):
        assert detect_language("main.py") == "python"
        assert detect_language("src/module.pyi") == "python"

    def test_typescript(self):
        assert detect_language("App.tsx") == "typescript"
        assert detect_language("utils.ts") == "typescript"

    def test_javascript(self):
        assert detect_language("index.js") == "javascript"
        assert detect_language("lib.mjs") == "javascript"

    def test_go(self):
        assert detect_language("main.go") == "go"

    def test_unknown(self):
        assert detect_language("data.bin") == "unknown"
        assert detect_language("Makefile") == "unknown"


# ─── Python symbol extraction ────────────────────────────────────────────────

PYTHON_SOURCE = '''"""
Module docstring.
"""

import os
from pathlib import Path
from typing import Optional, List

MAX_RETRIES = 3

class UserProfile:
    """Represents a user."""

    def __init__(self, name: str, age: int = 0):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, {self.name}"

def get_user(user_id: int) -> Optional[UserProfile]:
    """Fetch a user by ID."""
    return None

@dataclass
class Config:
    host: str = "localhost"
'''


class TestPythonExtraction:
    def test_extract_functions(self):
        symbols = extract_symbols(PYTHON_SOURCE, "python")
        funcs = [s for s in symbols if s.kind == "function"]
        func_names = {f.name for f in funcs}
        assert "__init__" in func_names
        assert "greet" in func_names
        assert "get_user" in func_names

    def test_extract_classes(self):
        symbols = extract_symbols(PYTHON_SOURCE, "python")
        classes = [s for s in symbols if s.kind == "class"]
        class_names = {c.name for c in classes}
        assert "UserProfile" in class_names

    def test_extract_imports(self):
        symbols = extract_symbols(PYTHON_SOURCE, "python")
        imports = [s for s in symbols if s.kind == "import"]
        assert len(imports) >= 3  # os, pathlib, typing

    def test_extract_constants(self):
        symbols = extract_symbols(PYTHON_SOURCE, "python")
        constants = [s for s in symbols if s.kind == "constant"]
        const_names = {c.name for c in constants}
        assert "MAX_RETRIES" in const_names

    def test_extract_decorators(self):
        symbols = extract_symbols(PYTHON_SOURCE, "python")
        decorators = [s for s in symbols if s.kind == "decorator"]
        assert len(decorators) >= 1  # @dataclass


# ─── TypeScript symbol extraction ────────────────────────────────────────────

TYPESCRIPT_SOURCE = '''
import { useState } from "react";
import type { User } from "./types";

export interface UserProps {
  name: string;
  age: number;
}

export async function fetchUser(id: number): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}

export class UserService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async getUser(id: number): User {
    return fetchUser(id);
  }
}

const formatName = (user: User): string => {
  return user.name.toUpperCase();
};

export const API_URL = "https://api.example.com";
'''


class TestTypeScriptExtraction:
    def test_extract_functions(self):
        symbols = extract_symbols(TYPESCRIPT_SOURCE, "typescript")
        funcs = [s for s in symbols if s.kind == "function"]
        func_names = {f.name for f in funcs}
        assert "fetchUser" in func_names
        assert "formatName" in func_names

    def test_extract_classes(self):
        symbols = extract_symbols(TYPESCRIPT_SOURCE, "typescript")
        classes = [s for s in symbols if s.kind == "class"]
        class_names = {c.name for c in classes}
        assert "UserService" in class_names

    def test_extract_interfaces(self):
        symbols = extract_symbols(TYPESCRIPT_SOURCE, "typescript")
        types = [s for s in symbols if s.kind == "type"]
        type_names = {t.name for t in types}
        assert "UserProps" in type_names

    def test_extract_imports(self):
        symbols = extract_symbols(TYPESCRIPT_SOURCE, "typescript")
        imports = [s for s in symbols if s.kind == "import"]
        assert len(imports) >= 1  # react, ./types


# ─── Go symbol extraction ────────────────────────────────────────────────────

GO_SOURCE = '''
package main

import (
    "fmt"
    "net/http"
)

type Server struct {
    port int
}

func NewServer(port int) *Server {
    return &Server{port: port}
}

func (s *Server) Start() error {
    fmt.Printf("Starting on :%d\\n", s.port)
    return nil
}

func main() {
    srv := NewServer(8080)
    srv.Start()
}
'''


class TestGoExtraction:
    def test_extract_functions(self):
        symbols = extract_symbols(GO_SOURCE, "go")
        funcs = [s for s in symbols if s.kind == "function"]
        func_names = {f.name for f in funcs}
        assert "NewServer" in func_names
        assert "Server.Start" in func_names
        assert "main" in func_names

    def test_extract_types(self):
        symbols = extract_symbols(GO_SOURCE, "go")
        types = [s for s in symbols if s.kind == "class"]
        type_names = {t.name for t in types}
        assert "Server" in type_names

    def test_extract_imports(self):
        symbols = extract_symbols(GO_SOURCE, "go")
        imports = [s for s in symbols if s.kind == "import"]
        assert len(imports) >= 1  # fmt, net/http


# ─── Cartographer integration ────────────────────────────────────────────────

@pytest.fixture
def test_repo(tmp_path):
    """Create a minimal test repo with Python and TS files."""
    repo = tmp_path / "testrepo"
    repo.mkdir()

    # Python file
    (repo / "main.py").write_text(PYTHON_SOURCE, encoding="utf-8")

    # TypeScript file
    (repo / "components").mkdir()
    (repo / "components" / "User.tsx").write_text(TYPESCRIPT_SOURCE, encoding="utf-8")

    # Go file
    (repo / "server.go").write_text(GO_SOURCE, encoding="utf-8")

    # A file to be skipped
    (repo / "image.png").write_bytes(b"\x89PNG")

    return repo


class TestCartographer:
    def test_full_scan(self, test_repo):
        ctg = RepoCartographer(test_repo)
        repo_map = ctg.scan_full()

        assert repo_map.total_files >= 3  # main.py, User.tsx, server.go
        assert repo_map.total_symbols > 0
        assert "python" in repo_map.languages
        assert "typescript" in repo_map.languages
        assert "go" in repo_map.languages

        # Verify specific files (paths use OS separator)
        file_paths = list(repo_map.files.keys())
        assert any("main.py" in p for p in file_paths)
        assert any("User.tsx" in p for p in file_paths)
        assert any("server.go" in p for p in file_paths)

        # PNG should be skipped
        assert "image.png" not in repo_map.files

    def test_incremental_uses_cache(self, test_repo):
        ctg = RepoCartographer(test_repo)

        # First scan
        m1 = ctg.scan_full()
        assert m1.total_files >= 3

        # Second scan without changes — should use cache
        m2 = ctg.scan_incremental()
        assert m2.total_files == m1.total_files

        # Cache file should exist
        cache_path = test_repo / ".igris" / "cartographer_cache.json"
        assert cache_path.exists()

    def test_incremental_detects_changes(self, test_repo):
        ctg = RepoCartographer(test_repo)

        # Initial scan
        ctg.scan_full()

        # Modify a file — ensure mtime changes noticeably
        import time
        time.sleep(0.05)  # ensure distinct mtime
        py_file = test_repo / "main.py"
        py_file.write_text(PYTHON_SOURCE + "\n\ndef new_function():\n    pass\n", encoding="utf-8")

        # Force a fresh stat
        new_mtime = py_file.stat().st_mtime

        # Scan again — should pick up change
        m = ctg.scan_incremental()

        # Find main.py in the map (OS-specific separators)
        entry = None
        for path, e in m.files.items():
            if "main.py" in path:
                entry = e
                break

        assert entry is not None, "main.py not found in scan"

        # Should have the new function
        funcs = [s for s in entry.symbols if s.kind == "function"]
        assert "new_function" in {f.name for f in funcs}

    def test_symbol_model(self):
        sym = Symbol(name="test_func", kind="function", line=42, signature="def test_func(x: int)")
        assert sym.name == "test_func"
        assert sym.line == 42

    def test_file_entry_model(self):
        entry = FileEntry(
            path="src/main.py",
            language="python",
            mtime=1234567890.0,
            size_bytes=1024,
            symbols=[Symbol(name="f", kind="function", line=1)],
        )
        assert entry.language == "python"
        assert len(entry.symbols) == 1

    def test_repo_map_summary(self, test_repo):
        ctg = RepoCartographer(test_repo)
        m = ctg.scan_full()
        summary = m.summary()
        assert "files" in summary
        assert str(m.total_files) in summary

    def test_force_full_clears_cache(self, test_repo):
        ctg = RepoCartographer(test_repo)
        ctg.scan_full()

        # Force full re-scan
        m = ctg.scan(force_full=True)
        assert m.total_files >= 3

    def test_extract_symbols_unknown_language(self):
        result = extract_symbols("print('hello')", "unknown")
        assert result == []


# ─── Idle Detector tests ─────────────────────────────────────────────────────

class TestIdleDetector:
    def test_initial_state(self):
        from igris.idle_detector import IdleDetector, IdleState
        d = IdleDetector(threshold_s=60)
        assert d.state == IdleState.ACTIVE
        assert d.idle_seconds < 1.0
        assert not d.is_active_idle

    def test_mark_activity(self):
        from igris.idle_detector import IdleDetector, IdleState
        d = IdleDetector(threshold_s=60)
        time.sleep(0.1)
        d.mark_activity()
        assert d.idle_seconds < 1.0
        assert d.state == IdleState.ACTIVE

    def test_status_dict(self):
        from igris.idle_detector import IdleDetector
        d = IdleDetector(threshold_s=60)
        status = d.status_dict()
        assert status["state"] == "active"
        assert status["threshold_s"] == 60
        assert "idle_seconds" in status

    def test_custom_threshold(self):
        from igris.idle_detector import IdleDetector
        d = IdleDetector(threshold_s=30)
        assert d.threshold_s == 30

    def test_start_stop(self):
        from igris.idle_detector import IdleDetector
        d = IdleDetector(threshold_s=999)  # threshold high so it won't trigger during test
        d.start(check_interval_s=0.1)
        assert d._running
        d.stop()
        assert not d._running

    def test_triggers_idle(self):
        from igris.idle_detector import IdleDetector, IdleState
        triggered = []

        def on_idle():
            triggered.append(True)

        # Use a very short threshold
        d = IdleDetector(threshold_s=0.3, on_idle=on_idle)
        d.start(check_interval_s=0.1)

        # Wait for it to trigger
        time.sleep(0.6)

        assert len(triggered) >= 1
        assert d.state == IdleState.ACTIVE_IDLE
        d.stop()

    def test_wake_from_idle(self):
        from igris.idle_detector import IdleDetector, IdleState
        woken = []

        def on_wake():
            woken.append(True)

        d = IdleDetector(threshold_s=0.3, on_wake=on_wake)
        d.start(check_interval_s=0.1)

        # Let it go idle
        time.sleep(0.6)
        assert d.state == IdleState.ACTIVE_IDLE

        # Mark activity — should wake
        d.mark_activity()
        assert d.state == IdleState.ACTIVE
        assert len(woken) >= 1
        d.stop()
