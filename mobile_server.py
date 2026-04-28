import json
import random
import threading
import time

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

from app_paths import get_data_file

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}
race_started = False
race_finished = False
winner = None
race_results = []
active_race_sids = set()
session_counter = 0
current_maze = []
current_theme = {}

MOBILE_RACE_HISTORY_FILE = get_data_file("mobile_race_history.json")
QUIZ_LENGTH = 5
THEME_ROTATION = ["Neon Circuit", "Frost Vault", "Ember Core", "Void Grid"]
MOBILE_THEME_RULES = {
    "Neon Circuit": {
        "bg_top": "#0a1234",
        "bg_mid": "#12225c",
        "panel_glow": "rgba(0, 170, 255, 0.18)",
        "accent": "#00f5ff",
        "accent_soft": "#4fc3ff",
        "path": "#10234d",
        "path_alt": "#0a1732",
        "wall": "#14264c",
        "wall_alt": "#091126",
        "goal": "#ff50be",
        "goal_soft": "#ff96d4",
    },
    "Frost Vault": {
        "bg_top": "#10243d",
        "bg_mid": "#1f5586",
        "panel_glow": "rgba(120, 220, 255, 0.2)",
        "accent": "#8feaff",
        "accent_soft": "#d8fbff",
        "path": "#153a58",
        "path_alt": "#10283c",
        "wall": "#234f6d",
        "wall_alt": "#112b42",
        "goal": "#9ef5ff",
        "goal_soft": "#e8ffff",
    },
    "Ember Core": {
        "bg_top": "#2a1008",
        "bg_mid": "#5a1f12",
        "panel_glow": "rgba(255, 120, 60, 0.18)",
        "accent": "#ff9a4d",
        "accent_soft": "#ffd1ad",
        "path": "#4a2214",
        "path_alt": "#2a130d",
        "wall": "#7f3418",
        "wall_alt": "#4d1f0f",
        "goal": "#ff7848",
        "goal_soft": "#ffcf8f",
    },
    "Void Grid": {
        "bg_top": "#160f30",
        "bg_mid": "#311957",
        "panel_glow": "rgba(190, 110, 255, 0.2)",
        "accent": "#bb87ff",
        "accent_soft": "#edd8ff",
        "path": "#281544",
        "path_alt": "#180d2b",
        "wall": "#48206a",
        "wall_alt": "#28153f",
        "goal": "#d471ff",
        "goal_soft": "#f2cbff",
    },
}
QUESTION_BANK = [
    {"q": "What does BFS stand for?", "a": ["Breadth-First Search", "Binary Flow Search", "Best-First System"], "c": 0},
    {"q": "Which search is guaranteed to find the shortest path in an unweighted grid?", "a": ["BFS", "DFS", "Greedy Best-First Search"], "c": 0},
    {"q": "A heuristic in A* is best described as...", "a": ["A guess of the remaining cost", "A random move", "A stored maze wall"], "c": 0},
    {"q": "Which algorithm combines path cost so far with a heuristic estimate to the goal?", "a": ["A*", "BFS", "DFS"], "c": 0},
    {"q": "If a heuristic never overestimates the true cost, it is called...", "a": ["Admissible", "Recursive", "Weighted"], "c": 0},
    {"q": "BFS usually explores nodes...", "a": ["Level by level", "Only near the goal", "In a random order"], "c": 0},
    {"q": "Which search usually uses more memory on large wide graphs?", "a": ["BFS", "DFS", "Hill climbing"], "c": 0},
    {"q": "Why can A* be faster than BFS in many mazes?", "a": ["It uses a heuristic to guide the search", "It ignores the goal", "It avoids storing visited nodes"], "c": 0},
    {"q": "Which statement about heuristics is correct?", "a": ["They help estimate how close a state is to the goal", "They always guarantee the answer is wrong", "They replace the maze completely"], "c": 0},
    {"q": "Breadth-first search explores all nodes at distance 1 before distance 2.", "a": ["True", "False"], "c": 0},
    {"q": "If every move in a maze costs the same, BFS is useful because it...", "a": ["Finds the shortest path by number of steps", "Only finds deep paths", "Needs no queue"], "c": 0},
    {"q": "What does the heuristic part of A* try to predict?", "a": ["How far the goal still is", "How many players joined", "How many walls are in the whole maze"], "c": 0},
]


def generate_shared_maze(size=10):
    maze = [[1 for _ in range(size)] for _ in range(size)]

    def carve(x, y):
        maze[y][x] = 0
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx = x + dx * 2
            ny = y + dy * 2
            if 0 <= nx < size and 0 <= ny < size and maze[ny][nx] == 1:
                maze[y + dy][x + dx] = 0
                carve(nx, ny)

    carve(0, 0)
    maze[size - 1][size - 1] = 0
    maze[size - 2][size - 1] = 0
    return maze


def build_quiz_set():
    selected = random.sample(QUESTION_BANK, min(QUIZ_LENGTH, len(QUESTION_BANK)))
    random.shuffle(selected)
    return selected


def build_session_theme(session_number):
    name = THEME_ROTATION[(max(1, session_number) - 1) % len(THEME_ROTATION)]
    theme = dict(MOBILE_THEME_RULES.get(name, MOBILE_THEME_RULES["Neon Circuit"]))
    theme["name"] = name
    return theme


