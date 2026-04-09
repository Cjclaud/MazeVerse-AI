import json
import os

FILE_PATH = "progress.json"


def load_progress():
    if not os.path.exists(FILE_PATH):
        return {}

    with open(FILE_PATH, "r") as f:
        return json.load(f)


def save_progress(data):
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)


def update_level_progress(level, score, ai_score, time_taken, items_used):
    data = load_progress()

    level = str(level)

    if level not in data:
        data[level] = {
            "completed": True,
            "best_score": score,
            "best_ai_score": ai_score,
            "best_time": time_taken,
            "items_used": items_used
        }
    else:
        data[level]["completed"] = True
        data[level]["best_score"] = max(score, data[level]["best_score"])
        data[level]["best_ai_score"] = max(ai_score, data[level]["best_ai_score"])

        if data[level]["best_time"] is None or time_taken < data[level]["best_time"]:
            data[level]["best_time"] = time_taken

        data[level]["items_used"] = items_used

    save_progress(data)