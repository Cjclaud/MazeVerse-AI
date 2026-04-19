
# advanced_tracking.py
# -------------------------------------------------
# Advanced tracking systems:
# - movement heatmap
# - player replay recording
# - ghost AI comparison
# -------------------------------------------------

import json
import os
from app_paths import migrate_legacy_file

REPLAY_FILE = migrate_legacy_file("data/replays.json")


def create_empty_heatmap(rows, cols):
    return [[0 for _ in range(cols)] for _ in range(rows)]


def record_heatmap_visit(heatmap, row, col):
    if 0 <= row < len(heatmap) and 0 <= col < len(heatmap[0]):
        heatmap[row][col] += 1


def get_heatmap_max(heatmap):
    max_value = 0
    for row in heatmap:
        for value in row:
            if value > max_value:
                max_value = value
    return max_value


def build_replay_entry(level, difficulty, moves, ai_path, rows, cols, game_mode="Solo", ai_difficulty=None):
    return {
        "level": level,
        "difficulty": difficulty,
        "game_mode": game_mode,
        "ai_difficulty": ai_difficulty,
        "moves": moves,
        "ai_path": ai_path,
        "rows": rows,
        "cols": cols,
    }


def load_replays():
    if not os.path.exists(REPLAY_FILE):
        return []

    try:
        with open(REPLAY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_replays(data):
    os.makedirs(os.path.dirname(REPLAY_FILE), exist_ok=True)
    with open(REPLAY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def save_replay(entry):
    data = load_replays()
    data.append(entry)

    # keep last 20 only
    if len(data) > 20:
        data = data[-20:]

    save_replays(data)


def get_last_replay():
    data = load_replays()
    if not data:
        return None
    return data[-1]


def compare_player_vs_ai(player_moves, ai_path):
    """
    Simple comparison summary.
    """
    player_steps = max(0, len(player_moves) - 1)
    if not ai_path:
        return {
            "player_steps": player_steps,
            "ai_steps": 0,
            "difference": 0,
            "verdict": "Solo run - no AI comparison",
        }

    ai_steps = max(0, len(ai_path) - 1)

    difference = player_steps - ai_steps

    if difference <= 0:
        verdict = "Matched or beat AI route"
    elif difference <= 5:
        verdict = "Very close to AI route"
    elif difference <= 15:
        verdict = "Moderately less efficient than AI"
    else:
        verdict = "Far less efficient than AI"

    return {
        "player_steps": player_steps,
        "ai_steps": ai_steps,
        "difference": difference,
        "verdict": verdict,
    }
