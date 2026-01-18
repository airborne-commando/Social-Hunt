from __future__ import annotations

"""Read runtime settings written by the dashboard.

Settings are stored server-side in a JSON file (default: data/settings.json).
Python providers can read keys from this file instead of relying on env vars.

This module intentionally does a small file read each time to keep the
implementation simple and to pick up dashboard changes without restart.

Path handling:
- If SOCIAL_HUNT_SETTINGS_PATH is absolute, it is used as-is.
- If it is relative (or unset), it is resolved relative to the project root.
"""

import json
import os
from typing import Any, Dict

from .paths import resolve_path


def _settings_path() -> str:
    return (os.getenv("SOCIAL_HUNT_SETTINGS_PATH") or "data/settings.json").strip() or "data/settings.json"


def load_settings() -> Dict[str, Any]:
    path = resolve_path(_settings_path())
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def get_setting(key: str, default: Any = None) -> Any:
    return load_settings().get(key, default)
