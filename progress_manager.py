import json
import os
from app_paths import get_data_file, migrate_legacy_file

FILE_PATH = migrate_legacy_file("progress.json")
AI_DIFFICULTY_RANK = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3,
    "Insane": 4,
}


def _normalize_level_entry(entry):
    entry = dict(entry or {})
    mode_stats = entry.get("mode_stats")

    if not isinstance(mode_stats, dict):
        mode_stats = {
            "Solo": {
                "completed": bool(entry.get("completed", False)),
                "best_score": int(entry.get("best_score", 0) or 0),
                "best_ai_score": int(entry.get("best_ai_score", 0) or 0),
                "best_time": entry.get("best_time"),
                "items_used": list(entry.get("items_used", [])),
            },
            "VS AI": {
                "completed": False,
                "best_score": 0,
                "best_ai_score": 0,
                "best_time": None,
                "items_used": [],
                "best_ai_difficulty_beaten": None,
            },
        }

    for mode in ("Solo", "VS AI"):
        stats = dict(mode_stats.get(mode, {}))
        stats.setdefault("completed", False)
        stats.setdefault("best_score", 0)
        stats.setdefault("best_ai_score", 0)
        stats.setdefault("best_time", None)
        stats.setdefault("items_used", [])
        stats.setdefault("best_ai_difficulty_beaten", None)
        mode_stats[mode] = stats

    entry["mode_stats"] = mode_stats
    entry["completed"] = any(stats.get("completed") for stats in mode_stats.values())
    entry["best_score"] = max(stats.get("best_score", 0) for stats in mode_stats.values())
    entry["best_ai_score"] = max(stats.get("best_ai_score", 0) for stats in mode_stats.values())

    times = [stats.get("best_time") for stats in mode_stats.values() if stats.get("best_time") is not None]
    entry["best_time"] = min(times) if times else None
    return entry


def normalize_progress_data(data):
    normalized = {}
    for level, entry in (data or {}).items():
        normalized[str(level)] = _normalize_level_entry(entry)
    return normalized


def load_progress():
    if not os.path.exists(FILE_PATH):
        return {}

    try:
        with open(FILE_PATH, "r") as f:
            return normalize_progress_data(json.load(f))
    except (json.JSONDecodeError, OSError):
        return {}


def save_progress(data):
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)


def update_level_progress(level, score, ai_score, time_taken, items_used, game_mode="Solo", ai_difficulty=None):
    data = load_progress()

    level = str(level)
    if level not in data:
        data[level] = _normalize_level_entry({})

    entry = _normalize_level_entry(data[level])
    mode_key = "VS AI" if str(game_mode).upper() == "VS AI" else "Solo"
    mode_entry = entry["mode_stats"][mode_key]

    mode_entry["completed"] = True
    mode_entry["best_score"] = max(score, mode_entry["best_score"])
    mode_entry["best_ai_score"] = max(ai_score, mode_entry["best_ai_score"])

    if mode_entry["best_time"] is None or time_taken < mode_entry["best_time"]:
        mode_entry["best_time"] = time_taken

    mode_entry["items_used"] = items_used

    if mode_key == "VS AI" and ai_difficulty:
        current_best = mode_entry.get("best_ai_difficulty_beaten")
        if AI_DIFFICULTY_RANK.get(ai_difficulty, 0) >= AI_DIFFICULTY_RANK.get(current_best, 0):
            mode_entry["best_ai_difficulty_beaten"] = ai_difficulty

    entry["mode_stats"][mode_key] = mode_entry
    data[level] = _normalize_level_entry(entry)

    save_progress(data)
