"""
storage.py
----------
Tiny persistence layer for the high score and mute preference.

Keeping this in its own module is an example of *decomposition*: the game
logic never has to know how data is stored on disk.
"""

from __future__ import annotations

import json
import os

from settings import DATA_PATH

_DEFAULT = {"high_score": 0, "muted": False}


def load_data() -> dict:
    """Load saved data, returning safe defaults if the file is missing/corrupt."""
    data = dict(_DEFAULT)
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if isinstance(raw, dict):
            if isinstance(raw.get("high_score"), int) and raw["high_score"] >= 0:
                data["high_score"] = raw["high_score"]
            data["muted"] = bool(raw.get("muted", False))
    except (OSError, ValueError, TypeError):
        pass
    return data


def save_data(data: dict) -> None:
    """Write data atomically so an interrupted save cannot corrupt the file."""
    payload = {
        "high_score": max(0, int(data.get("high_score", 0))),
        "muted": bool(data.get("muted", False)),
    }
    tmp = DATA_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp, DATA_PATH)
    except OSError:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
