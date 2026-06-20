"""
Per-language symbol extractors for Repo-Cartographer.

Uses regex-based extraction (no heavy dependencies).
Supported languages: Python, TypeScript/JavaScript, Go.

Each extractor returns a list of Symbol objects from source text.
"""

from __future__ import annotations

import re

from .models import Symbol


# ─── Language detection ──────────────────────────────────────────────────────

EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".toml": "toml",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
}


def detect_language(filepath: str) -> str:
    """Detect language from file extension. Returns 'unknown' if not mapped."""
    import os
    ext = os.path.splitext(filepath)[1].lower()
    return EXTENSION_MAP.get(ext, "unknown")


# ─── Python extractor ────────────────────────────────────────────────────────

PYTHON_PATTERNS: list[tuple[str, str]] = [
    # function def (top-level or method)
    (r"^\s*def\s+(\w+)\s*\((.*?)\)(\s*->\s*\S+)?\s*:", "function"),
    # class def
    (r"^\s*class\s+(\w+)\s*(\(.*?\))?\s*:", "class"),
    # import X
    (r"^\s*import\s+([\w.]+)", "import"),
    # from X import Y
    (r"^\s*from\s+([\w.]+)\s+import\s+([\w,\s*]+)", "import"),
    # decorated function/class
    (r"^\s*@\w+", "decorator"),
    # assignment to constant (uppercase)
    (r"^\s*([A-Z_][A-Z0-9_]*)\s*[:=]\s*", "constant"),
]


def extract_python(source: str) -> list[Symbol]:
    """Extract symbols from Python source code."""
    symbols: list[Symbol] = []
    lines = source.split("\n")

    for i, line in enumerate(lines, 1):
        # Skip comments and empty lines
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Try function/class patterns first (take priority)
        func_match = re.match(r"^\s*def\s+(\w+)\s*\(([^)]*)\)", line)
        if func_match:
            symbols.append(Symbol(
                name=func_match.group(1),
                kind="function",
                line=i,
                signature=f"def {func_match.group(1)}({func_match.group(2)})",
            ))
            continue

        class_match = re.match(r"^\s*class\s+(\w+)", line)
        if class_match:
            # Find parent class if present
            parent_match = re.match(r"^\s*class\s+\w+\s*\((\w+)", line)
            parent = parent_match.group(1) if parent_match else None
            symbols.append(Symbol(
                name=class_match.group(1),
                kind="class",
                line=i,
                signature=f"class {class_match.group(1)}",
                parent=parent,
            ))
            continue

        # Import statements
        import_match = re.match(r"^\s*import\s+([\w.]+)", line)
        if import_match:
            symbols.append(Symbol(
                name=import_match.group(1),
                kind="import",
                line=i,
            ))
            continue

        from_match = re.match(r"^\s*from\s+([\w.]+)\s+import\s+(.+)", line)
        if from_match:
            imported = from_match.group(2).strip()
            symbols.append(Symbol(
                name=f"{from_match.group(1)}.{imported}",
                kind="import",
                line=i,
            ))
            continue

        # Decorator
        if re.match(r"^\s*@\w+", line):
            symbols.append(Symbol(
                name=stripped,
                kind="decorator",
                line=i,
            ))
            continue

        # Constants (UPPER_CASE assignments)
        const_match = re.match(r"^\s*([A-Z_][A-Z0-9_]*)\s*[:=]\s*", line)
        if const_match:
            symbols.append(Symbol(
                name=const_match.group(1),
                kind="constant",
                line=i,
            ))

    return symbols


# ─── TypeScript / JavaScript extractor ───────────────────────────────────────

