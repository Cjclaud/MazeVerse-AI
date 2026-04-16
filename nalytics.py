# analytics.py
# -------------------------------------------------
# Player analytics system
# Tracks history and generates performance insights
# -------------------------------------------------

import json
import os
from app_paths import migrate_legacy_file

FILE_PATH = migrate_legacy_file("data/analytics.json")


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_analytics():
    if not os.path.exists(FILE_PATH):
        return []

    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_analytics(data):
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)


def record_session(entry):
    if not isinstance(entry, dict):
        return

    data = load_analytics()
    data.append(entry)
    save_analytics(data)


def get_summary():
    raw_data = load_analytics()
    data = [d for d in raw_data if isinstance(d, dict)]

    if not data:
        return {
            "games_played": 0,
            "avg_time": 0,
            "avg_moves": 0,
            "avg_score": 0,
            "avg_ai_score": 0,
        }

    total_time = sum(_safe_int(d.get("time", 0)) for d in data)
    total_moves = sum(_safe_int(d.get("moves", 0)) for d in data)
    total_score = sum(_safe_int(d.get("score", 0)) for d in data)
    total_ai = sum(_safe_int(d.get("ai_score", 0)) for d in data)

    count = len(data)

    return {
        "games_played": count,
        "avg_time": int(total_time / count),
        "avg_moves": int(total_moves / count),
        "avg_score": int(total_score / count),
        "avg_ai_score": int(total_ai / count),
    }


def get_recent_sessions(limit=5):
    data = [d for d in load_analytics() if isinstance(d, dict)]
    return data[-limit:]
