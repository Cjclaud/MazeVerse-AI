# ai_engine.py
# -------------------------------------------------
# Adaptive AI engine for the Intelligent Maze Game
# Handles:
# - player profiling
# - performance analysis
# - adaptive difficulty recommendations
# - post-level summaries
# -------------------------------------------------

from dataclasses import dataclass


@dataclass
class PlayerMetrics:
    level: int
    difficulty: str
    moves: int
    wrong_turns: int
    manual_hints_used: int
    auto_hints_used: int
    time_taken: int
    maze_rows: int
    maze_cols: int
    fog_enabled: bool


@dataclass
class PlayerProfile:
    label: str
    score: int
    summary: str


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def calculate_efficiency_ratio(moves, maze_rows, maze_cols):
    """
    Compare actual moves to a rough expected maze effort.
    Lower is better.
    """
    expected_moves = max(maze_rows + maze_cols, 1)
    return moves / expected_moves


def calculate_hint_pressure(manual_hints_used, auto_hints_used):
    return manual_hints_used * 10 + auto_hints_used * 14


def calculate_wrong_turn_pressure(wrong_turns):
    return wrong_turns * 6


def calculate_time_pressure(time_taken, maze_rows, maze_cols):
    """
    Rough expected time formula based on maze size.
    """
    expected_time = (maze_rows + maze_cols) * 2
    if expected_time <= 0:
        return 0

    ratio = time_taken / expected_time
    if ratio <= 1.0:
        return 0
    elif ratio <= 1.4:
        return 8
    elif ratio <= 1.8:
        return 16
    elif ratio <= 2.3:
        return 24
    return 32


def calculate_performance_score(metrics: PlayerMetrics):
    """
    Returns a score out of 100.
    Higher = better performance.
    """
    score = 100

    efficiency_ratio = calculate_efficiency_ratio(
        metrics.moves, metrics.maze_rows, metrics.maze_cols
    )

    if efficiency_ratio <= 1.2:
        score -= 0
    elif efficiency_ratio <= 1.6:
        score -= 8
    elif efficiency_ratio <= 2.0:
        score -= 16
    elif efficiency_ratio <= 2.6:
        score -= 24
    else:
        score -= 34

    score -= calculate_hint_pressure(
        metrics.manual_hints_used, metrics.auto_hints_used
    )
    score -= calculate_wrong_turn_pressure(metrics.wrong_turns)
    score -= calculate_time_pressure(
        metrics.time_taken, metrics.maze_rows, metrics.maze_cols
    )

    if metrics.fog_enabled:
        score += 5

    return clamp(int(score), 0, 100)


def classify_player(metrics: PlayerMetrics):
    score = calculate_performance_score(metrics)

    if score >= 80:
        return PlayerProfile(
            label="Expert",
            score=score,
            summary="Fast, efficient, and mostly independent."
        )
    elif score >= 55:
        return PlayerProfile(
            label="Intermediate",
            score=score,
            summary="Good control, but still benefits from support."
        )
    return PlayerProfile(
        label="Beginner",
        score=score,
        summary="Needs more guidance and a lighter challenge curve."
    )


def get_adaptive_recommendation(profile: PlayerProfile, current_level: int):
    """
    Returns gameplay recommendations for future levels.
    These are modifiers only. Your main game decides how to use them.
    """
    if profile.label == "Expert":
        return {
            "next_profile": profile.label,
            "maze_size_bonus": 1,
            "fog_bonus": True,
            "hint_preview_steps": 3,
            "auto_help_delay": 6.0,
            "reward_multiplier": 1.15,
            "message": f"AI detected {profile.label} performance. Increasing challenge."
        }

    if profile.label == "Intermediate":
        return {
            "next_profile": profile.label,
            "maze_size_bonus": 0,
            "fog_bonus": True,
            "hint_preview_steps": 4,
            "auto_help_delay": 4.5,
            "reward_multiplier": 1.0,
            "message": f"AI detected {profile.label} performance. Keeping balanced difficulty."
        }

    return {
        "next_profile": profile.label,
        "maze_size_bonus": -1,
        "fog_bonus": False,
        "hint_preview_steps": 6,
        "auto_help_delay": 3.0,
        "reward_multiplier": 0.9,
        "message": f"AI detected {profile.label} performance. Easing the next challenge."
    }


def build_post_level_report(metrics: PlayerMetrics):
    profile = classify_player(metrics)
    recommendation = get_adaptive_recommendation(profile, metrics.level)

    return {
        "profile": profile.label,
        "profile_score": profile.score,
        "profile_summary": profile.summary,
        "recommendation": recommendation,
    }