def load_mobile_race_history():
    try:
        with open(MOBILE_RACE_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("sessions", [])
                data.setdefault("player_best_times", {})
                return data
    except (OSError, json.JSONDecodeError):
        pass

    return {"sessions": [], "player_best_times": {}}


def save_mobile_race_history(data):
    with open(MOBILE_RACE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def format_seconds(seconds):
    if seconds is None:
        return "--"

    total_seconds = max(0.0, float(seconds))
    minutes = int(total_seconds // 60)
    remainder = total_seconds - (minutes * 60)
    return f"{minutes:02d}:{remainder:05.2f}"


def build_player_update_payload():
    total_players = len(players)
    ready_players = sum(1 for player in players.values() if player.get("ready_for_replay"))
    finished_players = sum(1 for sid in active_race_sids if players.get(sid, {}).get("finished"))
    roster = []

    for player in players.values():
        roster.append(
            {
                "name": player.get("name", "STUDENT"),
                "finished": bool(player.get("finished")),
                "ready_for_replay": bool(player.get("ready_for_replay")),
            }
        )

    return {
        "count": total_players,
        "finished_count": finished_players,
        "active_count": len(active_race_sids),
        "ready_count": ready_players,
        "race_started": race_started,
        "race_finished": race_finished,
        "roster": roster,
        "partial_results": build_partial_results(),
        "theme": current_theme,
    }


def broadcast_player_update():
    socketio.emit("player_update", build_player_update_payload())


def build_results_payload():
    return {
        "winner": winner,
        "results": race_results,
        "session_counter": session_counter,
        "player_count": len(race_results),
    }


def build_partial_results():
    partial = []
    for sid in active_race_sids:
        player = players.get(sid)
        if not player or not player.get("finished"):
            continue

        partial.append(
            {
                "name": player.get("name", "STUDENT"),
                "total": int(player.get("total", 0) or 0),
                "completion_seconds": round(float(player.get("completion_seconds", 0.0) or 0.0), 2),
                "completion_time": format_seconds(player.get("completion_seconds")),
            }
        )

    partial.sort(key=lambda item: (-item["total"], item["completion_seconds"], item["name"]))
    for rank, entry in enumerate(partial, start=1):
        entry["rank"] = rank
    return partial


def persist_race_results():
    if not race_results:
        return

    history = load_mobile_race_history()
    history["sessions"].append(
        {
            "timestamp": int(time.time()),
            "session_counter": session_counter,
            "winner": winner,
            "results": race_results,
        }
    )
    history["sessions"] = history["sessions"][-50:]

    best_times = history.get("player_best_times", {})
    for entry in race_results:
        player_name = entry.get("name", "STUDENT")
        completion_seconds = entry.get("completion_seconds")
        if completion_seconds is None:
            continue
        current_best = best_times.get(player_name)
        if current_best is None or completion_seconds < current_best:
            best_times[player_name] = completion_seconds

    history["player_best_times"] = best_times
    save_mobile_race_history(history)


def finalize_race_results():
    global winner, race_finished, race_started, race_results

    standings = []
    for sid in active_race_sids:
        player = players.get(sid)
        if not player or not player.get("finished"):
            continue

        standings.append(
            {
                "name": player.get("name", "STUDENT"),
                "race_marks": int(player.get("race_marks", 0) or 0),
                "quiz_marks": int(player.get("quiz_marks", 0) or 0),
                "total": int(player.get("total", 0) or 0),
                "completion_seconds": round(float(player.get("completion_seconds", 0.0) or 0.0), 2),
                "completion_time": format_seconds(player.get("completion_seconds")),
            }
        )

    standings.sort(key=lambda item: (-item["total"], item["completion_seconds"], item["name"]))
    for rank, entry in enumerate(standings, start=1):
        entry["rank"] = rank

    race_results = standings
    winner = standings[0] if standings else None
    race_finished = True
    race_started = False
    persist_race_results()
    socketio.emit("results_ready", build_results_payload())
    broadcast_player_update()


def maybe_finalize_race():
    global race_started

    if not race_started or race_finished:
        return

    if not active_race_sids:
        race_started = False
        broadcast_player_update()
        return

    if all(players.get(sid, {}).get("finished") for sid in active_race_sids):
        finalize_race_results()


def reset_race_state(keep_players=True):
    global race_started, race_finished, winner, race_results, active_race_sids, current_maze, current_theme

    race_started = False
    race_finished = False
    winner = None
    race_results = []
    active_race_sids = set()
    current_maze = []
    current_theme = {}

    if keep_players:
        for player in players.values():
            player["finished"] = False
            player["ready_for_replay"] = False
            player["race_marks"] = 0
            player["quiz_marks"] = 0
            player["total"] = 0
            player["completion_seconds"] = None
            player["start_time"] = None
    else:
        players.clear()


def start_race_session():
    global race_started, race_finished, winner, race_results, active_race_sids, session_counter, current_maze, current_theme

    if race_started or not players:
        return False

    race_started = True
    race_finished = False
    winner = None
    race_results = []
    active_race_sids = set(players.keys())
    session_counter += 1
    current_theme = build_session_theme(session_counter)
    current_maze = generate_shared_maze()
    quiz_set = build_quiz_set()
    start_time = time.time()

    for sid, player in players.items():
        player["finished"] = False
        player["ready_for_replay"] = False
        player["race_marks"] = 0
        player["quiz_marks"] = 0
        player["total"] = 0
        player["completion_seconds"] = None
        player["start_time"] = start_time

    socketio.emit(
        "race_start",
        {
            "session_counter": session_counter,
            "maze": current_maze,
            "questions": quiz_set,
            "theme": current_theme,
            "countdown_seconds": 3,
        },
    )
    broadcast_player_update()
    return True


def open_new_session():
    reset_race_state(keep_players=False)
    socketio.emit("session_reset", {"session_counter": session_counter})
    broadcast_player_update()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MAZEVERSE | Knowledge Uplink</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js" crossorigin="anonymous"></script>
    <style>
        :root {
            --cyan: #00f5ff;
            --blue: #3a69eb;
            --dark: #040612;
            --glass: rgba(10, 16, 40, 0.9);
            --pink: #ff50be;
            --success: #00ff95;
            --warning: #ffc857;
            --muted: #97a5d6;
            --danger: #ff7b7b;
            --panel: rgba(10, 16, 34, 0.92);
            --panel-border: rgba(70, 145, 255, 0.38);
            --panel-inner: rgba(8, 12, 28, 0.96);
            --soft-white: #f0f7ff;
            --grid-line: rgba(36, 78, 150, 0.65);
            --theme-top: #0a1234;
            --theme-mid: #12225c;
            --theme-accent: #00f5ff;
            --theme-accent-soft: #4fc3ff;
            --theme-path: #10234d;
            --theme-path-alt: #0a1732;
            --theme-wall: #14264c;
            --theme-wall-alt: #091126;
            --theme-goal: #ff50be;
            --theme-goal-soft: #ff96d4;
            --theme-panel-glow: rgba(0, 170, 255, 0.18);
        }
        * { box-sizing: border-box; }
        body {
            background:
                radial-gradient(circle at top, color-mix(in srgb, var(--theme-accent) 25%, transparent), transparent 34%),
                radial-gradient(circle at bottom right, rgba(255, 80, 190, 0.18), transparent 28%),
                linear-gradient(180deg, var(--theme-top) 0%, var(--theme-mid) 42%, #040612 100%);
            color: #f0f7ff;
            font-family: "Segoe UI", sans-serif;
            text-align: center;
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 18px;
            user-select: none;
        }
        #game-container {
            width: min(100%, 440px);
            padding: 24px 16px 20px;
            border: 1px solid rgba(0, 245, 255, 0.32);
            border-radius: 30px;
            background:
                linear-gradient(180deg, rgba(16, 28, 60, 0.96), rgba(7, 11, 25, 0.96));
            backdrop-filter: blur(10px);
            box-shadow:
                0 0 0 1px rgba(100, 180, 255, 0.08) inset,
                0 0 34px var(--theme-panel-glow),
                0 18px 45px rgba(0, 0, 0, 0.38);
            position: relative;
            overflow: hidden;
        }
        #game-container::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, transparent 0, rgba(255, 255, 255, 0.03) 50%, transparent 100%),
                repeating-linear-gradient(
                    180deg,
                    transparent 0,
                    transparent 18px,
                    rgba(80, 135, 255, 0.035) 19px
                );
            pointer-events: none;
            opacity: 0.7;
        }
        #game-container > * {
            position: relative;
            z-index: 1;
        }
        .eyebrow-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 12px;
            border-radius: 999px;
            margin-bottom: 14px;
            background: linear-gradient(180deg, rgba(10, 24, 48, 0.92), rgba(8, 14, 28, 0.96));
            border: 1px solid rgba(0, 245, 255, 0.24);
            color: var(--soft-white);
            font-size: 11px;
            letter-spacing: 2px;
            text-transform: uppercase;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
        }
        .eyebrow-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--success);
            box-shadow: 0 0 12px rgba(0, 255, 149, 0.65);
            animation: signalPulse 1.6s ease-in-out infinite;
        }
        h1 {
            color: var(--cyan);
            font-size: 24px;
            letter-spacing: 5px;
            margin: 0 0 6px;
            text-shadow: 0 0 10px var(--theme-accent), 0 0 24px color-mix(in srgb, var(--theme-accent) 35%, transparent);
        }
        h2 { margin: 8px 0 12px; }
        p { margin: 8px 0; }
        .setup-shell {
            position: relative;
            padding: 18px 16px 16px;
            border-radius: 24px;
            background:
                linear-gradient(180deg, rgba(12, 23, 49, 0.92), rgba(8, 14, 30, 0.9));
            border: 1px solid rgba(0, 245, 255, 0.16);
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.02),
                0 18px 30px rgba(0, 0, 0, 0.18);
        }
        .setup-shell::before {
            content: "";
            position: absolute;
            inset: 1px;
            border-radius: 23px;
            background:
                radial-gradient(circle at top, rgba(79, 195, 255, 0.12), transparent 42%),
                linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 34%);
            pointer-events: none;
        }
        .setup-shell > * {
            position: relative;
            z-index: 1;
        }
        .section-kicker {
            color: var(--muted);
            font-size: 11px;
            letter-spacing: 2.4px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .setup-title {
            margin-bottom: 18px;
        }
        .setup-blurb {
            max-width: 330px;
            margin: 0 auto 16px;
            line-height: 1.45;
        }
        .btn, .ghost-btn {
            border: none;
            color: white;
            padding: 16px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 16px;
            cursor: pointer;
            width: 100%;
            touch-action: manipulation;
            margin-top: 10px;
            transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
        }
        .btn {
            background: linear-gradient(135deg, #00f5ff 0%, #2289ff 55%, #5d6dff 100%);
            box-shadow: 0 14px 28px rgba(0, 120, 255, 0.28);
            letter-spacing: 1.6px;
        }
        .ghost-btn {
            background: linear-gradient(180deg, rgba(27, 40, 79, 0.68), rgba(14, 22, 44, 0.78));
            border: 1px solid rgba(0, 245, 255, 0.2);
        }
        .ghost-btn.small {
            padding: 12px;
            font-size: 14px;
        }
        .btn:hover, .ghost-btn:hover, .control-btn:hover, .option-btn:hover {
            transform: translateY(-1px);
        }
        .btn:active, .ghost-btn:active, .control-btn:active, .option-btn:active {
            transform: scale(0.98);
        }
        .panel {
            background: linear-gradient(180deg, rgba(11, 20, 43, 0.96), rgba(8, 12, 28, 0.96));
            border: 1px solid rgba(70, 145, 255, 0.22);
            border-radius: 18px;
            padding: 14px 12px;
            margin-top: 12px;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.025);
        }
        .muted { color: var(--muted); font-size: 13px; }
        .accent { color: var(--cyan); }
        .success { color: var(--success); }
        .warning { color: var(--warning); }
        .danger { color: var(--danger); }
        .callsign-shell {
            display: grid;
            grid-template-columns: 44px 1fr;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            margin-bottom: 12px;
            border-radius: 18px;
            border: 1px solid rgba(0, 245, 255, 0.2);
            background: linear-gradient(180deg, rgba(6, 11, 26, 0.96), rgba(8, 15, 33, 0.92));
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
        }
        .callsign-icon {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: var(--theme-accent);
            background: linear-gradient(180deg, rgba(9, 30, 56, 0.96), rgba(10, 20, 38, 0.96));
            border: 1px solid rgba(79, 195, 255, 0.18);
            box-shadow: 0 0 18px rgba(0, 245, 255, 0.12);
        }
        #player-name {
            padding: 6px 2px;
            width: 100%;
            border-radius: 0;
            border: none;
            background: transparent;
            color: white;
            margin-bottom: 0;
            text-align: left;
            font-size: 24px;
            letter-spacing: 1px;
            box-shadow: none;
            outline: none;
            font-weight: 600;
        }
        #player-name::placeholder {
            color: rgba(240, 247, 255, 0.34);
            letter-spacing: 2px;
        }
        .setup-actions {
            display: grid;
            gap: 10px;
            margin-top: 8px;
        }
        .status-card {
            margin-top: 14px;
            padding: 14px 14px 12px;
            border-radius: 18px;
            text-align: left;
            background: linear-gradient(180deg, rgba(13, 23, 49, 0.9), rgba(8, 13, 28, 0.94));
            border: 1px solid rgba(96, 135, 255, 0.18);
        }
        .status-label {
            display: block;
            margin-bottom: 6px;
            color: var(--cyan);
            font-size: 10px;
            letter-spacing: 2.2px;
            text-transform: uppercase;
        }
        #setup-status {
            margin: 0;
            font-size: 14px;
            color: var(--soft-white);
            line-height: 1.45;
        }
        .setup-footnote {
            margin-top: 12px;
            line-height: 1.45;
        }
        #maze-grid {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 3px;
            background:
                linear-gradient(180deg, rgba(14, 26, 52, 0.98), rgba(8, 14, 28, 0.98));
            border: 2px solid color-mix(in srgb, var(--theme-accent) 62%, white 14%);
            border-radius: 18px;
            margin: 18px auto 14px;
            width: min(72vw, 300px);
            height: min(72vw, 300px);
            padding: 8px;
            box-shadow:
                0 0 26px color-mix(in srgb, var(--theme-accent) 18%, transparent),
                inset 0 0 22px rgba(0, 0, 0, 0.38),
                inset 0 0 0 1px rgba(255, 255, 255, 0.05);
            position: relative;
        }
        #maze-grid::after {
            content: "";
            position: absolute;
            inset: 8px;
            border-radius: 12px;
            background-image:
                linear-gradient(var(--grid-line) 1px, transparent 1px),
                linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
            background-size: calc(100% / 10) calc(100% / 10);
            opacity: 0.22;
            pointer-events: none;
        }
        .cell {
            width: 100%;
            height: 100%;
            border-radius: 6px;
            transition: transform 0.14s ease, box-shadow 0.14s ease, background 0.14s ease, border-color 0.14s ease;
            border: 1px solid transparent;
        }
        .wall {
            background:
                linear-gradient(180deg, #07101f, color-mix(in srgb, var(--theme-wall-alt) 82%, black 18%) 48%, #13284d);
            border-color: rgba(255, 255, 255, 0.14);
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.07),
                inset 0 -4px 8px rgba(0, 0, 0, 0.42),
                0 1px 0 rgba(0, 0, 0, 0.2);
        }
        .path {
            background:
                linear-gradient(180deg, #8ea8c8, #5e7697 58%, #405575);
            border-color: rgba(210, 232, 255, 0.2);
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.08),
                inset 0 -2px 4px rgba(0, 0, 0, 0.16);
        }
        .visited {
            background:
                linear-gradient(180deg, #c7fbff, #62ebff 46%, #1ca0ff);
            border-color: rgba(233, 255, 255, 0.45);
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.18),
                0 0 10px rgba(98, 235, 255, 0.2);
        }
        .player {
            background: radial-gradient(circle at 35% 35%, #ffffff, var(--theme-accent) 58%, color-mix(in srgb, var(--theme-accent) 70%, #0f1f45));
            border-radius: 50%;
            border-color: rgba(255, 255, 255, 0.38);
            box-shadow: 0 0 18px var(--theme-accent), 0 0 26px color-mix(in srgb, var(--theme-accent) 35%, transparent);
            transform: scale(0.82);
            animation: playerPulse 0.9s ease-in-out infinite alternate;
        }
        .goal {
            background: radial-gradient(circle, var(--theme-goal-soft), var(--theme-goal));
            box-shadow: 0 0 14px var(--theme-goal);
            border-radius: 8px;
            transform: scale(0.84) rotate(45deg);
            animation: pulseGoal 1.4s ease-in-out infinite alternate;
        }
        .start {
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.3), 0 0 12px color-mix(in srgb, var(--theme-accent) 22%, transparent);
            position: relative;
        }
        .maze-legend {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
            margin-top: 12px;
        }
        .legend-chip {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            padding: 8px 6px;
            border-radius: 12px;
            font-size: 11px;
            color: var(--soft-white);
            background: linear-gradient(180deg, rgba(13, 23, 49, 0.88), rgba(8, 14, 30, 0.9));
            border: 1px solid rgba(88, 170, 255, 0.16);
        }
        .legend-swatch {
            width: 12px;
            height: 12px;
            border-radius: 4px;
            flex: 0 0 auto;
        }
        .legend-swatch.wall-swatch {
            background: linear-gradient(180deg, #07101f, color-mix(in srgb, var(--theme-wall-alt) 82%, black 18%) 48%, #13284d);
            border: 1px solid rgba(255, 255, 255, 0.14);
        }
        .legend-swatch.path-swatch {
            background: linear-gradient(180deg, #8ea8c8, #5e7697 58%, #405575);
            border: 1px solid rgba(210, 232, 255, 0.2);
        }
        .legend-swatch.visited-swatch {
            background: linear-gradient(180deg, #c7fbff, #62ebff 46%, #1ca0ff);
            border: 1px solid rgba(233, 255, 255, 0.45);
        }
        .legend-swatch.goal-swatch {
            background: radial-gradient(circle, var(--theme-goal-soft), var(--theme-goal));
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        #controls {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            width: 180px;
            margin: 15px auto;
        }
        .control-btn {
            background: linear-gradient(180deg, rgba(24, 52, 108, 0.92), rgba(14, 26, 58, 0.92));
            border: 1px solid rgba(70, 145, 255, 0.72);
            color: var(--cyan);
            height: 54px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 18px rgba(0, 140, 255, 0.12);
        }
        .option-btn {
            display: block;
            width: 100%;
            padding: 16px 16px;
            margin: 12px 0;
            background: linear-gradient(180deg, rgba(20, 36, 74, 0.98), rgba(10, 19, 41, 0.98));
            border: 1px solid rgba(89, 154, 255, 0.34);
            color: white;
            border-radius: 18px;
            text-align: left;
            font-size: 15px;
            line-height: 1.35;
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.035),
                0 12px 22px rgba(0, 0, 0, 0.16);
        }
        .option-btn.correct-answer {
            background: linear-gradient(180deg, rgba(14, 76, 60, 0.96), rgba(8, 48, 37, 0.96));
            border-color: rgba(0, 255, 149, 0.55);
            box-shadow: 0 0 24px rgba(0, 255, 149, 0.14), inset 0 0 0 1px rgba(255, 255, 255, 0.05);
        }
        .option-btn.wrong-answer {
            background: linear-gradient(180deg, rgba(92, 26, 39, 0.94), rgba(54, 15, 24, 0.96));
            border-color: rgba(255, 123, 123, 0.55);
            box-shadow: 0 0 24px rgba(255, 123, 123, 0.12), inset 0 0 0 1px rgba(255, 255, 255, 0.04);
        }
        .option-btn.dimmed-answer {
            opacity: 0.58;
            transform: none;
        }
        .quiz-shell {
            position: relative;
            padding: 16px 16px 18px;
            border-radius: 28px;
            background:
                radial-gradient(circle at top, rgba(79, 195, 255, 0.08), transparent 32%),
                linear-gradient(180deg, rgba(13, 24, 52, 0.96), rgba(8, 14, 30, 0.94));
            border: 1px solid rgba(0, 245, 255, 0.16);
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.03),
                0 18px 34px rgba(0, 0, 0, 0.22);
            overflow: hidden;
        }
        .quiz-shell::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(120deg, rgba(255, 255, 255, 0.035), transparent 22%, transparent 72%, rgba(255, 255, 255, 0.025)),
                repeating-linear-gradient(
                    180deg,
                    transparent 0,
                    transparent 24px,
                    rgba(79, 195, 255, 0.03) 25px
                );
            pointer-events: none;
            opacity: 0.9;
        }
        .quiz-shell > * {
            position: relative;
            z-index: 1;
        }
        .quiz-hero {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
        }
        .quiz-copy {
            text-align: left;
        }
        .quiz-topline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        .quiz-step {
            color: var(--cyan);
            font-size: 11px;
            letter-spacing: 2.6px;
            text-transform: uppercase;
        }
        .quiz-title {
            margin: 0;
            font-size: 26px;
            font-weight: 800;
            letter-spacing: 0.6px;
            color: var(--soft-white);
            text-align: left;
            text-shadow: 0 0 14px rgba(79, 195, 255, 0.08);
        }
        .quiz-subtitle {
            margin: 6px 0 0;
            max-width: 280px;
            text-align: left;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.45;
        }
        .quiz-progress-pill {
            padding: 9px 12px;
            border-radius: 18px;
            font-size: 11px;
            color: var(--soft-white);
            background: linear-gradient(180deg, rgba(9, 51, 79, 0.92), rgba(10, 37, 57, 0.92));
            border: 1px solid rgba(0, 245, 255, 0.22);
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
            text-align: center;
            min-width: 92px;
        }
        .quiz-progress-bar {
            height: 8px;
            border-radius: 999px;
            overflow: hidden;
            margin: 4px 0 14px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(88, 170, 255, 0.12);
        }
        .quiz-progress-fill {
            width: 20%;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #00f5ff, #3fb1ff 55%, #7ce0ff);
            box-shadow: 0 0 18px rgba(0, 245, 255, 0.32);
            transition: width 0.22s ease;
        }
        .quiz-question-card {
            padding: 18px 16px;
            border-radius: 22px;
            margin: 0 0 14px;
            text-align: left;
            background:
                radial-gradient(circle at top left, rgba(79, 195, 255, 0.08), transparent 38%),
                linear-gradient(180deg, rgba(6, 12, 28, 0.96), rgba(10, 18, 40, 0.98));
            border: 1px solid rgba(88, 170, 255, 0.2);
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.025),
                0 10px 20px rgba(0, 0, 0, 0.16);
        }
        #q-text {
            font-size: 20px;
            font-weight: 700;
            line-height: 1.45;
            margin: 0;
        }
        #options-box {
            margin-top: 4px;
        }
        #answer-reveal {
            min-height: 44px;
            margin-top: 14px;
            padding: 12px 14px;
            border-radius: 16px;
            text-align: left;
            background: linear-gradient(180deg, rgba(9, 18, 39, 0.76), rgba(9, 18, 39, 0.92));
            border: 1px solid rgba(88, 170, 255, 0.14);
            color: var(--soft-white);
            line-height: 1.45;
        }
        #answer-reveal.hidden {
            display: none;
        }
        #answer-reveal.correct {
            border-color: rgba(0, 255, 149, 0.35);
            background: linear-gradient(180deg, rgba(10, 62, 49, 0.84), rgba(8, 34, 28, 0.92));
        }
        #answer-reveal.wrong {
            border-color: rgba(255, 123, 123, 0.35);
            background: linear-gradient(180deg, rgba(68, 23, 33, 0.84), rgba(35, 12, 17, 0.92));
        }
        .reveal-label {
            display: block;
            margin-bottom: 4px;
            font-size: 10px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: rgba(240, 247, 255, 0.72);
        }
        #feedback-emoji {
            font-size: 48px;
            margin: 10px;
            height: 58px;
            filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.16));
        }
        .hidden { display: none; }
        .score-chip {
            display: inline-block;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(0, 245, 255, 0.12);
            border: 1px solid rgba(0, 245, 255, 0.25);
            margin-top: 8px;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        }
        .score-chip.tight {
            font-size: 12px;
            padding: 7px 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 13px;
        }
        th, td {
            padding: 8px 6px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        th { color: var(--cyan); font-size: 12px; }
        td { color: #edf3ff; }
        .race-shell {
            background: linear-gradient(180deg, rgba(8, 18, 36, 0.92), rgba(6, 10, 24, 0.92));
            border: 1px solid rgba(70, 145, 255, 0.18);
            border-radius: 22px;
            padding: 12px 10px 14px;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        }
        #goal-burst {
            position: absolute;
            inset: 0;
            display: none;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            background: rgba(4, 8, 18, 0.66);
            backdrop-filter: blur(4px);
            z-index: 4;
            border-radius: 30px;
        }
        #goal-burst-icon {
            font-size: 64px;
            filter: drop-shadow(0 0 16px color-mix(in srgb, var(--theme-goal) 55%, transparent));
            animation: burstPop 0.5s ease-out both;
        }
        #goal-burst-text {
            color: var(--soft-white);
            letter-spacing: 3px;
            font-size: 13px;
            margin-top: 8px;
        }
        #waiting-preview-list {
            display: grid;
            gap: 8px;
            margin-top: 10px;
        }
        .preview-row {
            display: grid;
            grid-template-columns: 36px 1fr auto auto;
            gap: 8px;
            align-items: center;
            padding: 9px 10px;
            border-radius: 12px;
            background: linear-gradient(180deg, rgba(16, 30, 64, 0.9), rgba(9, 18, 39, 0.9));
            border: 1px solid rgba(70, 145, 255, 0.24);
            font-size: 12px;
        }
        .preview-rank {
            color: var(--theme-accent);
            font-weight: bold;
        }
        .preview-name {
            text-align: left;
            color: var(--soft-white);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .preview-score {
            color: var(--success);
        }
        .preview-time {
            color: var(--muted);
            min-width: 56px;
            text-align: right;
        }
        .hud-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--muted);
            margin-top: 6px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        @keyframes pulseGoal {
            from { box-shadow: 0 0 10px rgba(255, 80, 190, 0.55); }
            to { box-shadow: 0 0 20px rgba(255, 120, 220, 0.95); }
        }
        @keyframes playerPulse {
            from { box-shadow: 0 0 10px color-mix(in srgb, var(--theme-accent) 55%, transparent); }
            to { box-shadow: 0 0 20px color-mix(in srgb, var(--theme-accent) 95%, transparent); }
        }
        @keyframes floatOrb {
            from { transform: translateY(0px) translateX(0px) scale(1); opacity: 0.5; }
            to { transform: translateY(-18px) translateX(10px) scale(1.08); opacity: 0.9; }
        }
        @keyframes signalPulse {
            from { transform: scale(0.92); opacity: 0.7; }
            to { transform: scale(1.08); opacity: 1; }
        }
        .ambient-orb {
            position: fixed;
            border-radius: 999px;
            filter: blur(8px);
            pointer-events: none;
            opacity: 0.4;
            animation: floatOrb 4.5s ease-in-out infinite alternate;
        }
        .ambient-orb.a {
            width: 88px;
            height: 88px;
            top: 12%;
            left: 8%;
            background: color-mix(in srgb, var(--theme-accent) 45%, transparent);
        }
        .ambient-orb.b {
            width: 110px;
            height: 110px;
            right: 7%;
            bottom: 16%;
            animation-duration: 5.6s;
            background: color-mix(in srgb, var(--theme-goal) 40%, transparent);
        }
        @keyframes burstPop {
            from { transform: scale(0.3); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        #countdown-overlay {
            position: absolute;
            inset: 0;
            display: none;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            background: rgba(4, 8, 18, 0.72);
            backdrop-filter: blur(6px);
            z-index: 3;
            border-radius: 30px;
        }
        #countdown-number {
            font-size: 76px;
            font-weight: bold;
            color: var(--theme-accent);
            text-shadow: 0 0 24px color-mix(in srgb, var(--theme-accent) 55%, transparent);
        }
        #countdown-label {
            color: var(--soft-white);
            letter-spacing: 3px;
            font-size: 13px;
        }
        @media (max-width: 420px) {
            body {
                padding: 10px;
                align-items: stretch;
            }
            #game-container {
                width: 100%;
                min-height: calc(100vh - 20px);
                border-radius: 24px;
                padding: 18px 12px 16px;
            }
            #goal-burst, #countdown-overlay {
                border-radius: 24px;
            }
            h1 {
                font-size: 21px;
                letter-spacing: 3px;
            }
            #maze-grid {
                width: min(82vw, 320px);
                height: min(82vw, 320px);
            }
            #controls {
                width: min(64vw, 190px);
                gap: 8px;
            }
            .control-btn {
                height: 50px;
                font-size: 20px;
            }
            .preview-row {
                grid-template-columns: 32px 1fr auto;
            }
            .preview-time {
                display: none;
            }
            .quiz-hero {
                align-items: stretch;
            }
            .quiz-title {
                font-size: 22px;
            }
            .quiz-subtitle {
                font-size: 12px;
            }
            .quiz-topline {
                align-items: flex-start;
            }
            .quiz-progress-pill {
                min-width: 82px;
                font-size: 10px;
            }
        }
        @media (min-width: 700px) {
            body {
                padding: 24px;
            }
            #game-container {
                width: min(92vw, 720px);
                padding: 28px 24px 22px;
            }
            #maze-grid {
                width: min(48vw, 360px);
                height: min(48vw, 360px);
            }
            #controls {
                width: 220px;
            }
            .control-btn {
                height: 60px;
                font-size: 24px;
            }
            #setup, #lobby, #quiz, #waiting, #results {
                max-width: 560px;
                margin: 0 auto;
            }
            .option-btn {
                font-size: 15px;
                padding: 14px;
            }
            .panel {
                padding: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="ambient-orb a"></div>
    <div class="ambient-orb b"></div>
    <div id="game-container">
        <div id="goal-burst">
            <div id="goal-burst-icon">\u2728</div>
            <div id="goal-burst-text">CORE REACHED</div>
        </div>
        <div id="countdown-overlay">
            <div id="countdown-number">3</div>
            <div id="countdown-label">SYNCING START</div>
        </div>

        <div id="setup">
            <div class="setup-shell">
                <div class="eyebrow-chip"><span class="eyebrow-dot"></span>Host Signal Ready</div>
                <div class="setup-title">
                    <h1 id="main-title">MAZEVERSE</h1>
                    <p class="section-kicker">Knowledge Uplink</p>
                    <p class="muted setup-blurb">Prime your callsign, sync with the host, and launch straight into the shared race grid.</p>
                </div>
                <div class="callsign-shell">
                    <div class="callsign-icon">+</div>
                    <input type="text" id="player-name" maxlength="18" placeholder="CALLSIGN">
                </div>
                <div class="setup-actions">
                    <button class="btn" id="join-btn" onclick="joinGame()">INITIALIZE</button>
                    <button class="ghost-btn hidden" id="quick-play-btn" onclick="quickJoinRemembered()"></button>
                    <button class="ghost-btn small hidden" id="change-name-btn" onclick="focusNameField()">USE A DIFFERENT NAME</button>
                </div>
                <div class="status-card">
                    <span class="status-label">Link Status</span>
                    <p id="setup-status">Ready to connect to the host.</p>
                </div>
                <p class="muted setup-footnote">Your callsign stays on this device so you can jump back into the next uplink faster.</p>
            </div>
        </div>

        <div id="lobby" class="hidden">
            <p class="section-kicker">Pilot Sync</p>
            <p>SYNCING PILOTS...</p>
            <p id="player-count" style="font-size: 48px; color: var(--cyan);">1</p>
            <p id="lobby-status" class="muted">Waiting for the host to start the race.</p>
        </div>

        <div id="race" class="hidden">
            <div class="race-shell">
                <p class="section-kicker">Step 1</p>
                <p style="font-size:12px">REACH THE CORE</p>
                <div class="hud-line">
                    <span id="theme-name">Neon Circuit</span>
                    <span id="maze-status">Maze Live</span>
                </div>
                <div id="maze-grid"></div>
                <div id="controls">
                    <div></div><div class="control-btn" onclick="move(0, -1)">&uarr;</div><div></div>
                    <div class="control-btn" onclick="move(-1, 0)">&larr;</div><div></div><div class="control-btn" onclick="move(1, 0)">&rarr;</div>
                    <div></div><div class="control-btn" onclick="move(0, 1)">&darr;</div><div></div>
                </div>
                <div class="maze-legend">
                    <div class="legend-chip"><span class="legend-swatch wall-swatch"></span>Wall</div>
                    <div class="legend-chip"><span class="legend-swatch path-swatch"></span>Path</div>
                    <div class="legend-chip"><span class="legend-swatch visited-swatch"></span>Trail</div>
                    <div class="legend-chip"><span class="legend-swatch goal-swatch"></span>Core</div>
                </div>
            </div>
        </div>

        <div id="quiz" class="hidden">
            <div class="quiz-shell">
                <div class="quiz-hero">
                    <div class="quiz-copy">
                        <div class="quiz-topline">
                            <span class="quiz-step">Step 2: Knowledge Uplink</span>
                        </div>
                        <p class="quiz-title">Lock In Your Answer</p>
                        <p class="quiz-subtitle">Read fast, choose cleanly, and keep your score climbing before the next prompt arrives.</p>
                    </div>
                    <span id="q-count" class="quiz-progress-pill">Question 1 of 5</span>
                </div>
                <div class="quiz-progress-bar"><div id="quiz-progress-fill" class="quiz-progress-fill"></div></div>
                <div id="feedback-emoji"></div>
                <div class="quiz-question-card">
                    <p id="q-text"></p>
                </div>
                <div id="options-box"></div>
                <div id="answer-reveal" class="hidden"></div>
            </div>
        </div>

        <div id="waiting" class="hidden">
            <p class="section-kicker">Transmission Hold</p>
            <h2 class="accent">UPLINK COMPLETE</h2>
            <p class="success">Your run has been saved.</p>
            <div class="score-chip" id="waiting-score">Final Score: 0/100</div>
            <div class="panel">
                <p id="waiting-message">Waiting for the other pilots to finish...</p>
                <p id="waiting-progress" class="muted">0 of 0 finished</p>
                <div id="waiting-preview-list"></div>
            </div>
        </div>

        <div id="results" class="hidden">
            <p class="section-kicker">Final Ranking</p>
            <h2 id="res-msg" style="color:var(--success)">MISSION COMPLETE</h2>
            <p id="winner-display"></p>
            <div class="score-chip" id="player-summary">Your Score: 0/100</div>
            <div class="panel">
                <p class="muted">Final ranking is ordered by total marks, then fastest completion time.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Pilot</th>
                            <th>Score</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody id="results-table-body"></tbody>
                </table>
            </div>
            <p class="muted">When the host opens a new session, you can play again right here.</p>
        </div>
    </div>

    <script>
        let socket = null;
        const STORAGE_KEY = "mazeverse_mobile_callsign";
        let myName = "";
        let maze = [];
        let playerPos = {x: 0, y: 0};
        let visitedTiles = new Set();
        let quizMarks = 0;
        let raceMarks = 0;
        let currentQ = 0;
        let lastSubmittedTotal = 0;
        let hasJoined = false;
        let activeQuestions = [];
        let currentThemeName = "Neon Circuit";
        let audioUnlocked = false;
        let audioContext = null;
        let countdownRunning = false;
        let socketReady = false;
        let answerLocked = false;
        let currentRenderedOptions = [];

        try {
            if (typeof io === "function") {
                socket = io();
            }
        } catch (error) {
            socket = null;
        }

        function setSetupStatus(message) {
            const status = document.getElementById("setup-status");
            if (status) {
                status.innerText = message;
            }
        }

        function getRememberedName() {
            try {
                return (localStorage.getItem(STORAGE_KEY) || "").trim().toUpperCase();
            } catch (error) {
                return "";
            }
        }

        function rememberName(name) {
            if (!name) {
                return;
            }
            try {
                localStorage.setItem(STORAGE_KEY, name);
            } catch (error) {
                // Some mobile browsers block storage in private or embedded views.
            }
        }

        function showSection(sectionId) {
            ["setup", "lobby", "race", "quiz", "waiting", "results"].forEach((id) => {
                document.getElementById(id).classList.toggle("hidden", id !== sectionId);
            });
        }

        function ensureAudio() {
            try {
                if (audioUnlocked) {
                    return;
                }
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (!AudioCtx) {
                    return;
                }
                audioContext = audioContext || new AudioCtx();
                if (audioContext.state === "suspended") {
                    audioContext.resume();
                }
                audioUnlocked = true;
            } catch (error) {
                audioUnlocked = false;
            }
        }

        function playTone(frequency, duration, type, volume) {
            if (!audioUnlocked || !audioContext) {
                return;
            }
            const osc = audioContext.createOscillator();
            const gain = audioContext.createGain();
            osc.type = type || "sine";
            osc.frequency.value = frequency;
            gain.gain.value = volume || 0.03;
            osc.connect(gain);
            gain.connect(audioContext.destination);
            const now = audioContext.currentTime;
            gain.gain.setValueAtTime(volume || 0.03, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
            osc.start(now);
            osc.stop(now + duration);
        }

        function playFeedbackSound(kind) {
            ensureAudio();
            if (kind === "countdown") {
                playTone(440, 0.12, "square", 0.025);
            } else if (kind === "go") {
                playTone(660, 0.14, "triangle", 0.03);
                setTimeout(() => playTone(880, 0.18, "triangle", 0.025), 90);
            } else if (kind === "move") {
                playTone(310, 0.05, "triangle", 0.015);
            } else if (kind === "correct") {
                playTone(740, 0.11, "triangle", 0.028);
                setTimeout(() => playTone(960, 0.13, "triangle", 0.024), 80);
            } else if (kind === "wrong") {
                playTone(250, 0.13, "sawtooth", 0.02);
            } else if (kind === "goal") {
                playTone(520, 0.12, "triangle", 0.03);
                setTimeout(() => playTone(720, 0.14, "triangle", 0.026), 90);
                setTimeout(() => playTone(980, 0.18, "triangle", 0.022), 180);
            }
        }

        function showGoalBurst(onDone) {
            const overlay = document.getElementById("goal-burst");
            overlay.style.display = "flex";
            playFeedbackSound("goal");
            setTimeout(() => {
                overlay.style.display = "none";
                if (typeof onDone === "function") {
                    onDone();
                }
            }, 950);
        }

        function renderWaitingPreview(partialResults) {
            const list = document.getElementById("waiting-preview-list");
            const results = Array.isArray(partialResults) ? partialResults : [];
            list.innerHTML = "";
            if (!results.length) {
                list.innerHTML = '<p class="muted">No pilots have finished yet.</p>';
                return;
            }

            results.slice(0, 4).forEach((entry) => {
                const row = document.createElement("div");
                row.className = "preview-row";
                row.innerHTML =
                    '<span class="preview-rank">#' + entry.rank + "</span>" +
                    '<span class="preview-name">' + entry.name + "</span>" +
                    '<span class="preview-score">' + entry.total + "/100</span>" +
                    '<span class="preview-time">' + entry.completion_time + "</span>";
                list.appendChild(row);
            });
        }

        function applyTheme(theme) {
            const root = document.documentElement;
            const safeTheme = theme || {};
            const mappings = {
                "--theme-top": safeTheme.bg_top || "#0a1234",
                "--theme-mid": safeTheme.bg_mid || "#12225c",
                "--theme-accent": safeTheme.accent || "#00f5ff",
                "--theme-accent-soft": safeTheme.accent_soft || "#4fc3ff",
                "--theme-path": safeTheme.path || "#10234d",
                "--theme-path-alt": safeTheme.path_alt || "#0a1732",
                "--theme-wall": safeTheme.wall || "#14264c",
                "--theme-wall-alt": safeTheme.wall_alt || "#091126",
                "--theme-goal": safeTheme.goal || "#ff50be",
                "--theme-goal-soft": safeTheme.goal_soft || "#ff96d4",
                "--theme-panel-glow": safeTheme.panel_glow || "rgba(0, 170, 255, 0.18)"
            };

            Object.entries(mappings).forEach(([key, value]) => root.style.setProperty(key, value));
            currentThemeName = safeTheme.name || "Neon Circuit";
            document.getElementById("theme-name").innerText = currentThemeName;
            document.getElementById("countdown-label").innerText = currentThemeName.toUpperCase();
        }

        function startCountdown(seconds, onDone) {
            if (countdownRunning) {
                return;
            }
            const overlay = document.getElementById("countdown-overlay");
            const number = document.getElementById("countdown-number");
            let remaining = Math.max(1, Number(seconds) || 3);
            countdownRunning = true;

            overlay.style.display = "flex";
            number.innerText = remaining;
            playFeedbackSound("countdown");

            const tick = () => {
                remaining -= 1;
                if (remaining <= 0) {
                    number.innerText = "GO";
                    playFeedbackSound("go");
                    setTimeout(() => {
                        overlay.style.display = "none";
                        countdownRunning = false;
                        if (typeof onDone === "function") {
                            onDone();
                        }
                    }, 550);
                    return;
                }
                number.innerText = remaining;
                playFeedbackSound("countdown");
                setTimeout(tick, 700);
            };

            setTimeout(tick, 700);
        }

        function updateRememberedNameUI() {
            const remembered = getRememberedName();
            const quickPlayBtn = document.getElementById("quick-play-btn");
            const changeNameBtn = document.getElementById("change-name-btn");
            const nameInput = document.getElementById("player-name");

            if (remembered) {
                nameInput.value = remembered;
                quickPlayBtn.classList.remove("hidden");
                changeNameBtn.classList.remove("hidden");
                quickPlayBtn.innerText = "PLAY AGAIN AS " + remembered;
            } else {
                quickPlayBtn.classList.add("hidden");
                changeNameBtn.classList.add("hidden");
            }
        }

        function focusNameField() {
            document.getElementById("player-name").focus();
            document.getElementById("player-name").select();
        }

        function resetRunState() {
            maze = [];
            playerPos = {x: 0, y: 0};
            visitedTiles = new Set(["0,0"]);
            quizMarks = 0;
            raceMarks = 0;
            currentQ = 0;
            activeQuestions = [];
            lastSubmittedTotal = 0;
            document.getElementById("feedback-emoji").innerText = "";
            document.getElementById("results-table-body").innerHTML = "";
            document.getElementById("waiting-score").innerText = "Final Score: 0/100";
            document.getElementById("player-summary").innerText = "Your Score: 0/100";
            document.getElementById("maze-status").innerText = "Maze Live";
            document.getElementById("theme-name").innerText = currentThemeName;
            document.getElementById("waiting-preview-list").innerHTML = "";
            document.getElementById("goal-burst").style.display = "none";
            document.getElementById("countdown-overlay").style.display = "none";
            document.getElementById("answer-reveal").innerHTML = "";
            document.getElementById("answer-reveal").className = "hidden";
            countdownRunning = false;
            answerLocked = false;
            currentRenderedOptions = [];
        }

        function prepareForLobby() {
            resetRunState();
            showSection("lobby");
            document.getElementById("lobby-status").innerText = "Waiting for the host to start the race.";
        }

        function quickJoinRemembered() {
            ensureAudio();
            const remembered = getRememberedName();
            if (!remembered) {
                focusNameField();
                return;
            }

            document.getElementById("player-name").value = remembered;
            joinGame();
        }

        function cloneMazeLayout(layout) {
            return (layout || []).map((row) => row.slice());
        }

        function drawMaze() {
            const grid = document.getElementById("maze-grid");
            grid.innerHTML = "";
            for (let y = 0; y < 10; y++) {
                for (let x = 0; x < 10; x++) {
                    const cell = document.createElement("div");
                    cell.className = "cell " + (maze[y][x] === 1 ? "wall" : "path");
                    if (visitedTiles.has(x + "," + y) && maze[y][x] === 0) {
                        cell.classList.add("visited");
                    }
                    if (x === playerPos.x && y === playerPos.y) {
                        cell.classList.add("player");
                    } else if (x === 0 && y === 0) {
                        cell.classList.add("start");
                    } else if (x === 9 && y === 9) {
                        cell.classList.add("goal");
                    }
                    grid.appendChild(cell);
                }
            }
        }

        function move(dx, dy) {
            const nx = playerPos.x + dx;
            const ny = playerPos.y + dy;
            if (nx >= 0 && nx < 10 && ny >= 0 && ny < 10 && maze[ny][nx] === 0) {
                playerPos.x = nx;
                playerPos.y = ny;
                visitedTiles.add(nx + "," + ny);
                document.getElementById("maze-status").innerText = "Core Route " + visitedTiles.size;
                playFeedbackSound("move");
                drawMaze();
                if (nx === 9 && ny === 9) {
                    raceMarks = 50;
                    showGoalBurst(() => startQuiz());
                }
            }
        }

        function startQuiz() {
            if (!activeQuestions.length) {
                finishAll();
                return;
            }
            showSection("quiz");
            showQuestion();
        }

        function buildShuffledOptions(question) {
            const options = (question.a || []).map((text, originalIndex) => ({ text, originalIndex }));
            for (let i = options.length - 1; i > 0; i -= 1) {
                const swapIndex = Math.floor(Math.random() * (i + 1));
                const temp = options[i];
                options[i] = options[swapIndex];
                options[swapIndex] = temp;
            }
            return options;
        }

        function showQuestion() {
            answerLocked = false;
            const q = activeQuestions[currentQ];
            document.getElementById("q-text").innerText = q.q;
            document.getElementById("q-count").innerText = "Question " + (currentQ + 1) + " of " + activeQuestions.length;
            document.getElementById("quiz-progress-fill").style.width = ((currentQ + 1) / activeQuestions.length * 100) + "%";
            const box = document.getElementById("options-box");
            const reveal = document.getElementById("answer-reveal");
            box.innerHTML = "";
            reveal.innerHTML = "";
            reveal.className = "hidden";
            currentRenderedOptions = buildShuffledOptions(q);
            currentRenderedOptions.forEach((option, renderedIndex) => {
                const button = document.createElement("button");
                button.className = "option-btn";
                button.innerText = option.text;
                button.dataset.optionIndex = renderedIndex;
                button.onclick = () => checkAnswer(renderedIndex);
                box.appendChild(button);
            });
        }

        function checkAnswer(idx) {
            if (answerLocked) {
                return;
            }
            answerLocked = true;
            const feedback = document.getElementById("feedback-emoji");
            const q = activeQuestions[currentQ];
            const correctIndex = q.c;
            const reveal = document.getElementById("answer-reveal");
            const optionButtons = Array.from(document.querySelectorAll("#options-box .option-btn"));
            const selectedOption = currentRenderedOptions[idx];
            const isCorrect = selectedOption && selectedOption.originalIndex === correctIndex;

            optionButtons.forEach((button, buttonIndex) => {
                button.disabled = true;
                const renderedOption = currentRenderedOptions[buttonIndex];
                if (renderedOption && renderedOption.originalIndex === correctIndex) {
                    button.classList.add("correct-answer");
                } else if (buttonIndex === idx && !isCorrect) {
                    button.classList.add("wrong-answer");
                } else {
                    button.classList.add("dimmed-answer");
                }
            });

            if (isCorrect) {
                quizMarks += 10;
                feedback.innerText = "\u2705";
                playFeedbackSound("correct");
                reveal.className = "correct";
                reveal.innerHTML =
                    '<span class="reveal-label">Answer Locked</span>' +
                    "Correct. " + q.a[correctIndex] + " is the right answer.";
            } else {
                feedback.innerText = "\u274C";
                playFeedbackSound("wrong");
                reveal.className = "wrong";
                reveal.innerHTML =
                    '<span class="reveal-label">Correct Answer</span>' +
                    q.a[correctIndex];
            }

            setTimeout(() => {
                feedback.innerText = "";
                currentQ += 1;
                if (currentQ >= activeQuestions.length) {
                    finishAll();
                } else {
                    showQuestion();
                }
            }, 800);
        }

        function finishAll() {
            lastSubmittedTotal = raceMarks + quizMarks;
            if (socket) {
                socket.emit("finish", {
                    name: myName,
                    race_marks: raceMarks,
                    quiz_marks: quizMarks,
                    total: lastSubmittedTotal
                });
            }
            document.getElementById("waiting-score").innerText = "Final Score: " + lastSubmittedTotal + "/100";
            renderWaitingPreview([]);
            showSection("waiting");
        }

        function joinGame() {
            try {
                ensureAudio();
                const enteredName = document.getElementById("player-name").value.trim().toUpperCase() || "STUDENT";
                myName = enteredName;
                rememberName(myName);
                if (!socket) {
                    setSetupStatus("The uplink could not load its network client. Reload this page and try again.");
                    return;
                }
                hasJoined = true;
                setSetupStatus(socket.connected ? "Joining host..." : "Connecting to host...");
                socket.emit("join", {name: myName});
                prepareForLobby();
            } catch (error) {
                setSetupStatus("Could not initialize this device. Reload the page and try again.");
            }
        }

        function renderResults(payload) {
            const results = payload.results || [];
            const winnerData = payload.winner || null;
            const tableBody = document.getElementById("results-table-body");
            tableBody.innerHTML = "";

            results.forEach((entry) => {
                const row = document.createElement("tr");
                row.innerHTML =
                    "<td>" + entry.rank + "</td>" +
                    "<td>" + entry.name + "</td>" +
                    "<td>" + entry.total + "/100</td>" +
                    "<td>" + entry.completion_time + "</td>";
                tableBody.appendChild(row);
            });

            const myEntry = results.find((entry) => entry.name === myName);
            const summaryText = myEntry
                ? "Your Score: " + myEntry.total + "/100 | Time: " + myEntry.completion_time
                : "Your Score: " + lastSubmittedTotal + "/100";

            document.getElementById("player-summary").innerText = summaryText;
            document.getElementById("res-msg").innerText = winnerData && winnerData.name === myName ? "VICTORY" : "RACE COMPLETE";
            document.getElementById("winner-display").innerText = winnerData
                ? "Winner: " + winnerData.name + " with " + winnerData.total + "/100"
                : "Final standings are ready.";
            showSection("results");
        }

        if (socket) {
            socket.on("connect", () => {
                socketReady = true;
                updateRememberedNameUI();
                applyTheme({ name: "Neon Circuit" });
                setSetupStatus("Ready to connect to the host.");
            });

            socket.on("disconnect", () => {
                socketReady = false;
                setSetupStatus("Connection lost. Reload the page and reconnect.");
            });

            socket.on("connect_error", () => {
                socketReady = false;
                setSetupStatus("Could not reach the desktop host. Check that the game is open on the same network.");
            });

            socket.on("player_update", (payload) => {
                const playerCount = typeof payload === "number" ? payload : (payload.count || 0);
                document.getElementById("player-count").innerText = playerCount;

                if (payload && typeof payload === "object") {
                    if (payload.race_started) {
                        document.getElementById("lobby-status").innerText = "Race in progress. Finish strong.";
                    } else if (payload.race_finished) {
                        document.getElementById("lobby-status").innerText = "Results are locked in.";
                    } else {
                        document.getElementById("lobby-status").innerText = payload.ready_count > 0
                            ? payload.ready_count + " pilot(s) are ready for the next session."
                            : "Waiting for the host to start the race.";
                    }

                    if (!document.getElementById("waiting").classList.contains("hidden")) {
                        const activeCount = payload.active_count || 0;
                        const finishedCount = payload.finished_count || 0;
                        document.getElementById("waiting-progress").innerText = finishedCount + " of " + activeCount + " finished";
                        renderWaitingPreview(payload.partial_results || []);
                    }
                }
            });

            socket.on("race_start", (payload) => {
                if (!hasJoined) {
                    return;
                }
                resetRunState();
                applyTheme(payload && payload.theme ? payload.theme : null);
                maze = cloneMazeLayout(payload && payload.maze ? payload.maze : []);
                activeQuestions = Array.isArray(payload && payload.questions) ? payload.questions : [];
                if (!maze.length) {
                    return;
                }
                showSection("race");
                startCountdown(payload && payload.countdown_seconds ? payload.countdown_seconds : 3, () => {
                    drawMaze();
                });
            });

            socket.on("results_ready", (payload) => {
                renderResults(payload);
            });

            socket.on("session_reset", () => {
                resetRunState();
                updateRememberedNameUI();
                hasJoined = false;
                showSection("setup");
            });
        } else {
            setSetupStatus("The uplink client could not start. Reload the page and try again.");
        }

        document.getElementById("player-name").addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                joinGame();
            }
        });

        document.addEventListener("pointerdown", ensureAudio, { once: true });
        window.addEventListener("error", () => {
            const status = document.getElementById("setup-status");
            if (status && !hasJoined) {
                status.innerText = "A page error occurred. Reload the uplink page and try again.";
            }
        });

        updateRememberedNameUI();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@socketio.on("join")
