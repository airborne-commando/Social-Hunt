from __future__ import annotations

from pathlib import Path

# Project root is the repository folder (one level above this package).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


def resolve_path(p: str | Path) -> Path:
    """Resolve a path relative to the project root unless it's already absolute."""
    path = p if isinstance(p, Path) else Path(str(p))
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()