def extract_typescript(source: str) -> list[Symbol]:
    """Extract symbols from TypeScript/JavaScript source code."""
    symbols: list[Symbol] = []
    lines = source.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        # function declaration
        func_match = re.match(
            r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
            line,
        )
        if func_match:
            symbols.append(Symbol(
                name=func_match.group(1),
                kind="function",
                line=i,
                signature=f"function {func_match.group(1)}({func_match.group(2)})",
            ))
            continue

        # arrow function (const/let/var)
        arrow_match = re.match(
            r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*[:=]\s*(?:async\s*)?\(([^)]*)\)",
            line,
        )
        if arrow_match:
            symbols.append(Symbol(
                name=arrow_match.group(1),
                kind="function",
                line=i,
                signature=f"const {arrow_match.group(1)} = (...) =>",
            ))
            continue

        # class declaration
        class_match = re.match(
            r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)",
            line,
        )
        if class_match:
            extends_match = re.search(r"extends\s+(\w+)", line)
            symbols.append(Symbol(
                name=class_match.group(1),
                kind="class",
                line=i,
                signature=f"class {class_match.group(1)}",
                parent=extends_match.group(1) if extends_match else None,
            ))
            continue

        # interface / type
        interface_match = re.match(
            r"^\s*(?:export\s+)?(?:interface|type)\s+(\w+)",
            line,
        )
        if interface_match:
            symbols.append(Symbol(
                name=interface_match.group(1),
                kind="type",
                line=i,
            ))
            continue

        # import statement
        import_match = re.match(
            r"""^\s*import\s+(?:\{[^}]*\}|(\w+))\s*from\s*['"]([^'"]+)['"]""",
            line,
        )
        if import_match:
            name = import_match.group(1) or import_match.group(0)
            symbols.append(Symbol(
                name=import_match.group(2),
                kind="import",
                line=i,
            ))
            continue

        # export statement (non-function/class)
        export_match = re.match(
            r"^\s*export\s+(?:const|let|var|enum)\s+(\w+)",
            line,
        )
        if export_match:
            symbols.append(Symbol(
                name=export_match.group(1),
                kind="export",
                line=i,
            ))

    return symbols


# ─── Go extractor ────────────────────────────────────────────────────────────

def extract_go(source: str) -> list[Symbol]:
    """Extract symbols from Go source code."""
    symbols: list[Symbol] = []
    lines = source.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        # func declaration
        func_match = re.match(
            r"^\s*func\s+(?:\((\w+)\s+\*?(\w+)\)\s+)?(\w+)\s*\(([^)]*)\)",
            line,
        )
        if func_match:
            method_of = func_match.group(2) if func_match.group(1) else None
            name = func_match.group(3)
            full_name = f"{method_of}.{name}" if method_of else name
            symbols.append(Symbol(
                name=full_name,
                kind="function",
                line=i,
                signature=stripped,
                parent=method_of,
            ))
            continue

        # type/struct declaration
        type_match = re.match(r"^\s*type\s+(\w+)\s+(struct|interface)", line)
        if type_match:
            symbols.append(Symbol(
                name=type_match.group(1),
                kind="class",
                line=i,
                signature=f"type {type_match.group(1)} {type_match.group(2)}",
            ))
            continue

        # import block entries (single import handled inline)
        import_match = re.match(r'^\s*"([^"]+)"', stripped)
        if import_match:
            symbols.append(Symbol(
                name=import_match.group(1),
                kind="import",
                line=i,
            ))
            continue

        # var/const
        var_match = re.match(r"^\s*(?:var|const)\s+(\w+)", line)
        if var_match:
            symbols.append(Symbol(
                name=var_match.group(1),
                kind="variable",
                line=i,
            ))

    return symbols


# ─── Extractor registry ──────────────────────────────────────────────────────

EXTRACTORS: dict[str, callable] = {
    "python": extract_python,
    "typescript": extract_typescript,
    "javascript": extract_typescript,
    "go": extract_go,
}


def extract_symbols(source: str, language: str) -> list[Symbol]:
    """Dispatch to the correct language extractor."""
    extractor = EXTRACTORS.get(language)
    if extractor is None:
        return []  # unknown language — skip symbol extraction
    return extractor(source)
