from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Tuple


def calculate_content_hash(data: Dict[str, Any]) -> str:
    """Stable SHA-256 hash of JSON-like dict."""
    normalized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode()).hexdigest()


def diff_dicts(old: Dict[str, Any], new: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (changed_fields, old_values) for fields that differ."""
    changed: Dict[str, Any] = {}
    old_values: Dict[str, Any] = {}
    for key in new.keys() | old.keys():
        if old.get(key) != new.get(key):
            changed[key] = new.get(key)
            old_values[key] = old.get(key)
    return changed, old_values