def handle_join(data):
    incoming_name = str(data.get("name", "STUDENT")).strip().upper() or "STUDENT"
    existing = players.get(request.sid, {})
    players[request.sid] = {
        "name": incoming_name,
        "finished": existing.get("finished", False),
        "ready_for_replay": not race_started and not race_finished,
        "race_marks": existing.get("race_marks", 0),
        "quiz_marks": existing.get("quiz_marks", 0),
        "total": existing.get("total", 0),
        "completion_seconds": existing.get("completion_seconds"),
        "start_time": existing.get("start_time"),
    }
    broadcast_player_update()


@socketio.on("finish")
def handle_finish(data):
    player = players.get(request.sid)
    if not player or not race_started or request.sid not in active_race_sids:
        return

    if player.get("finished"):
        return

    completion_seconds = max(0.0, time.time() - float(player.get("start_time") or time.time()))
    player["finished"] = True
    player["ready_for_replay"] = False
    player["race_marks"] = int(data.get("race_marks", 0) or 0)
    player["quiz_marks"] = int(data.get("quiz_marks", 0) or 0)
    player["total"] = int(data.get("total", 0) or 0)
    player["completion_seconds"] = completion_seconds

    broadcast_player_update()
    maybe_finalize_race()


@socketio.on("disconnect")
def handle_disconnect():
    was_active_racer = request.sid in active_race_sids
    players.pop(request.sid, None)
    if was_active_racer:
        active_race_sids.discard(request.sid)
        maybe_finalize_race()
    broadcast_player_update()


def run_server(host="0.0.0.0", port=8000):
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )


def start_background_server():
    threading.Thread(target=run_server, daemon=True).start()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
