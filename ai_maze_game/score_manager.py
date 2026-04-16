# score_manager.py
import json
import os

SCORE_FILE = "best_scores.json"


def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {}

    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


def save_scores(scores):
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=4)


def get_best_score(difficulty):
    scores = load_scores()
    return scores.get(difficulty, 0)


def update_best_score(difficulty, new_score):
    scores = load_scores()
    old_score = scores.get(difficulty, 0)

    if new_score > old_score:
        scores[difficulty] = new_score
        save_scores(scores)
        return True, new_score

    return False, old_score