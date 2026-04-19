# main.py
import sys
import time
import random
import math
import os
from collections import deque, Counter

import pygame

import settings as game_settings
from settings import *
from app_paths import get_user_sound_dir, get_user_music_dir, ensure_user_audio_readme, resolve_existing_path
from splash_screen import SplashScreen
from main_menu import MainMenu
from settings_menu import SettingsMenu
from level_select import LevelSelect
from maze import generate_maze
from solver import bfs_solve, a_star_solve
from ai_engine import PlayerMetrics, build_post_level_report
from game_features import place_traps, place_powerups, place_checkpoint
from analytics import record_session, get_summary, get_recent_sessions
from advanced_tracking import (
    create_empty_heatmap,
    record_heatmap_visit,
    get_heatmap_max,
    build_replay_entry,
    save_replay,
    compare_player_vs_ai,
)
from score_manager import get_best_score, update_best_score
from progress_manager import load_progress
import qrcode
import mobile_server
import socket
import threading

def generate_qr_surface(url, size=300):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    
    qr_width = len(matrix)
    cell_size = size // qr_width
    actual_size = qr_width * cell_size
    
    surf = pygame.Surface((actual_size, actual_size))
    surf.fill((255, 255, 255))
    
    for r in range(qr_width):
        for c in range(qr_width):
            if matrix[r][c]:
                pygame.draw.rect(surf, (0, 0, 0), (c * cell_size, r * cell_size, cell_size, cell_size))
    
    return surf

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"

# -------------------------------------------------
# PYGAME INITIALIZATION
# -------------------------------------------------
pygame.init()
ensure_user_audio_readme()
AUDIO_AVAILABLE = True
try:
    pygame.mixer.init()
except pygame.error as e:
    AUDIO_AVAILABLE = False
    print("Audio initialization skipped:", e)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
try:
    window_icon = pygame.image.load(resolve_existing_path("assets/icon.ico"))
    pygame.display.set_icon(window_icon)
except Exception:
    pass
clock = pygame.time.Clock()

# -------------------------------------------------
# BACKGROUND IMAGE
# -------------------------------------------------
try:
    bg_image = pygame.image.load(resolve_existing_path("assets/images/game_bg.png")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
except:
    bg_image = None

# -------------------------------------------------
# FONTS
# -------------------------------------------------
font_title = pygame.font.SysFont("arial", 34, bold=True)
font_text = pygame.font.SysFont("arial", 22)
font_small = pygame.font.SysFont("arial", 18)
font_tiny = pygame.font.SysFont("arial", 16)
font_menu = pygame.font.SysFont("arial", 28, bold=True)

# -------------------------------------------------
# Load Sounds
# -------------------------------------------------
CUSTOM_SOUND_FILES = {
    "move": ["move.wav", "move.mp3", "move.ogg"],
    "win": ["win.wav", "win.mp3", "win.ogg"],
    "click": ["click.wav", "click.mp3", "click.ogg"],
    "wall_hit": ["wall_hit.wav", "wall_hit.wav.mp3", "wall_hit.mp3", "wall_hit.ogg"],
    "trap_hit": ["trap_hit.wav", "trap_hit.wav.mp3", "trap_hit.mp3", "trap_hit.ogg"],
    "powerup": ["powerup.wav", "powerup.wav.mp3", "powerup.mp3", "powerup.ogg"],
}


def _user_audio_candidates(file_names, subdir):
    base_dir = get_user_sound_dir() if subdir == "sounds" else get_user_music_dir()
    return [os.path.join(base_dir, name) for name in file_names]


def resolve_sound_candidates(key, *default_paths):
    user_files = _user_audio_candidates(CUSTOM_SOUND_FILES.get(key, []), "sounds")
    return [*user_files, *default_paths]


def _music_override_paths(name):
    candidates = [os.path.join(get_user_music_dir(), name)]

    base_name, ext = os.path.splitext(name)
    if ext:
        for other_ext in (".mp3", ".wav", ".ogg"):
            if other_ext != ext:
                candidates.append(os.path.join(get_user_music_dir(), base_name + other_ext))
    else:
        for other_ext in (".mp3", ".wav", ".ogg"):
            candidates.append(os.path.join(get_user_music_dir(), name + other_ext))

    return candidates


def load_sound_from_candidates(*paths):
    if not (SOUND_ENABLED and AUDIO_AVAILABLE):
        return None

    for path in paths:
        if not path:
            continue
        try:
            resolved = resolve_existing_path(path)
            if os.path.exists(resolved):
                return pygame.mixer.Sound(resolved)
        except Exception:
            continue

    return None


move_sound = load_sound_from_candidates(
    *resolve_sound_candidates(
        "move",
        getattr(game_settings, "MOVE_SOUND_FILE", None),
        "assets/sounds/move.wav",
    ),
)
win_sound = load_sound_from_candidates(
    *resolve_sound_candidates(
        "win",
        getattr(game_settings, "WIN_SOUND_FILE", None),
        "assets/sounds/win.wav",
    ),
)
click_sound = load_sound_from_candidates(
    *resolve_sound_candidates(
        "click",
        getattr(game_settings, "CLICK_SOUND_FILE", None),
        "assets/sounds/click.wav",
    ),
)
wall_hit_sound = load_sound_from_candidates(
    *resolve_sound_candidates(
        "wall_hit",
        getattr(game_settings, "WALL_HIT_SOUND_FILE", None),
        "assets/sounds/wall_hit.wav",
        getattr(game_settings, "CLICK_SOUND_FILE", None),
        "assets/sounds/click.wav",
    ),
)
trap_hit_sound = load_sound_from_candidates(
    *resolve_sound_candidates(
        "trap_hit",
        getattr(game_settings, "TRAP_HIT_SOUND_FILE", None),
        "assets/sounds/trap_hit.wav",
        getattr(game_settings, "CLICK_SOUND_FILE", None),
        "assets/sounds/click.wav",
    ),
)
powerup_sound = load_sound_from_candidates(
    *resolve_sound_candidates(
        "powerup",
        getattr(game_settings, "POWERUP_SOUND_FILE", None),
        "assets/sounds/powerup.wav",
        getattr(game_settings, "CLICK_SOUND_FILE", None),
        "assets/sounds/click.wav",
    ),
)

def _clamp01(value):
    return max(0.0, min(1.0, float(value)))

# -------------------------------------------------
# GAME STATES
# -------------------------------------------------
STATE_SPLASH = "splash"
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_WON = "won"
STATE_LOST = "lost"
STATE_MOBILE_RACE = "mobile_race"

game_state = STATE_SPLASH

# -------------------------------------------------
# DIFFICULTY / LEVEL SETTINGS
# -------------------------------------------------
difficulty = "Medium"
level = 1
current_level = 1

difficulty_config = {
    "Easy": (10, 14),
    "Medium": (15, 20),
    "Hard": (18, 24),
}

runtime_settings = {
    "music": MUSIC_ENABLED and AUDIO_AVAILABLE,
    "sfx": SOUND_ENABLED and AUDIO_AVAILABLE,
    "difficulty": difficulty,
    "game_mode": "Solo",
    "ai_difficulty": "Medium",
    "show_hints": AUTO_HELP_DEFAULT,
    "timer": True,
    "fog": FOG_OF_WAR_ENABLED,
}

rows, cols = difficulty_config[difficulty]
cell_size = CELL_SIZE

# -------------------------------------------------
# GAME VARIABLES
# -------------------------------------------------
current_maze = []
start_pos = (0, 0)
goal_pos = (rows - 1, cols - 1)

player_row, player_col = start_pos
moves_count = 0

ai_path = []
ai_explored = []
ai_mode = "Not active"

visible_explored = []
visible_path = []

animating = False
animation_stage = "none"
animation_index = 0
animation_delay = 2
animation_counter = 0

start_time = 0
player_time = 0
final_player_time = 0
ai_time = 0
timer_running = False
win_time = None

# -------------------------------------------------
# MOBILE RACE VARIABLES
# -------------------------------------------------
qr_code_surface = None
mobile_server_thread = None
mobile_server_started = False

# -------------------------------------------------
# ADAPTIVE HELP / HINT SYSTEM
# -------------------------------------------------
auto_help_enabled = AUTO_HELP_DEFAULT
hint_path = []
hint_level = 0
hint_message = "Hints ready"
help_state = "Normal"
manual_hints_used = 0
auto_hints_used = 0

last_move_time = 0
position_history = deque(maxlen=18)
wrong_turns = 0
best_distance_seen = None
last_distance_to_goal = None
last_auto_hint_time = 0

# -------------------------------------------------
# ADAPTIVE AI PROFILE
# -------------------------------------------------
ai_profile_label = "Unknown"
ai_profile_score = 0
ai_profile_summary = "No adaptive profile yet"
ai_adaptive_message = "AI analysis pending"
ai_adaptive_config = {
    "maze_size_bonus": 0,
    "fog_bonus": False,
    "hint_preview_steps": HINT_PREVIEW_STEPS,
    "auto_help_delay": 4.0,
    "reward_multiplier": 1.0,
}

# -------------------------------------------------
# SCORE / RECORDS / FOG
# -------------------------------------------------
score = 0
total_score = 0
best_score = 0
new_record = False
level_reward_applied = False
win_rewatch_mode = False

level_time_limit = 0
level_failed_reason = ""

pause_options = [
    "Resume",
    "Restart Level",
    "Toggle Fog",
    "Toggle Auto Help",
    "Run BFS",
    "Run A*",
    "Replay Run",
    "Ghost AI",
    "Quit to Menu",
]

pause_selected = 0
pause_overlay_anim = 0.0
last_wall_hit_sfx_time = 0.0
WALL_HIT_SFX_COOLDOWN = 0.14

# Music playback state
music_mode = None
music_tracks = []
music_track_index = -1
music_duck_until = 0.0

move_volume_mult = float(getattr(game_settings, "SFX_MOVE_VOLUME_MULT", 1.0))
win_volume_mult = float(getattr(game_settings, "SFX_WIN_VOLUME_MULT", 1.0))
click_volume_mult = float(getattr(game_settings, "SFX_CLICK_VOLUME_MULT", 1.0))
wall_hit_volume_mult = float(getattr(game_settings, "SFX_WALL_HIT_VOLUME_MULT", 1.0))
trap_hit_volume_mult = float(getattr(game_settings, "SFX_TRAP_HIT_VOLUME_MULT", 1.0))
powerup_volume_mult = float(getattr(game_settings, "SFX_POWERUP_VOLUME_MULT", 1.0))

# Smooth player movement variables
render_player_x = 0
render_player_y = 0
target_player_x = 0
target_player_y = 0

# -------------------------------------------------
# PARTICLE BACKGROUND
# -------------------------------------------------
particles = []
for _ in range(55):
    particles.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "r": random.randint(1, 3),
        "speed": random.uniform(0.15, 0.6),
        "alpha": random.randint(60, 180)
    })

fog_enabled = FOG_OF_WAR_ENABLED
splash_screen = SplashScreen()
menu_screen = MainMenu()
settings_screen = SettingsMenu()
level_select_screen = LevelSelect(total_levels=18)

# -------------------------------------------------
# GAME FEATURES
# -------------------------------------------------
traps = []
powerups = []
checkpoint = None
checkpoint_pos = None
shield_active = False
reveal_timer = 0
score_boost_active = False
score_boost_timer = 0

# -------------------------------------------------
# ADVANCED TRACKING
# -------------------------------------------------
heatmap = []
player_replay_path = []
replay_mode = False
replay_index = 0
replay_counter = 0
replay_delay = 6

ghost_ai_visible = False
ghost_ai_index = 0
ghost_ai_counter = 0
ghost_ai_delay = 6
ghost_ai_finished = False

ghost_player_pos = None
ghost_ai_pos = None

active_theme_name = THEME_ROTATION[0] if THEME_ROTATION else "Neon Circuit"
active_theme_config = dict(THEME_RULES.get(active_theme_name, {}))

comparison_result = {
    "player_steps": 0,
    "ai_steps": 0,
    "difference": 0,
    "verdict": "No comparison yet",
}

menu_screen.runtime_settings = runtime_settings
settings_screen.runtime_settings = runtime_settings

# Pass click_sound to menus
if SOUND_ENABLED and click_sound:
    menu_screen.set_click_sound(click_sound)
    settings_screen.set_click_sound(click_sound)


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def draw_text(text, font, color, x, y):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))


def draw_glow_rect(x, y, width, height, color, layers=4, radius=12):
    glow_surface = pygame.Surface((width + layers * 8, height + layers * 8), pygame.SRCALPHA)

    for i in range(layers, 0, -1):
        alpha = max(12, 50 - i * 8)
        pygame.draw.rect(
            glow_surface,
            (*color, alpha),
            (layers * 4 - i * 2, layers * 4 - i * 2, width + i * 4, height + i * 4),
            border_radius=radius + i
        )

    screen.blit(glow_surface, (x - layers * 4, y - layers * 4))


def play_sfx(sound, duck_mult=None, duck_duration=None):
    if runtime_settings["sfx"] and sound is not None:
        sound.play()
        _trigger_music_duck(duck_mult=duck_mult, duck_duration=duck_duration)


def refresh_sound_volumes():
    sfx_on = runtime_settings["sfx"]
    base = float(SOUND_VOLUME) if sfx_on else 0.0

    if move_sound:
        move_sound.set_volume(_clamp01(base * move_volume_mult))
    if win_sound:
        win_sound.set_volume(_clamp01(base * win_volume_mult))
    if click_sound:
        click_sound.set_volume(_clamp01(base * click_volume_mult))
    if wall_hit_sound:
        wall_hit_sound.set_volume(_clamp01(base * wall_hit_volume_mult))
    if trap_hit_sound:
        trap_hit_sound.set_volume(_clamp01(base * trap_hit_volume_mult))
    if powerup_sound:
        powerup_sound.set_volume(_clamp01(base * powerup_volume_mult))


def _music_base_volume():
    mode_mult = getattr(game_settings, "MUSIC_GAMEPLAY_VOLUME_MULT", 1.0)
    if music_mode == "menu":
        mode_mult = getattr(game_settings, "MUSIC_MENU_VOLUME_MULT", 1.0)
    return _clamp01(float(MUSIC_VOLUME) * float(mode_mult))


def _apply_music_volume():
    if not (AUDIO_AVAILABLE and runtime_settings["music"]):
        return

    volume = _music_base_volume()
    now = time.time()

    if getattr(game_settings, "MUSIC_DUCKING_ENABLED", True) and now < music_duck_until:
        override_duck = getattr(game_settings, "_runtime_duck_mult", None)
        if override_duck is None:
            duck_mult = float(getattr(game_settings, "MUSIC_DUCK_VOLUME_MULT", 0.45))
        else:
            duck_mult = float(override_duck)
        volume = _clamp01(volume * duck_mult)

    pygame.mixer.music.set_volume(volume)


def _trigger_music_duck(duck_mult=None, duck_duration=None):
    global music_duck_until

    if not (AUDIO_AVAILABLE and runtime_settings["music"]):
        return

    if not getattr(game_settings, "MUSIC_DUCKING_ENABLED", True):
        return

    if duck_mult is not None:
        duck_mult = _clamp01(duck_mult)
        setattr(game_settings, "_runtime_duck_mult", duck_mult)
    else:
        setattr(game_settings, "_runtime_duck_mult", None)

    duration = duck_duration
    if duration is None:
        duration = float(getattr(game_settings, "MUSIC_DUCK_DURATION_SEC", 0.25))
    music_duck_until = max(music_duck_until, time.time() + max(0.0, duration))
    _apply_music_volume()


def _existing_tracks(paths):
    tracks = []
    for path in paths:
        if isinstance(path, str) and path:
            resolved = resolve_existing_path(path)
            if os.path.exists(resolved):
                tracks.append(resolved)
    return tracks


def _get_menu_tracks():
    configured = getattr(game_settings, "MENU_MUSIC_PLAYLIST", [])
    candidates = []
    for path in configured:
        if isinstance(path, str) and path:
            candidates.extend(_music_override_paths(os.path.basename(path)))
            candidates.append(path)

    tracks = _existing_tracks(candidates)
    if tracks:
        return tracks

    fallback_candidates = _music_override_paths("bg_music.mp3") + ["assets/sounds/bg_music.mp3"]
    fallback = _existing_tracks(fallback_candidates)
    return fallback


def _get_game_tracks(difficulty_name):
    table = getattr(game_settings, "GAMEPLAY_MUSIC_BY_DIFFICULTY", {})
    configured = table.get(difficulty_name, table.get("Medium", []))
    if isinstance(configured, str):
        configured = [configured]

    candidates = []
    for path in configured:
        if isinstance(path, str) and path:
            candidates.extend(_music_override_paths(os.path.basename(path)))
            candidates.append(path)

    tracks = _existing_tracks(candidates)
    if tracks:
        return tracks

    fallback_candidates = _music_override_paths("bg_music.mp3") + ["assets/sounds/bg_music.mp3"]
    fallback = _existing_tracks(fallback_candidates)
    return fallback


def _play_next_music_track():
    global music_track_index

    if not (AUDIO_AVAILABLE and runtime_settings["music"] and music_tracks):
        return

    attempts = len(music_tracks)
    while attempts > 0:
        music_track_index = (music_track_index + 1) % len(music_tracks)
        track = music_tracks[music_track_index]
        try:
            pygame.mixer.music.load(track)
            _apply_music_volume()
            pygame.mixer.music.play()
            return
        except Exception as e:
            print("Music track load error:", e)
            attempts -= 1


def set_music_mode(new_mode, force_restart=False):
    global music_mode, music_tracks, music_track_index

    if not AUDIO_AVAILABLE:
        return

    if not runtime_settings["music"]:
        pygame.mixer.music.stop()
        music_mode = None
        return

    if new_mode is None:
        pygame.mixer.music.stop()
        music_mode = None
        music_tracks = []
        music_track_index = -1
        return

    if new_mode == music_mode and not force_restart:
        return

    if new_mode == "menu":
        chosen_tracks = _get_menu_tracks()
    elif new_mode.startswith("game:"):
        chosen_tracks = _get_game_tracks(new_mode.split(":", 1)[1])
    else:
        chosen_tracks = _get_menu_tracks()

    music_mode = new_mode
    music_tracks = chosen_tracks
    music_track_index = -1

    if not music_tracks:
        pygame.mixer.music.stop()
        return

    _play_next_music_track()


def update_music_playlist():
    if not (AUDIO_AVAILABLE and runtime_settings["music"]):
        return

    if music_mode and not pygame.mixer.music.get_busy():
        _play_next_music_track()


def get_desired_music_mode():
    if game_state in (STATE_MENU, "settings", "level_select", STATE_SPLASH, STATE_MOBILE_RACE):
        return "menu"

    if game_state in (STATE_PLAYING, STATE_PAUSED, STATE_LOST):
        return f"game:{runtime_settings['difficulty'].title()}"

    if game_state == STATE_WON:
        return None

    return "menu"


refresh_sound_volumes()


def get_theme_for_level(level_number):
    if not THEME_ROTATION:
        return "Neon Circuit", {}
    name = THEME_ROTATION[(max(1, level_number) - 1) % len(THEME_ROTATION)]
    return name, dict(THEME_RULES.get(name, {}))


def get_theme_value(key, default):
    return active_theme_config.get(key, default)


def ensure_ai_path():
    global ai_path, ai_explored, ai_time, ai_mode

    if ai_path:
        return True

    solve_start = time.time()
    path, explored = a_star_solve(current_maze, start_pos, goal_pos)
    solve_end = time.time()

    ai_path = path
    ai_explored = explored
    ai_time = round(solve_end - solve_start, 6)
    ai_mode = "Rival AI locked on" if path and is_vs_ai_mode() else "AI route ready" if path else "No path found"
    return bool(path)


def get_rival_delay():
    base_delay = int(get_theme_value("ghost_delay", RIVAL_GHOST_BASE_DELAY))
    ai_difficulty = runtime_settings.get("ai_difficulty", "Medium")
    ai_config = AI_DIFFICULTY_SETTINGS.get(ai_difficulty, AI_DIFFICULTY_SETTINGS["Medium"])
    base_delay += int(ai_config.get("delay_bonus", 0))

    if runtime_settings["difficulty"].title() == "Easy":
        base_delay += 1
    elif runtime_settings["difficulty"].title() == "Hard":
        base_delay -= 1

    if wrong_turns >= 4:
        base_delay -= 1
    if level >= 8:
        base_delay -= 1

    return max(RIVAL_GHOST_MIN_DELAY, base_delay)


def is_vs_ai_mode():
    return runtime_settings.get("game_mode", "Solo") == "VS AI"


def draw_glow_circle(center_x, center_y, radius, color, layers=4):
    size = (radius + layers * 6) * 2
    glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)

    for i in range(layers, 0, -1):
        alpha = max(12, 55 - i * 8)
        pygame.draw.circle(
            glow_surface,
            (*color, alpha),
            (size // 2, size // 2),
            radius + i * 4
        )

    screen.blit(glow_surface, (center_x - size // 2, center_y - size // 2))


def update_particles():
    for p in particles:
        p["y"] += p["speed"]
        if p["y"] > HEIGHT:
            p["y"] = -5
            p["x"] = random.randint(0, WIDTH)


def draw_particles():
    particle_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for p in particles:
        pygame.draw.circle(
            particle_surface,
            (220, 240, 255, p["alpha"]),
            (int(p["x"]), int(p["y"])),
            p["r"]
        )

    screen.blit(particle_surface, (0, 0))


def update_player_animation():
    global render_player_x, render_player_y
    global target_player_x, target_player_y

    smoothing = 0.22
    render_player_x += (target_player_x - render_player_x) * smoothing
    render_player_y += (target_player_y - render_player_y) * smoothing


def draw_hover_tile():
    mx, my = pygame.mouse.get_pos()

    maze_width = cols * cell_size
    maze_height = rows * cell_size

    if MAZE_OFFSET_X <= mx < MAZE_OFFSET_X + maze_width and MAZE_OFFSET_Y <= my < MAZE_OFFSET_Y + maze_height:
        col = (mx - MAZE_OFFSET_X) // cell_size
        row = (my - MAZE_OFFSET_Y) // cell_size

        if 0 <= row < rows and 0 <= col < cols:
            x = MAZE_OFFSET_X + col * cell_size
            y = MAZE_OFFSET_Y + row * cell_size
            hover_rect = pygame.Rect(x + 2, y + 2, cell_size - 4, cell_size - 4)
            draw_glow_rect(hover_rect.x, hover_rect.y, hover_rect.width, hover_rect.height, HINT_COLOR, layers=2, radius=BORDER_RADIUS)
            pygame.draw.rect(screen, HINT_COLOR, hover_rect, 2, border_radius=BORDER_RADIUS)


def update_feature_timers():
    global reveal_timer, fog_enabled, score_boost_timer, score_boost_active

    if reveal_timer > 0:
        reveal_timer -= 1
        fog_enabled = False
    else:
        fog_enabled = runtime_settings["fog"]

    if score_boost_timer > 0:
        score_boost_timer -= 1
    else:
        score_boost_active = False

    blocked_cells = {start_pos, goal_pos, (player_row, player_col)}
    if checkpoint:
        blocked_cells.add(checkpoint.position())
    for powerup in powerups:
        if not powerup.collected:
            blocked_cells.add(powerup.position())

    for trap in traps:
        trap.update(
            current_maze,
            blocked_cells=blocked_cells,
            speed_bonus=get_theme_value("moving_trap_bonus", 0),
        )
        blocked_cells.add(trap.position())

    for powerup in powerups:
        powerup.update()


def handle_checkpoint():
    global checkpoint_pos, hint_message, shield_active, reveal_timer, score

    if checkpoint and not checkpoint.activated:
        if (player_row, player_col) == checkpoint.position():
            checkpoint.activated = True
            checkpoint_pos = checkpoint.position()
            reward = get_theme_value("checkpoint_reward", "score")
            if reward == "shield":
                shield_active = True
                hint_message = "Checkpoint activated! Frost shield granted."
            elif reward == "reveal":
                reveal_timer = max(reveal_timer, FPS * 4)
                hint_message = "Checkpoint activated! Void scan online."
            else:
                score += 10
                hint_message = "Checkpoint activated! Bonus score earned."


def handle_traps():
    global shield_active, hint_message, moves_count, last_move_time

    for trap in traps:
        if trap.active and (player_row, player_col) == trap.position():
            trap.active = False
            play_sfx(trap_hit_sound)

            if shield_active:
                shield_active = False
                hint_message = "Shield absorbed a trap!"
                return

            # penalty always applies
            update_score(-TRAP_SCORE_PENALTY)
            moves_count += 3
            last_move_time = time.time()

            if is_deadly_trap_level():
                hint_message = "Deadly trap triggered!"
                pygame.time.delay(180)
                fail_level("You were eliminated by a deadly trap.")
                return

            # non-deadly behavior
            trap_label = "Moving trap" if trap.trap_type == "moving" else "Blink trap" if trap.trap_type == "blink" else "Trap"
            hint_message = f"{trap_label} hit! -{TRAP_SCORE_PENALTY} score"

            if TRAP_RESPAWN_ENABLED:
                pygame.time.delay(150)
                respawn_at_checkpoint()
                hint_message += " Respawned to checkpoint."

            return


def handle_powerups():
    global shield_active, reveal_timer, score_boost_active, score_boost_timer, hint_message, score

    for powerup in powerups:
        if not powerup.collected and (player_row, player_col) == powerup.position():
            powerup.collected = True
            play_sfx(powerup_sound)

            if powerup.kind == "reveal":
                reveal_timer = FPS * 5 + int(get_theme_value("reveal_bonus_frames", 0))
                hint_message = "Reveal power-up collected!"

            elif powerup.kind == "shield":
                shield_active = True
                hint_message = "Shield power-up collected!"

            elif powerup.kind == "score_boost":
                score_boost_active = True
                score_boost_timer = FPS * 6
                score += 20
                hint_message = "Score boost collected! +20"


def respawn_at_checkpoint():
    global player_row, player_col, target_player_x, target_player_y

    if checkpoint_pos:
        player_row, player_col = checkpoint_pos
    else:
        player_row, player_col = start_pos

    target_player_x = MAZE_OFFSET_X + player_col * cell_size + cell_size // 2
    target_player_y = MAZE_OFFSET_Y + player_row * cell_size + cell_size // 2


def start_replay_mode():
    global replay_mode, replay_index, replay_counter, ghost_player_pos

    if len(player_replay_path) < 2:
        return

    replay_mode = True
    replay_index = 0
    replay_counter = 0
    ghost_player_pos = player_replay_path[0]


def update_replay_mode():
    global replay_mode, replay_index, replay_counter, ghost_player_pos

    if not replay_mode or len(player_replay_path) < 2:
        return

    replay_counter += 1
    if replay_counter < replay_delay:
        return

    replay_counter = 0

    if replay_index < len(player_replay_path):
        ghost_player_pos = player_replay_path[replay_index]
        replay_index += 1
    else:
        replay_mode = False


def start_ghost_ai():
    global ghost_ai_visible, ghost_ai_index, ghost_ai_counter, ghost_ai_pos
    global ghost_ai_delay, ghost_ai_finished, hint_message

    if not is_vs_ai_mode():
        hint_message = "Ghost AI is only available in VS AI mode"
        return

    if not ensure_ai_path():
        hint_message = "Rival AI could not find a route"
        return

    ghost_ai_delay = get_rival_delay()
    ghost_ai_visible = True
    ghost_ai_index = 1 if len(ai_path) > 1 else 0
    ghost_ai_counter = 0
    ghost_ai_finished = False
    ghost_ai_pos = ai_path[0]


def update_ghost_ai():
    global ghost_ai_visible, ghost_ai_index, ghost_ai_counter, ghost_ai_pos
    global ghost_ai_delay, ghost_ai_finished, hint_message, shield_active

    if not ghost_ai_visible or not ai_path:
        return

    ghost_ai_delay = get_rival_delay()
    ghost_ai_counter += 1
    if ghost_ai_counter < ghost_ai_delay:
        return

    ghost_ai_counter = 0

    if ghost_ai_index < len(ai_path):
        ghost_ai_pos = ai_path[ghost_ai_index]
        ghost_ai_index += 1
    else:
        ghost_ai_visible = False
        ghost_ai_finished = True
        ghost_ai_pos = goal_pos
        if game_state == STATE_PLAYING and not player_won():
            fail_level("The rival AI reached the core first.")
        return

    if ghost_ai_pos == (player_row, player_col):
        ai_config = AI_DIFFICULTY_SETTINGS.get(runtime_settings.get("ai_difficulty", "Medium"), AI_DIFFICULTY_SETTINGS["Medium"])
        touch_penalty = int(ai_config.get("collision_penalty", RIVAL_GHOST_TOUCH_PENALTY))
        if shield_active:
            shield_active = False
            hint_message = "Rival AI intercepted you, but your shield held."
        else:
            update_score(-touch_penalty)
            respawn_at_checkpoint()
            hint_message = "Rival AI intercepted you! Respawning..."


def evaluate_player_with_ai():
    global ai_profile_label, ai_profile_score, ai_profile_summary
    global ai_adaptive_message, ai_adaptive_config

    metrics = PlayerMetrics(
        level=level,
        difficulty=difficulty,
        moves=moves_count,
        wrong_turns=wrong_turns,
        manual_hints_used=manual_hints_used,
        auto_hints_used=auto_hints_used,
        time_taken=final_player_time,
        maze_rows=rows,
        maze_cols=cols,
        fog_enabled=fog_enabled,
    )

    report = build_post_level_report(metrics)

    ai_profile_label = report["profile"]
    ai_profile_score = report["profile_score"]
    ai_profile_summary = report["profile_summary"]
    ai_adaptive_config = report["recommendation"]
    ai_adaptive_message = report["recommendation"]["message"]


def apply_runtime_settings(new_settings):
    global difficulty, auto_help_enabled, fog_enabled, timer_running
    global move_sound, win_sound, click_sound
    global wall_hit_sound, trap_hit_sound, powerup_sound

    runtime_settings.update(new_settings)

    # difficulty
    difficulty = runtime_settings["difficulty"].title()

    # hint system
    auto_help_enabled = runtime_settings["show_hints"]

    # fog
    fog_enabled = runtime_settings["fog"]

    # timer control
    if not runtime_settings["timer"]:
        timer_running = False

    # sound effects volume / mute
    refresh_sound_volumes()

    if runtime_settings["sfx"]:
        menu_screen.set_click_sound(click_sound)
        settings_screen.set_click_sound(click_sound)
    else:
        menu_screen.set_click_sound(None)
        settings_screen.set_click_sound(None)

    # background music
    if runtime_settings["music"] and AUDIO_AVAILABLE:
        set_music_mode(get_desired_music_mode())
        _apply_music_volume()
    else:
        if AUDIO_AVAILABLE:
            pygame.mixer.music.stop()


def get_dynamic_cell_size(current_rows, current_cols):
    """
    Scale maze cells to use more of the available screen space.
    Leaves room for title, hint dialog, and compact HUD.
    """
    usable_width = WIDTH - 120
    usable_height = HEIGHT - 210

    size_by_width = usable_width // current_cols
    size_by_height = usable_height // current_rows

    return max(MIN_CELL_SIZE, min(size_by_width, size_by_height))


def update_maze_position():
    global MAZE_OFFSET_X, MAZE_OFFSET_Y

    maze_pixel_width = cols * cell_size
    maze_pixel_height = rows * cell_size

    MAZE_OFFSET_X = max(30, (WIDTH - maze_pixel_width) // 2)
    MAZE_OFFSET_Y = max(80, (HEIGHT - maze_pixel_height) // 2 - 25)


def get_current_position():
    return (player_row, player_col)


def get_shortest_path_from_player():
    return bfs_solve(current_maze, get_current_position(), goal_pos)


def compute_distance_to_goal():
    path, _ = get_shortest_path_from_player()
    if path:
        return len(path) - 1
    return None


def reset_player_tracking():
    global position_history, wrong_turns, best_distance_seen, last_distance_to_goal
    global last_move_time, hint_path, hint_level, hint_message, help_state

    position_history = deque(maxlen=18)
    position_history.append(start_pos)
    wrong_turns = 0

    distance = compute_distance_to_goal()
    best_distance_seen = distance
    last_distance_to_goal = distance

    last_move_time = time.time()
    hint_path = []
    hint_level = 0
    hint_message = "Hints ready"
    help_state = "Normal"


def get_goal_candidates(rows, cols):
    """
    Candidate goal positions away from the start.
    Keeps variety while avoiding goals too close to (0, 0).
    """
    candidates = [
        (rows - 1, cols - 1),   # bottom-right
        (rows - 1, cols // 2),  # bottom-middle
        (rows // 2, cols - 1),  # right-middle
        (rows - 2, cols - 2),   # near bottom-right
        (rows // 2, cols // 2), # center
        (rows - 3, cols // 3),  # lower-left-ish
        (rows // 3, cols - 3),  # upper-right-ish
    ]

    valid = []
    for r, c in candidates:
        r = max(1, min(rows - 1, r))
        c = max(1, min(cols - 1, c))

        # keep goal far enough from start
        if abs(r - 0) + abs(c - 0) >= (rows + cols) // 2:
            valid.append((r, c))

    if not valid:
        valid.append((rows - 1, cols - 1))

    return list(dict.fromkeys(valid))  # remove duplicates


def choose_dynamic_goal(rows, cols, level):
    """
    Pick a more visibly different goal position.
    Keeps it far from the start so the level still feels meaningful.
    """
    attempts = 0

    while attempts < 40:
        r = random.randint(max(1, rows // 3), rows - 1)
        c = random.randint(max(1, cols // 3), cols - 1)

        # keep it far enough from start
        if abs(r - start_pos[0]) + abs(c - start_pos[1]) >= (rows + cols) // 2:
            return (r, c)

        attempts += 1

    # safe fallback
    return (rows - 1, cols - 1)


def get_level_time_limit(rows, cols, level, difficulty):
    """
    Soft target for level completion.
    Bigger mazes get more time.
    """
    base = (rows + cols)

    if difficulty == "Easy":
        result = base + 18 + level * 2
    elif difficulty == "Medium":
        result = base + 12 + level * 2
    else:  # Hard
        result = base + 8 + level * 2

    return max(12, result + int(get_theme_value("timer_bonus", 0)))


def is_deadly_trap_level():
    """
    Deadly traps only start later, or immediately on Hard mode.
    """
    if runtime_settings["difficulty"].title() == "Hard":
        return True

    return level >= 10


def fail_level(reason="Mission failed"):
    global game_state, timer_running, final_player_time, level_failed_reason

    if timer_running:
        final_player_time = int(time.time() - start_time)
        timer_running = False

    level_failed_reason = reason
    game_state = STATE_LOST


def create_level():
    global rows, cols, cell_size, start_pos, goal_pos, current_maze
    global player_row, player_col, moves_count
    global ai_path, ai_explored, ai_mode
    global visible_explored, visible_path
    global animating, animation_stage, animation_index, animation_counter
    global start_time, player_time, final_player_time, ai_time, timer_running, win_time, level_time_limit
    global score, manual_hints_used, auto_hints_used, new_record, best_score
    global render_player_x, render_player_y, target_player_x, target_player_y
    global auto_help_enabled, fog_enabled, current_level
    global heatmap, player_replay_path, replay_mode, replay_index, replay_counter
    global ghost_ai_visible, ghost_ai_index, ghost_ai_counter, ghost_ai_delay, ghost_ai_finished
    global ghost_player_pos, ghost_ai_pos, comparison_result
    global win_rewatch_mode
    global active_theme_name, active_theme_config

    if win_sound:
        win_sound.stop()

    win_rewatch_mode = False

    selected_difficulty = runtime_settings["difficulty"].title()
    base_rows, base_cols = difficulty_config[selected_difficulty]
    active_theme_name, active_theme_config = get_theme_for_level(level)

    # Endless scaling + adaptive AI adjustment
    size_growth = (level - 1) // 2
    adaptive_bonus = ai_adaptive_config.get("maze_size_bonus", 0)

    rows = min(max(base_rows + size_growth + adaptive_bonus, 8), MAX_ROWS)
    cols = min(max(base_cols + size_growth + adaptive_bonus, 10), MAX_COLS)

    cell_size = get_dynamic_cell_size(rows, cols)
    update_maze_position()

    start_pos = (0, 0)
    goal_pos = choose_dynamic_goal(rows, cols, level)

    current_maze = generate_maze(rows, cols, start_pos, goal_pos, level=level, difficulty=selected_difficulty)

    player_row, player_col = start_pos
    render_player_x = MAZE_OFFSET_X + player_col * cell_size + cell_size // 2
    render_player_y = MAZE_OFFSET_Y + player_row * cell_size + cell_size // 2
    target_player_x = render_player_x
    target_player_y = render_player_y
    moves_count = 0

    ai_path = []
    ai_explored = []
    ai_mode = "VS AI ready" if is_vs_ai_mode() else "Solo mode"

    visible_explored = []
    visible_path = []

    animating = False
    animation_stage = "none"
    animation_index = 0
    animation_counter = 0

    start_time = time.time()
    player_time = 0
    final_player_time = 0
    ai_time = 0
    timer_running = runtime_settings["timer"]
    win_time = None

    level_time_limit = get_level_time_limit(rows, cols, level, selected_difficulty)

    score = BASE_LEVEL_SCORE + (level - 1) * LEVEL_BONUS
    if runtime_settings["fog"]:
        score += FOG_BONUS

    manual_hints_used = 0
    auto_hints_used = 0
    new_record = False
    best_score = get_best_score(selected_difficulty)
    fog_enabled = runtime_settings["fog"]
    auto_help_enabled = runtime_settings["show_hints"]
    current_level = level

    reset_player_tracking()

    global traps, powerups, checkpoint, checkpoint_pos
    global shield_active, reveal_timer, score_boost_active, score_boost_timer

    # Reset feature states
    shield_active = False
    reveal_timer = 0
    score_boost_active = False
    score_boost_timer = 0
    checkpoint_pos = None

    # Scale features by level/profile a little
    trap_count = 2 if ai_profile_label == "Beginner" else 3 if ai_profile_label == "Intermediate" else 4
    powerup_count = 3 if ai_profile_label == "Beginner" else 2
    trap_count += int(get_theme_value("trap_bonus", 0))
    powerup_count += int(get_theme_value("powerup_bonus", 0))

    # Smart endless system:
    # Once maze size is near/maxed, difficulty continues by increasing danger
    # rather than making the maze visually too huge.
    reached_size_cap = (rows >= MAX_ROWS or cols >= MAX_COLS)

    if reached_size_cap:
        trap_count += max(1, level // 6)
        powerup_count = max(1, powerup_count - 1)

    traps = place_traps(current_maze, start_pos, goal_pos, count=trap_count)
    powerups = place_powerups(current_maze, start_pos, goal_pos, count=powerup_count)
    checkpoint = place_checkpoint(current_maze, start_pos, goal_pos)

    # Advanced tracking reset
    heatmap = create_empty_heatmap(rows, cols)
    player_replay_path = [start_pos]
    record_heatmap_visit(heatmap, start_pos[0], start_pos[1])

    replay_mode = False
    replay_index = 0
    replay_counter = 0

    ghost_ai_visible = False
    ghost_ai_index = 0
    ghost_ai_counter = 0
    ghost_ai_delay = get_rival_delay()
    ghost_ai_finished = False

    ghost_player_pos = None
    ghost_ai_pos = None

    comparison_result = {
        "player_steps": 0,
        "ai_steps": 0,
        "difference": 0,
        "verdict": "No comparison yet",
    }

    # Ensure game music matches current mode / difficulty.
    if runtime_settings["music"] and AUDIO_AVAILABLE:
        set_music_mode(f"game:{runtime_settings['difficulty'].title()}")

    if is_vs_ai_mode():
        ensure_ai_path()
    if RIVAL_GHOST_ENABLED and is_vs_ai_mode():
        start_ghost_ai()


def player_won():
    return (player_row, player_col) == goal_pos


def stop_timer():
    global timer_running, final_player_time, win_time
    if timer_running:
        final_player_time = int(time.time() - start_time)
        timer_running = False
        win_time = time.time()


def update_score(amount):
    global score
    score = max(0, score + amount)


def register_move_distance():
    global wrong_turns, best_distance_seen, last_distance_to_goal

    new_distance = compute_distance_to_goal()
    if new_distance is None:
        return

    if best_distance_seen is None or new_distance < best_distance_seen:
        best_distance_seen = new_distance

    if last_distance_to_goal is not None and new_distance > last_distance_to_goal:
        wrong_turns += 1

    last_distance_to_goal = new_distance


def move_player(dr, dc):
    global player_row, player_col, moves_count, last_move_time, target_player_x, target_player_y
    global last_wall_hit_sfx_time

    if animating or game_state != STATE_PLAYING:
        return

    new_row = player_row + dr
    new_col = player_col + dc

    if 0 <= new_row < len(current_maze) and 0 <= new_col < len(current_maze[0]):
        if current_maze[new_row][new_col] == 0:
            player_row = new_row
            player_col = new_col
            moves_count += 1
            update_score(-MOVE_PENALTY)
            last_move_time = time.time()
            position_history.append((player_row, player_col))
            player_replay_path.append((player_row, player_col))
            record_heatmap_visit(heatmap, player_row, player_col)
            register_move_distance()

            target_player_x = MAZE_OFFSET_X + player_col * cell_size + cell_size // 2
            target_player_y = MAZE_OFFSET_Y + player_row * cell_size + cell_size // 2
            
            play_sfx(move_sound)

            handle_checkpoint()
            handle_traps()
            handle_powerups()
        else:
            now = time.time()
            if now - last_wall_hit_sfx_time >= WALL_HIT_SFX_COOLDOWN:
                play_sfx(
                    wall_hit_sound,
                    duck_mult=float(getattr(game_settings, "WALL_HIT_MUSIC_DUCK_MULT", 0.20)),
                    duck_duration=float(getattr(game_settings, "WALL_HIT_MUSIC_DUCK_DURATION_SEC", 0.32)),
                )
                last_wall_hit_sfx_time = now
    else:
        now = time.time()
        if now - last_wall_hit_sfx_time >= WALL_HIT_SFX_COOLDOWN:
            play_sfx(
                wall_hit_sound,
                duck_mult=float(getattr(game_settings, "WALL_HIT_MUSIC_DUCK_MULT", 0.20)),
                duck_duration=float(getattr(game_settings, "WALL_HIT_MUSIC_DUCK_DURATION_SEC", 0.32)),
            )
            last_wall_hit_sfx_time = now


def start_ai_animation(path, explored, mode_name, solve_time):
    global ai_path, ai_explored, ai_mode, ai_time
    global visible_explored, visible_path
    global animating, animation_stage, animation_index, animation_counter

    ai_path = path
    ai_explored = explored
    ai_time = round(solve_time, 6)
    ai_mode = mode_name if path else "No path found"

    visible_explored = []
    visible_path = []

    animation_index = 0
    animation_counter = 0

    if path:
        animating = True
        animation_stage = "explored"
    else:
        animating = False
        animation_stage = "none"


def update_animation():
    global animating, animation_stage, animation_index, animation_counter
    global visible_explored, visible_path

    if not animating:
        return

    animation_counter += 1
    if animation_counter < animation_delay:
        return

    animation_counter = 0

    if animation_stage == "explored":
        if animation_index < len(ai_explored):
            visible_explored.append(ai_explored[animation_index])
            animation_index += 1
        else:
            animation_stage = "path"
            animation_index = 0

    elif animation_stage == "path":
        if animation_index < len(ai_path):
            visible_path.append(ai_path[animation_index])
            animation_index += 1
        else:
            animation_stage = "none"
            animating = False


def next_level():
    global level, current_level, game_state, win_rewatch_mode
    win_rewatch_mode = False
    level += 1
    current_level = level
    create_level()
    game_state = STATE_PLAYING


def get_loop_score():
    if len(position_history) < 8:
        return 0

    counts = Counter(position_history)
    most_common_visits = counts.most_common(1)[0][1]
    return max(0, most_common_visits - 1)


def determine_help_state():
    global help_state

    idle_time = time.time() - last_move_time
    loop_score = get_loop_score()
    current_distance = compute_distance_to_goal()
    shortest_path, _ = get_shortest_path_from_player()

    path_pressure = 0
    if current_distance is not None and best_distance_seen is not None:
        if current_distance > max(2, int(best_distance_seen * LONG_ROUTE_HINT_FACTOR)):
            path_pressure = 1

    if idle_time >= IDLE_HINT_THRESHOLD or wrong_turns >= WRONG_TURN_HINT_THRESHOLD or loop_score >= LOOP_HINT_THRESHOLD + 1:
        help_state = "Struggling"
    elif loop_score >= LOOP_HINT_THRESHOLD or path_pressure:
        help_state = "Needs guidance"
    else:
        help_state = "Normal"

    return help_state, shortest_path


def apply_hint(auto=False):
    global hint_path, hint_level, hint_message, manual_hints_used, auto_hints_used, last_auto_hint_time

    full_path, _ = get_shortest_path_from_player()

    if not full_path:
        hint_path = []
        hint_level = 0
        hint_message = "No hint available"
        return

    if len(full_path) <= 1:
        hint_path = []
        hint_level = 0
        hint_message = "You are at the goal"
        return

    preview_steps = ai_adaptive_config.get("hint_preview_steps", HINT_PREVIEW_STEPS)
    hint_path = full_path[1:1 + preview_steps]
    hint_level = 1
    hint_message = "Hint: best next path"
    update_score(-5)

    if auto:
        auto_hints_used += 1
        last_auto_hint_time = time.time()
    else:
        manual_hints_used += 1


def request_manual_hint():
    global hint_message
    if not runtime_settings["show_hints"]:
        hint_message = "Hints are disabled in Settings"
        return
    apply_hint(auto=False)


def update_adaptive_help():
    if not auto_help_enabled or game_state != STATE_PLAYING:
        return

    state, shortest_path = determine_help_state()
    _ = shortest_path

    now = time.time()
    auto_help_delay = ai_adaptive_config.get("auto_help_delay", 4.0)
    if now - last_auto_hint_time < auto_help_delay:
        return

    if state in ("Needs guidance", "Struggling"):
        apply_hint(auto=True)


def get_time_bonus():
    """
    Time affects score even when it does not fail the player.
    """
    if not runtime_settings["timer"]:
        return 0

    if final_player_time <= level_time_limit:
        return 50
    elif final_player_time <= level_time_limit + 10:
        return 10
    else:
        return -20


def finish_level_rewards():
    global total_score, new_record, best_score, score

    score += get_time_bonus()
    total_score += score
    new_record, best_score = update_best_score(difficulty, total_score)


def calculate_ai_score():
    base = 100

    # penalties
    hint_penalty = manual_hints_used * 12 + auto_hints_used * 18
    move_penalty = max(0, moves_count - (rows + cols)) * 0.6
    time_penalty = final_player_time * 0.25
    wrong_penalty = wrong_turns * 4

    score = base - hint_penalty - move_penalty - time_penalty - wrong_penalty

    return max(0, min(100, int(score)))


# -------------------------------------------------
# DRAWING
# -------------------------------------------------
def draw_background():
    if bg_image:
        screen.blit(bg_image, (0, 0))
    else:
        screen.fill(BG_COLOR)
        top_color = get_theme_value("bg_top", BG_ACCENT_1)
        mid_color = get_theme_value("bg_mid", BG_ACCENT_2)
        pygame.draw.rect(screen, top_color, (0, 0, WIDTH, HEIGHT // 3))
        pygame.draw.rect(screen, mid_color, (0, HEIGHT // 3, WIDTH, HEIGHT // 6))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((4, 8, 20, 120))
    screen.blit(overlay, (0, 0))

    t = pygame.time.get_ticks()
    glow1_x = 160 + int(18 * pygame.math.Vector2(1, 0).rotate(t * 0.02).x)
    glow2_x = 710 + int(12 * pygame.math.Vector2(1, 0).rotate(t * 0.03).x)
    glow3_x = 1080 + int(16 * pygame.math.Vector2(1, 0).rotate(t * 0.025).x)

    draw_glow_circle(glow1_x, 90, 55, get_theme_value("path_glow", PANEL_GLOW_COLOR), layers=6)
    draw_glow_circle(glow2_x, 70, 40, GOAL_COLOR, layers=5)
    draw_glow_circle(glow3_x, 110, 55, get_theme_value("wall_glow", PLAYER_COLOR), layers=6)

    header_rect = pygame.Rect(25, 18, WIDTH - 50, 48)
    pygame.draw.rect(screen, (12, 18, 36, 180), header_rect, border_radius=18)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, header_rect, 2, border_radius=18)


def draw_menu():
    draw_background()

    menu_box = pygame.Rect(180, 140, 900, 520)
    draw_glow_rect(180, 140, 900, 520, PANEL_GLOW_COLOR, layers=6, radius=26)
    pygame.draw.rect(screen, PANEL_COLOR, menu_box, border_radius=26)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, menu_box, 2, border_radius=26)

    draw_text("ADAPTIVE INTELLIGENT MAZE NAVIGATION GAME", font_title, TEXT_COLOR, 220, 185)
    draw_text("Futuristic AI Pathfinding Challenge", font_menu, TEXT_SUBCOLOR, 350, 235)

    draw_text("Choose Difficulty:", font_menu, TEXT_COLOR, 240, 325)
    draw_text("1 = Easy", font_menu, SUCCESS_COLOR if difficulty == "Easy" else TEXT_SUBCOLOR, 300, 385)
    draw_text("2 = Medium", font_menu, SUCCESS_COLOR if difficulty == "Medium" else TEXT_SUBCOLOR, 300, 435)
    draw_text("3 = Hard", font_menu, SUCCESS_COLOR if difficulty == "Hard" else TEXT_SUBCOLOR, 300, 485)

    draw_text("Press ENTER to Start", font_menu, WARNING_COLOR, 700, 390)
    draw_text("H = Hint | J = Auto Help | F = Fog On/Off", font_small, TEXT_MUTED, 620, 450)
    draw_text("B = BFS | P = A* | R = Reset", font_small, TEXT_MUTED, 620, 485)
    draw_text("Move with Arrow Keys or WASD", font_small, TEXT_MUTED, 620, 520)


def draw_maze():
    padding = CELL_PADDING

    for row in range(len(current_maze)):
        for col in range(len(current_maze[0])):
            x = MAZE_OFFSET_X + col * cell_size
            y = MAZE_OFFSET_Y + row * cell_size

            inner_rect = pygame.Rect(
                x + padding,
                y + padding,
                cell_size - padding * 2,
                cell_size - padding * 2
            )

            if current_maze[row][col] == 1:
                # ðŸ”· WALL TILE (Neon block)
                draw_glow_rect(
                    inner_rect.x,
                    inner_rect.y,
                    inner_rect.width,
                    inner_rect.height,
                    get_theme_value("wall_glow", WALL_GLOW_COLOR),
                    layers=3,
                    radius=BORDER_RADIUS + 2
                )

                pygame.draw.rect(
                    screen,
                    WALL_COLOR,
                    inner_rect,
                    border_radius=BORDER_RADIUS
                )

                pygame.draw.rect(
                    screen,
                    WALL_INNER_COLOR,
                    inner_rect.inflate(-6, -6),
                    border_radius=BORDER_RADIUS
                )

            else:
                # ðŸŒŒ PATH TILE
                pygame.draw.rect(
                    screen,
                    PATH_COLOR,
                    inner_rect,
                    border_radius=BORDER_RADIUS
                )

                pygame.draw.rect(
                    screen,
                    PATH_ALT_COLOR,
                    inner_rect.inflate(-8, -8),
                    border_radius=BORDER_RADIUS
                )

                draw_glow_rect(
                    inner_rect.x + 6,
                    inner_rect.y + 6,
                    inner_rect.width - 12,
                    inner_rect.height - 12,
                    get_theme_value("path_glow", PATH_GLOW_COLOR),
                    layers=1,
                    radius=BORDER_RADIUS
                )

    # =========================================================
    # ðŸŸ¢ START TILE (ENERGY CORE STYLE)
    # =========================================================
    sx = MAZE_OFFSET_X + start_pos[1] * cell_size
    sy = MAZE_OFFSET_Y + start_pos[0] * cell_size
    cx = sx + cell_size // 2
    cy = sy + cell_size // 2

    import math
    t = pygame.time.get_ticks() * PLAYER_PULSE_SPEED

    pygame.draw.rect(
        screen,
        (10, 30, 35),
        (sx, sy, cell_size, cell_size),
        border_radius=BORDER_RADIUS
    )

    draw_glow_circle(cx, cy, cell_size // 2, START_GLOW_COLOR, layers=5)

    pulse_r = cell_size // 3 + int(2 * math.sin(t * 2))
    pygame.draw.circle(screen, START_COLOR, (cx, cy), pulse_r)
    pygame.draw.circle(screen, WHITE, (cx, cy), max(3, pulse_r // 3))

    # =========================================================
    # ðŸ”® GOAL TILE (PORTAL STYLE - AAA LOOK)
    # =========================================================
    gx = MAZE_OFFSET_X + goal_pos[1] * cell_size
    gy = MAZE_OFFSET_Y + goal_pos[0] * cell_size
    cx = gx + cell_size // 2
    cy = gy + cell_size // 2

    t = pygame.time.get_ticks() * GOAL_PULSE_SPEED

    # base tile
    pygame.draw.rect(
        screen,
        (22, 10, 42),
        (gx, gy, cell_size, cell_size),
        border_radius=BORDER_RADIUS
    )

    pygame.draw.rect(
        screen,
        (38, 18, 68),
        (gx + 3, gy + 3, cell_size - 6, cell_size - 6),
        border_radius=BORDER_RADIUS
    )

    outer_r = max(10, cell_size // 2 - 3)
    mid_r = max(7, cell_size // 3 + int(2 * math.sin(t * 2.2)))
    core_r = max(4, cell_size // 6)

    # glow layers
    draw_glow_circle(cx, cy, outer_r + 6, PINK_GLOW, layers=5)
    draw_glow_circle(cx, cy, mid_r + 2, CYAN, layers=3)

    # animated pulse ring
    pulse_r = outer_r + int(2 * abs(math.sin(t * 1.8)))
    pygame.draw.circle(screen, GOAL_GLOW_COLOR, (cx, cy), pulse_r, 2)

    # inner ring
    pygame.draw.circle(screen, SOFT_CYAN, (cx, cy), mid_r, 2)

    # portal core
    pygame.draw.circle(screen, (90, 20, 130), (cx, cy), max(5, mid_r - 3))
    pygame.draw.circle(screen, GOAL_COLOR, (cx, cy), core_r + 2)
    pygame.draw.circle(screen, WHITE, (cx, cy), max(2, core_r - 1))

    # orbit particles
    for i in range(3):
        angle = t * 1.7 + i * 2.094
        px = int(cx + math.cos(angle) * (outer_r - 4))
        py = int(cy + math.sin(angle) * (outer_r - 4))
        pygame.draw.circle(screen, WHITE, (px, py), 2)

    # sparkle cross
    sparkle = max(3, cell_size // 9)
    pygame.draw.line(screen, WHITE, (cx - sparkle, cy), (cx + sparkle, cy), 1)
    pygame.draw.line(screen, WHITE, (cx, cy - sparkle), (cx, cy + sparkle), 1)


def draw_explored():
    for row, col in visible_explored:
        if (row, col) != start_pos and (row, col) != goal_pos:
            x = MAZE_OFFSET_X + col * cell_size
            y = MAZE_OFFSET_Y + row * cell_size
            rect = pygame.Rect(x, y, cell_size, cell_size)
            draw_glow_rect(x + 2, y + 2, cell_size - 4, cell_size - 4, EXPLORED_COLOR, layers=2, radius=BORDER_RADIUS)
            pygame.draw.rect(screen, EXPLORED_COLOR, rect, border_radius=BORDER_RADIUS)


def draw_ai_path():
    for row, col in visible_path:
        if (row, col) != start_pos and (row, col) != goal_pos:
            x = MAZE_OFFSET_X + col * cell_size
            y = MAZE_OFFSET_Y + row * cell_size
            rect = pygame.Rect(x, y, cell_size, cell_size)
            draw_glow_rect(x + 2, y + 2, cell_size - 4, cell_size - 4, AI_PATH_COLOR, layers=3, radius=BORDER_RADIUS)
            pygame.draw.rect(screen, AI_PATH_COLOR, rect, border_radius=BORDER_RADIUS)


def draw_hint_path():
    if not runtime_settings["show_hints"]:
        return

    for row, col in hint_path:
        if (row, col) != start_pos and (row, col) != goal_pos:
            x = MAZE_OFFSET_X + col * cell_size
            y = MAZE_OFFSET_Y + row * cell_size
            rect = pygame.Rect(x, y, cell_size, cell_size)

            color = AUTO_HELP_COLOR if auto_help_enabled else HINT_COLOR

            draw_glow_rect(
                x + 4, y + 4,
                cell_size - 8, cell_size - 8,
                color,
                layers=3,
                radius=BORDER_RADIUS
            )
            pygame.draw.rect(screen, color, rect, 2, border_radius=BORDER_RADIUS)


def draw_player():
    import math
    t = pygame.time.get_ticks()

    base_radius = max(8, cell_size // 3)
    pulse = int(3 * abs(math.sin(t * 0.006)))
    glow_radius = base_radius + pulse

    x = int(render_player_x)
    y = int(render_player_y)

    draw_glow_circle(x, y, glow_radius, PLAYER_COLOR, layers=5)
    pygame.draw.circle(screen, PLAYER_COLOR, (x, y), base_radius + 1)
    pygame.draw.circle(screen, (210, 250, 255), (x - 1, y - 1), max(4, cell_size // 6))
    pygame.draw.circle(screen, (255, 255, 255), (x - 4, y - 4), 2)


def draw_heatmap():
    max_heat = get_heatmap_max(heatmap)
    if max_heat <= 0:
        return

    for row in range(len(heatmap)):
        for col in range(len(heatmap[0])):
            value = heatmap[row][col]
            if value <= 0:
                continue

            intensity = min(180, int((value / max_heat) * 180))

            x = MAZE_OFFSET_X + col * cell_size
            y = MAZE_OFFSET_Y + row * cell_size

            overlay = pygame.Surface((cell_size - 6, cell_size - 6), pygame.SRCALPHA)
            overlay.fill((255, 120, 0, intensity // 2))
            screen.blit(overlay, (x + 3, y + 3))


def draw_replay_ghost():
    if not ghost_player_pos:
        return

    row, col = ghost_player_pos
    x = MAZE_OFFSET_X + col * cell_size + cell_size // 2
    y = MAZE_OFFSET_Y + row * cell_size + cell_size // 2

    ghost_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(
        ghost_surface,
        (255, 255, 255, 90),
        (cell_size // 2, cell_size // 2),
        max(8, cell_size // 3)
    )
    screen.blit(ghost_surface, (x - cell_size // 2, y - cell_size // 2))


def draw_ai_ghost():
    if not ghost_ai_pos:
        return

    row, col = ghost_ai_pos
    x = MAZE_OFFSET_X + col * cell_size + cell_size // 2
    y = MAZE_OFFSET_Y + row * cell_size + cell_size // 2

    ghost_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(
        ghost_surface,
        (0, 255, 255, 110),
        (cell_size // 2, cell_size // 2),
        max(8, cell_size // 3)
    )
    screen.blit(ghost_surface, (x - cell_size // 2, y - cell_size // 2))


def draw_traps():
    for trap in traps:
        if not trap.active and trap.trap_type != "blink":
            continue

        x = MAZE_OFFSET_X + trap.col * cell_size + cell_size // 2
        y = MAZE_OFFSET_Y + trap.row * cell_size + cell_size // 2

        pulse = (trap.pulse % 20) // 4
        radius = max(5, cell_size // 5 + pulse)
        trap_color = get_theme_value("trap_color", DANGER_COLOR)
        if trap.trap_type == "moving":
            trap_color = WARNING_COLOR
        elif trap.trap_type == "blink":
            trap_color = CYAN if trap.active else TEXT_MUTED

        draw_glow_circle(x, y, radius + 3, trap_color, layers=3)
        pygame.draw.circle(screen, trap_color, (x, y), radius)
        if trap.trap_type == "moving":
            pygame.draw.line(screen, WHITE, (x - radius, y), (x + radius, y), 2)
            pygame.draw.line(screen, WHITE, (x, y - radius), (x, y + radius), 2)
        else:
            pygame.draw.circle(screen, (255, 240, 240), (x, y), max(2, radius // 2))


def draw_powerups():
    for powerup in powerups:
        if powerup.collected:
            continue

        x = MAZE_OFFSET_X + powerup.col * cell_size + cell_size // 2
        y = MAZE_OFFSET_Y + powerup.row * cell_size + cell_size // 2

        pulse = (powerup.pulse % 20) // 5
        radius = max(5, cell_size // 5 + pulse)

        if powerup.kind == "reveal":
            color = CYAN
        elif powerup.kind == "shield":
            color = SUCCESS_COLOR
        else:
            color = WARNING_COLOR

        draw_glow_circle(x, y, radius + 3, color, layers=3)
        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), max(2, radius // 2))


def draw_checkpoint():
    if not checkpoint:
        return

    x = MAZE_OFFSET_X + checkpoint.col * cell_size
    y = MAZE_OFFSET_Y + checkpoint.row * cell_size

    color = SUCCESS_COLOR if checkpoint.activated else TEXT_SUBCOLOR
    draw_glow_rect(x + 4, y + 4, cell_size - 8, cell_size - 8, color, layers=3, radius=BORDER_RADIUS)
    pygame.draw.rect(
        screen,
        color,
        (x + 6, y + 6, cell_size - 12, cell_size - 12),
        2,
        border_radius=BORDER_RADIUS
    )


def draw_fog_of_war():
    if not fog_enabled:
        return

    fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fog_surface.fill((*FOG_COLOR, max(40, min(255, int(get_theme_value("fog_alpha", FOG_ALPHA))))))

    vision_radius = max(1, VISION_RADIUS + int(get_theme_value("vision_bonus", 0)))

    for row in range(len(current_maze)):
        for col in range(len(current_maze[0])):
            distance = abs(row - player_row) + abs(col - player_col)

            if distance <= vision_radius:
                x = MAZE_OFFSET_X + col * cell_size
                y = MAZE_OFFSET_Y + row * cell_size
                pygame.draw.rect(
                    fog_surface,
                    (0, 0, 0, 0),
                    (x, y, cell_size, cell_size),
                    border_radius=BORDER_RADIUS
                )

    px = MAZE_OFFSET_X + player_col * cell_size + cell_size // 2
    py = MAZE_OFFSET_Y + player_row * cell_size + cell_size // 2
    pygame.draw.circle(fog_surface, (0, 0, 0, 0), (px, py), cell_size * (vision_radius + 1))

    screen.blit(fog_surface, (0, 0))


def draw_compact_hud():
    hud_rect = pygame.Rect(18, HEIGHT - 98, 620, 64)
    pygame.draw.rect(screen, (8, 18, 40, 210), hud_rect, border_radius=16)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, hud_rect, 2, border_radius=16)

    shown_time = player_time if timer_running else final_player_time
    if not runtime_settings["timer"]:
        shown_time = "OFF"

    time_text = f"Time: {shown_time}s" if shown_time != "OFF" else "Time: OFF"
    mode_text = runtime_settings.get("game_mode", "Solo")
    if is_vs_ai_mode():
        mode_text = f"VS AI ({runtime_settings.get('ai_difficulty', 'Medium')})"

    draw_text(f"Level: {level}", font_small, TEXT_COLOR, 32, HEIGHT - 80)
    draw_text(f"Score: {score}", font_small, SUCCESS_COLOR, 120, HEIGHT - 80)
    draw_text(time_text, font_small, WARNING_COLOR, 235, HEIGHT - 80)
    draw_text(f"Moves: {moves_count}", font_small, TEXT_SUBCOLOR, 360, HEIGHT - 80)
    draw_text(f"Mode: {mode_text}", font_small, CYAN, 470, HEIGHT - 80)


def get_direction_hint_text():
    path, _ = get_shortest_path_from_player()

    if not path or len(path) < 2:
        return "You are very close."

    current = path[0]
    nxt = path[1]

    dr = nxt[0] - current[0]
    dc = nxt[1] - current[1]

    if dr == -1:
        return "Try moving up."
    elif dr == 1:
        return "Try moving down."
    elif dc == -1:
        return "Try moving left."
    elif dc == 1:
        return "Try moving right."

    return "Keep going."


def draw_hint_dialog():
    if not runtime_settings["show_hints"]:
        return

    message = hint_message

    if help_state in ("Needs guidance", "Struggling"):
        message = get_direction_hint_text()

    dialog_width = 320
    dialog_height = 60
    x = (WIDTH - dialog_width) // 2
    y = HEIGHT - 170

    pygame.draw.rect(screen, (10, 20, 46, 220), (x, y, dialog_width, dialog_height), border_radius=16)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, (x, y, dialog_width, dialog_height), 2, border_radius=16)

    draw_text("AI Hint", font_small, CYAN, x + 16, y + 10)
    draw_text(message[:32], font_small, TEXT_COLOR, x + 16, y + 32)


def draw_pause_overlay():
    progress = max(0.0, min(1.0, pause_overlay_anim))
    eased = 1 - (1 - progress) ** 3

    # Dim gameplay and add subtle top focus tint.
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((2, 4, 12, int(90 + 100 * eased)))
    screen.blit(overlay, (0, 0))

    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(vignette, (0, 120, 255, int(8 + 14 * eased)), (0, 0, WIDTH, HEIGHT // 3))
    screen.blit(vignette, (0, 0))

    box_w = 620
    row_h = 40
    options_h = len(pause_options) * row_h
    box_h = 250 + options_h
    box_x = (WIDTH - box_w) // 2
    box_y = (HEIGHT - box_h) // 2 + int((1 - eased) * 30)

    draw_glow_rect(box_x, box_y, box_w, box_h, PANEL_GLOW_COLOR, layers=7, radius=26)
    panel_rect = pygame.Rect(box_x, box_y, box_w, box_h)
    pygame.draw.rect(screen, (8, 14, 38), panel_rect, border_radius=26)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, panel_rect, 2, border_radius=26)

    inner_rect = panel_rect.inflate(-18, -18)
    pygame.draw.rect(screen, (12, 20, 50), inner_rect, border_radius=20)
    pygame.draw.rect(screen, (95, 170, 255), inner_rect, 1, border_radius=20)

    # Header
    draw_text("PAUSED", font_title, TEXT_COLOR, box_x + 32, box_y + 24)
    draw_text("Mission temporarily halted", font_small, TEXT_MUTED, box_x + 34, box_y + 68)

    pulse = (pygame.time.get_ticks() // 450) % 2
    pulse_color = CYAN if pulse == 0 else SOFT_CYAN
    pygame.draw.circle(screen, pulse_color, (box_x + box_w - 42, box_y + 42), 8)
    pygame.draw.circle(screen, pulse_color, (box_x + box_w - 42, box_y + 42), 14, 2)

    # Stats strip
    shown_time = player_time if runtime_settings["timer"] else "OFF"
    stats = [
        ("Level", str(level), TEXT_SUBCOLOR),
        ("Score", str(score), SUCCESS_COLOR),
        ("Moves", str(moves_count), TEXT_SUBCOLOR),
        ("Time", f"{shown_time}s" if shown_time != "OFF" else "OFF", WARNING_COLOR),
    ]

    chip_y = box_y + 96
    chip_gap = 14
    chip_w = (box_w - 64 - chip_gap * 3) // 4
    chip_x = box_x + 32

    for label, value, value_color in stats:
        chip_rect = pygame.Rect(chip_x, chip_y, chip_w, 58)
        pygame.draw.rect(screen, (10, 18, 42), chip_rect, border_radius=14)
        pygame.draw.rect(screen, GRID_SOFT_COLOR, chip_rect, 1, border_radius=14)
        draw_text(label, font_tiny, TEXT_MUTED, chip_x + 12, chip_y + 8)
        draw_text(value, font_small, value_color, chip_x + 12, chip_y + 30)
        chip_x += chip_w + chip_gap

    # Options list
    list_top = chip_y + 80
    list_left = box_x + 28
    list_w = box_w - 56

    for i, option in enumerate(pause_options):
        row_y = list_top + i * row_h
        row_rect = pygame.Rect(list_left, row_y, list_w, row_h - 4)
        selected = i == pause_selected

        if selected:
            row_float = int(3 * math.sin(pygame.time.get_ticks() * 0.012))
            row_rect.x += row_float

            draw_glow_rect(row_rect.x, row_rect.y, row_rect.width, row_rect.height, CYAN, layers=3, radius=12)
            pygame.draw.rect(screen, (10, 34, 70), row_rect, border_radius=12)
            pygame.draw.rect(screen, CYAN, row_rect, 2, border_radius=12)

            # Animated light sweep to make the selected action feel active.
            sweep_x = (pygame.time.get_ticks() // 3) % (row_rect.width + 120) - 60
            sweep = pygame.Surface((52, row_rect.height - 4), pygame.SRCALPHA)
            pygame.draw.rect(sweep, (255, 255, 255, 26), sweep.get_rect(), border_radius=8)
            screen.blit(sweep, (row_rect.x + sweep_x, row_rect.y + 2))

            draw_text(">>", font_text, CYAN, row_rect.x + 10, row_rect.y + 7)
            draw_text(option, font_text, CYAN, row_rect.x + 42, row_rect.y + 7)
        else:
            pygame.draw.rect(screen, (8, 16, 36), row_rect, border_radius=12)
            pygame.draw.rect(screen, GRID_SOFT_COLOR, row_rect, 1, border_radius=12)
            draw_text(option, font_text, TEXT_SUBCOLOR, row_rect.x + 42, row_rect.y + 7)

    # Footer hint
    footer_y = box_y + box_h - 34
    draw_text("UP / DOWN to navigate | ENTER to confirm | ESC to resume", font_tiny, TEXT_MUTED, box_x + 26, footer_y)


def handle_pause_choice(choice):
    global game_state, level_reward_applied, fog_enabled, auto_help_enabled, hint_message

    if choice == "Resume":
        hint_message = "Selected: Resume"
        game_state = STATE_PLAYING

    elif choice == "Restart Level":
        hint_message = "Selected: Restart Level"
        create_level()
        level_reward_applied = False
        game_state = STATE_PLAYING

    elif choice == "Toggle Fog":
        fog_enabled = not fog_enabled
        runtime_settings["fog"] = fog_enabled
        hint_message = f"Selected: Toggle Fog ({'ON' if fog_enabled else 'OFF'})"

    elif choice == "Toggle Auto Help":
        auto_help_enabled = not auto_help_enabled
        runtime_settings["show_hints"] = auto_help_enabled
        hint_message = f"Selected: Toggle Auto Help ({'ON' if auto_help_enabled else 'OFF'})"

    elif choice == "Run BFS":
        if not animating:
            solve_start = time.time()
            path, explored = bfs_solve(current_maze, start_pos, goal_pos)
            solve_end = time.time()
            start_ai_animation(path, explored, "BFS solved", solve_end - solve_start)
            hint_message = "Selected: Run BFS"
            game_state = STATE_PLAYING
        else:
            hint_message = "BFS unavailable while animation is running"

    elif choice == "Run A*":
        if not animating:
            solve_start = time.time()
            path, explored = a_star_solve(current_maze, start_pos, goal_pos)
            solve_end = time.time()
            start_ai_animation(path, explored, "A* solved", solve_end - solve_start)
            hint_message = "Selected: Run A*"
            game_state = STATE_PLAYING
        else:
            hint_message = "A* unavailable while animation is running"

    elif choice == "Replay Run":
        start_replay_mode()
        hint_message = "Selected: Replay Run"
        game_state = STATE_PLAYING

    elif choice == "Ghost AI":
        start_ghost_ai()
        if is_vs_ai_mode():
            hint_message = "Selected: Ghost AI"
        game_state = STATE_PLAYING

    elif choice == "Quit to Menu":
        hint_message = "Selected: Quit to Menu"
        game_state = STATE_MENU


def draw_play_screen():
    draw_background()
    draw_particles()
    draw_text(f"{TITLE}  |  {active_theme_name}", font_title, TEXT_COLOR, 45, 28)
    draw_maze()
    draw_heatmap()
    draw_hover_tile()
    draw_checkpoint()
    draw_traps()
    draw_powerups()
    draw_explored()
    draw_ai_path()
    draw_hint_path()
    draw_replay_ghost()
    draw_ai_ghost()
    draw_player()
    draw_fog_of_war()
    draw_compact_hud()
    draw_hint_dialog()


def draw_win_overlay():
    ai_score = calculate_ai_score()
    comparison_title = "VS AI RESULT" if is_vs_ai_mode() else "SOLO RESULT"
    comparison_detail = (
        f"You: {comparison_result['player_steps']}   AI: {comparison_result['ai_steps']}"
        if is_vs_ai_mode()
        else "Solo run recorded without AI comparison"
    )

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((2, 6, 18, 150))
    screen.blit(overlay, (0, 0))

    card_w = 860
    card_h = 430
    card_x = (WIDTH - card_w) // 2
    card_y = (HEIGHT - card_h) // 2

    draw_glow_rect(card_x, card_y, card_w, card_h, SUCCESS_COLOR, layers=6, radius=28)
    card = pygame.Rect(card_x, card_y, card_w, card_h)
    pygame.draw.rect(screen, (7, 14, 35), card, border_radius=28)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, card, 2, border_radius=28)

    inner = card.inflate(-22, -22)
    pygame.draw.rect(screen, (11, 20, 48), inner, border_radius=20)
    pygame.draw.rect(screen, GRID_SOFT_COLOR, inner, 1, border_radius=20)

    draw_text("MISSION COMPLETE", font_title, SUCCESS_COLOR, card_x + 34, card_y + 28)
    draw_text(f"Level {level} complete in {final_player_time}s with {moves_count} moves.", font_text, TEXT_COLOR, card_x + 34, card_y + 74)
    draw_text(f"AI Profile: {ai_profile_label}", font_text, CYAN, card_x + 34, card_y + 106)

    chip_y = card_y + 138
    chip_w = 190
    chip_h = 74
    gap = 16
    chip_x = card_x + 34
    chips = [
        ("Level Score", str(score), WARNING_COLOR),
        ("Total Score", str(total_score), TEXT_SUBCOLOR),
        ("AI Score", f"{ai_score}/100", CYAN),
        ("Hints Used", f"{manual_hints_used + auto_hints_used}", TEXT_MUTED),
    ]

    for label, value, value_color in chips:
        chip_rect = pygame.Rect(chip_x, chip_y, chip_w, chip_h)
        pygame.draw.rect(screen, (9, 18, 42), chip_rect, border_radius=14)
        pygame.draw.rect(screen, GRID_SOFT_COLOR, chip_rect, 1, border_radius=14)
        draw_text(label, font_tiny, TEXT_MUTED, chip_x + 12, chip_y + 10)
        draw_text(value, font_text, value_color, chip_x + 12, chip_y + 38)
        chip_x += chip_w + gap

    status_msg = "New Best Score Achieved!" if new_record else "Great run completed."
    status_color = SUCCESS_COLOR if new_record else TEXT_SUBCOLOR
    draw_text(status_msg, font_text, status_color, card_x + 34, card_y + 236)
    draw_text(comparison_title, font_tiny, CYAN, card_x + 34, card_y + 262)
    draw_text(comparison_detail[:58], font_small, TEXT_SUBCOLOR, card_x + 34, card_y + 282)
    draw_text(comparison_result["verdict"][:58], font_small, HINT_STRONG_COLOR, card_x + 34, card_y + 304)

    action_box = pygame.Rect(card_x + 30, card_y + 324, card_w - 60, 64)
    pygame.draw.rect(screen, (8, 22, 52), action_box, border_radius=14)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, action_box, 1, border_radius=14)
    draw_text("V = Rewatch then auto-next level", font_small, CYAN, action_box.x + 18, action_box.y + 12)
    draw_text("N = Next level now    R = Replay this level", font_small, TEXT_SUBCOLOR, action_box.x + 18, action_box.y + 36)


def draw_lose_overlay():
    overlay_rect = pygame.Rect(120, 220, 720, 285)
    draw_glow_rect(120, 220, 720, 285, DANGER_COLOR, layers=5, radius=24)
    pygame.draw.rect(screen, PANEL_COLOR, overlay_rect, border_radius=24)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, overlay_rect, 2, border_radius=24)

    draw_text("MISSION FAILED", font_title, DANGER_COLOR, 160, 245)
    draw_text(level_failed_reason, font_text, TEXT_COLOR, 160, 295)
    draw_text(f"Level: {level}", font_text, TEXT_SUBCOLOR, 160, 330)
    draw_text(f"Moves: {moves_count}", font_text, TEXT_SUBCOLOR, 160, 365)
    failed_time = final_player_time if final_player_time > 0 else player_time
    draw_text(f"Time: {failed_time}s", font_text, TEXT_SUBCOLOR, 160, 400)
    draw_text("Press R to retry or ESC to quit", font_text, WARNING_COLOR, 160, 445)


def fade_out(screen, clock, speed=12):
    fade_surface = pygame.Surface(screen.get_size())
    fade_surface.fill((0, 0, 0))

    for alpha in range(0, 255, speed):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)


# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
running = True

while running:
    clock.tick(FPS)

    if game_state == STATE_PAUSED:
        pause_overlay_anim = min(1.0, pause_overlay_anim + 0.12)
    else:
        pause_overlay_anim = max(0.0, pause_overlay_anim - 0.18)

    if AUDIO_AVAILABLE and runtime_settings["music"]:
        set_music_mode(get_desired_music_mode())
        update_music_playlist()
        _apply_music_volume()
    elif AUDIO_AVAILABLE:
        pygame.mixer.music.stop()

    if game_state == STATE_PLAYING:
        if timer_running:
            player_time = int(time.time() - start_time)

            # Clearer rule:
            # Easy / Medium -> timer affects score only
            # Hard -> timer can fail the level
            if runtime_settings["timer"]:
                if runtime_settings["difficulty"].title() == "Hard":
                    if player_time >= level_time_limit:
                        fail_level("Time expired. Level failed.")

        update_adaptive_help()
        update_feature_timers()
        update_replay_mode()
        update_ghost_ai()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == STATE_MENU:
            action = menu_screen.handle_event(event)
            if action in ("start_solo", "start_vs_ai"):
                print("Start Game clicked")
                level = 1
                total_score = 0
                runtime_settings["game_mode"] = "VS AI" if action == "start_vs_ai" else "Solo"
                difficulty = runtime_settings["difficulty"].title()
                best_score = get_best_score(difficulty)
                new_record = False
                
                create_level()
                level_reward_applied = False
                game_state = STATE_PLAYING
            elif action == "mobile_race":
                ip = get_local_ip()
                mobile_race_url = f"http://{ip}:8000"
                qr_code_surface = generate_qr_surface(mobile_race_url)
                
                # Reset server race state when entering
                mobile_server.race_started = False
                mobile_server.race_finished = False
                mobile_server.winner = None
                
                if not mobile_server_started:
                    mobile_server.start_background_server()
                    mobile_server_started = True
                game_state = STATE_MOBILE_RACE
            elif action == "cycle_ai_difficulty":
                menu_screen.runtime_settings = runtime_settings
            elif action == "level_select":
                game_state = "level_select"
            elif action == "settings":
                settings_screen.set_settings(runtime_settings)
                game_state = "settings"
            elif action == "exit":
                pygame.quit()
                raise SystemExit

        elif game_state == STATE_MOBILE_RACE:
            # Professional Layout Dimensions (Must match drawing code)
            card_w, card_h = 800, 540
            card_x = (WIDTH - card_w) // 2
            card_y = (HEIGHT - card_h) // 2
            footer_y = card_y + card_h - 100
            
            start_btn_rect = pygame.Rect(card_x + 420, footer_y, 180, 55)
            back_btn_rect = pygame.Rect(card_x + 615, footer_y, 135, 55)
            reset_btn_rect = pygame.Rect(card_x + 300, card_y + 400, 200, 50)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = STATE_MENU
                elif event.key == pygame.K_SPACE:
                    if len(mobile_server.players) > 0 and not mobile_server.race_started:
                        mobile_server.race_started = True
                        mobile_server.socketio.emit('race_start')
                elif event.key == pygame.K_r and mobile_server.race_finished:
                    # Reset race
                    mobile_server.race_started = False
                    mobile_server.race_finished = False
                    mobile_server.winner = None
                    for sid in list(mobile_server.players.keys()):
                        mobile_server.players[sid]['taps'] = 0
                        mobile_server.players[sid]['finished'] = False
                    mobile_server.socketio.emit('player_update', len(mobile_server.players))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(event.pos):
                    game_state = STATE_MENU
                
                if not mobile_server.race_started and not mobile_server.race_finished:
                    if start_btn_rect.collidepoint(event.pos):
                        if len(mobile_server.players) > 0:
                            mobile_server.race_started = True
                            mobile_server.socketio.emit('race_start')
                
                elif mobile_server.race_finished:
                    if reset_btn_rect.collidepoint(event.pos):
                        mobile_server.race_started = False
                        mobile_server.race_finished = False
                        mobile_server.winner = None
                        for sid in list(mobile_server.players.keys()):
                            mobile_server.players[sid]['taps'] = 0
                            mobile_server.players[sid]['finished'] = False
                        mobile_server.socketio.emit('player_update', len(mobile_server.players))

        elif game_state == "settings":
            action = settings_screen.handle_event(event)

            # Apply changes live while still inside settings
            apply_runtime_settings(settings_screen.get_settings())

            if action == "back":
                game_state = "menu"

        elif game_state == "level_select":
            result = level_select_screen.handle_event(event)

            if result:
                if result["action"] == "back":
                    game_state = "menu"

                elif result["action"] == "play_level":
                    selected_level = result["level"]
                    level = selected_level
                    current_level = selected_level
                    difficulty = runtime_settings["difficulty"].title()
                    best_score = get_best_score(difficulty)
                    new_record = False
                    create_level()
                    level_reward_applied = False
                    game_state = STATE_PLAYING

        elif event.type == pygame.KEYDOWN and game_state == STATE_PLAYING:
            if event.key == pygame.K_ESCAPE:
                pause_selected = 0
                game_state = STATE_PAUSED

            if event.key in (pygame.K_UP, pygame.K_w):
                move_player(-1, 0)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                move_player(1, 0)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                move_player(0, -1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                move_player(0, 1)
            elif event.key == pygame.K_h:
                request_manual_hint()
            elif event.key == pygame.K_j:
                auto_help_enabled = not auto_help_enabled
                runtime_settings["show_hints"] = auto_help_enabled
                hint_message = f"Auto Help {'enabled' if auto_help_enabled else 'disabled'}"
            elif event.key == pygame.K_f:
                fog_enabled = not fog_enabled
                runtime_settings["fog"] = fog_enabled
                hint_message = f"Fog {'enabled' if fog_enabled else 'disabled'}"
            elif event.key == pygame.K_b and not animating:
                solve_start = time.time()
                path, explored = bfs_solve(current_maze, start_pos, goal_pos)
                solve_end = time.time()
                start_ai_animation(path, explored, "BFS solved", solve_end - solve_start)
            elif event.key == pygame.K_p and not animating:
                solve_start = time.time()
                path, explored = a_star_solve(current_maze, start_pos, goal_pos)
                solve_end = time.time()
                start_ai_animation(path, explored, "A* solved", solve_end - solve_start)
            elif event.key == pygame.K_r:
                create_level()
                level_reward_applied = False
            elif event.key == pygame.K_t:
                start_replay_mode()
            elif event.key == pygame.K_g:
                start_ghost_ai()

        elif game_state == STATE_PAUSED:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = STATE_PLAYING

                elif event.key == pygame.K_UP:
                    pause_selected = (pause_selected - 1) % len(pause_options)

                elif event.key == pygame.K_DOWN:
                    pause_selected = (pause_selected + 1) % len(pause_options)

                elif event.key == pygame.K_RETURN:
                    choice = pause_options[pause_selected]
                    handle_pause_choice(choice)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                progress = max(0.0, min(1.0, pause_overlay_anim))
                eased = 1 - (1 - progress) ** 3

                box_w = 620
                row_h = 40
                options_h = len(pause_options) * row_h
                box_h = 250 + options_h
                box_x = (WIDTH - box_w) // 2
                box_y = (HEIGHT - box_h) // 2 + int((1 - eased) * 30)

                list_top = box_y + 176
                list_left = box_x + 28
                list_w = box_w - 56

                for i, option in enumerate(pause_options):
                    row_y = list_top + i * row_h
                    row_rect = pygame.Rect(list_left, row_y, list_w, row_h - 4)
                    if row_rect.collidepoint(event.pos):
                        pause_selected = i
                        handle_pause_choice(option)
                        break

        elif game_state == STATE_WON:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    win_rewatch_mode = False
                    next_level()
                    level_reward_applied = False

                elif event.key == pygame.K_v:
                    start_replay_mode()
                    if replay_mode:
                        win_rewatch_mode = True
                        hint_message = "Rewatching your run..."
                    else:
                        hint_message = "No replay available for this run"

                elif event.key == pygame.K_r:
                    win_rewatch_mode = False
                    create_level()
                    level_reward_applied = False
                    game_state = STATE_PLAYING

                elif event.key == pygame.K_ESCAPE:
                    running = False

        elif game_state == STATE_LOST:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    create_level()
                    level_reward_applied = False
                    game_state = STATE_PLAYING

                elif event.key == pygame.K_ESCAPE:
                    running = False

    update_particles()
    update_player_animation()

    if game_state == STATE_SPLASH:
        finished = splash_screen.update()
        splash_screen.draw(screen)
        if finished:
            fade_out(screen, clock)
            game_state = STATE_MENU

    elif game_state == STATE_PLAYING:
        update_animation()

        if player_won():
            stop_timer()

            if AUDIO_AVAILABLE and runtime_settings["music"]:
                set_music_mode(None, force_restart=True)
            
            play_sfx(win_sound)
            
            if not level_reward_applied:
                finish_level_rewards()
                evaluate_player_with_ai()

                ai_score = calculate_ai_score()

                replay_entry = build_replay_entry(
                    level=level,
                    difficulty=difficulty,
                    moves=player_replay_path,
                    ai_path=ai_path if is_vs_ai_mode() else [],
                    rows=rows,
                    cols=cols,
                    game_mode=runtime_settings.get("game_mode", "Solo"),
                    ai_difficulty=runtime_settings.get("ai_difficulty") if is_vs_ai_mode() else None,
                )
                save_replay(replay_entry)

                comparison_result = compare_player_vs_ai(
                    player_replay_path,
                    ai_path if is_vs_ai_mode() else [],
                )

                from progress_manager import update_level_progress

                items_used = []

                if manual_hints_used > 0:
                    items_used.append(f"Manual Hint x{manual_hints_used}")

                if auto_hints_used > 0:
                    items_used.append(f"Auto Hint x{auto_hints_used}")

                if fog_enabled:
                    items_used.append("Fog Mode")

                if shield_active:
                    items_used.append("Shield")

                if reveal_timer > 0:
                    items_used.append("Reveal Power-Up")

                if score_boost_active:
                    items_used.append("Score Boost")

                if checkpoint and checkpoint.activated:
                    items_used.append("Checkpoint Reached")

                update_level_progress(
                    level=level,
                    score=score,
                    ai_score=ai_score,
                    time_taken=final_player_time,
                    items_used=items_used,
                    game_mode=runtime_settings.get("game_mode", "Solo"),
                    ai_difficulty=runtime_settings.get("ai_difficulty") if is_vs_ai_mode() else None,
                )

                record_session({
                    "level": level,
                    "difficulty": difficulty,
                    "time": final_player_time,
                    "moves": moves_count,
                    "score": score,
                    "ai_score": ai_score,
                    "wrong_turns": wrong_turns,
                    "hints_manual": manual_hints_used,
                    "hints_auto": auto_hints_used
                })

                level_reward_applied = True

            game_state = STATE_WON

    elif game_state == STATE_WON:
        update_replay_mode()
        if win_rewatch_mode and not replay_mode:
            win_rewatch_mode = False
            next_level()
            level_reward_applied = False

    if game_state == STATE_SPLASH:
        pass
    elif game_state == STATE_MENU:
        menu_screen.update()
        menu_screen.draw(screen)
    elif game_state == STATE_MOBILE_RACE:
        draw_background()
        draw_particles()
        
        # Main Layout Dimensions
        card_w, card_h = 800, 540
        card_x = (WIDTH - card_w) // 2
        card_y = (HEIGHT - card_h) // 2
        
        # Draw Main Panel with Glass effect
        draw_glow_rect(card_x, card_y, card_w, card_h, CYAN, layers=8, radius=32)
        pygame.draw.rect(screen, (8, 14, 32), (card_x, card_y, card_w, card_h), border_radius=32)
        pygame.draw.rect(screen, PANEL_BORDER_COLOR, (card_x, card_y, card_w, card_h), 2, border_radius=32)
        
        # Header Area
        header_y = card_y + 45
        draw_text("MOBILE GRID LINK", font_title, CYAN, card_x + 50, header_y)
        pygame.draw.line(screen, (30, 60, 100), (card_x + 50, header_y + 50), (card_x + card_w - 50, header_y + 50), 2)
        
        # Left Side: Connection (QR Code)
        qr_area_x = card_x + 50
        qr_area_y = header_y + 80
        draw_text("SCAN TO UPLINK", font_tiny, TEXT_SUBCOLOR, qr_area_x, qr_area_y)
        if qr_code_surface:
            # Add a white background for the QR code for better scanning
            qr_bg = pygame.Surface((320, 320))
            qr_bg.fill((255, 255, 255))
            screen.blit(qr_bg, (qr_area_x - 10, qr_area_y + 30 - 10))
            screen.blit(qr_code_surface, (qr_area_x, qr_area_y + 30))
            
        # Right Side: Player Roster
        roster_x = card_x + 420
        roster_y = header_y + 80
        draw_text("PILOTS IN GRID", font_tiny, TEXT_SUBCOLOR, roster_x, roster_y)
        
        # Roster Box
        roster_box_h = 280
        roster_box_w = 330
        pygame.draw.rect(screen, (5, 10, 24), (roster_x, roster_y + 30, roster_box_w, roster_box_h), border_radius=15)
        pygame.draw.rect(screen, (20, 40, 80), (roster_x, roster_y + 30, roster_box_w, roster_box_h), 1, border_radius=15)
        
        players_list = list(mobile_server.players.values())
        if not players_list:
            # Pulsing wait text
            pulse = int(127 + 127 * math.sin(time.time() * 4))
            draw_text("WAITING FOR PILOTS...", font_small, (pulse, pulse, pulse), roster_x + 60, roster_y + 150)
        else:
            for i, p in enumerate(players_list[:10]):
                name_y = roster_y + 45 + (i * 26)
                pygame.draw.circle(screen, SUCCESS_COLOR, (roster_x + 20, name_y + 12), 5)
                draw_text(p['name'], font_small, TEXT_COLOR, roster_x + 40, name_y)

        # Footer Area: Status & Buttons
        footer_y = card_y + card_h - 100
        
        # Technical Readout
        draw_text(f"URL: {mobile_race_url}", font_tiny, TEXT_MUTED, card_x + 50, footer_y + 65)
        
        # Controls
        start_btn_rect = pygame.Rect(card_x + 420, footer_y, 180, 55)
        back_btn_rect = pygame.Rect(card_x + 615, footer_y, 135, 55)
        
        # Hover detection for buttons
        mx, my = pygame.mouse.get_pos()
        
        # START BUTTON
        can_start = len(players_list) > 0 and not mobile_server.race_started
        start_color = CYAN if can_start else TEXT_MUTED
        if can_start and start_btn_rect.collidepoint((mx, my)):
            draw_glow_rect(start_btn_rect.x, start_btn_rect.y, start_btn_rect.w, start_btn_rect.h, CYAN, layers=4)
            pygame.draw.rect(screen, (20, 60, 100), start_btn_rect, border_radius=12)
        else:
            pygame.draw.rect(screen, (10, 25, 50), start_btn_rect, border_radius=12)
        pygame.draw.rect(screen, start_color, start_btn_rect, 2, border_radius=12)
        draw_text("START RACE", font_small, start_color, start_btn_rect.x + 35, start_btn_rect.y + 15)
        
        # BACK BUTTON
        if back_btn_rect.collidepoint((mx, my)):
            draw_glow_rect(back_btn_rect.x, back_btn_rect.y, back_btn_rect.w, back_btn_rect.h, WARNING_COLOR, layers=4)
            pygame.draw.rect(screen, (80, 40, 10), back_btn_rect, border_radius=12)
        else:
            pygame.draw.rect(screen, (30, 20, 10), back_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WARNING_COLOR, back_btn_rect, 2, border_radius=12)
        draw_text("BACK", font_small, WARNING_COLOR, back_btn_rect.x + 45, back_btn_rect.y + 15)

        # Result Overlay (if race finished)
        if mobile_server.race_finished and mobile_server.winner:
            overlay = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            overlay.fill((5, 10, 30, 230))
            screen.blit(overlay, (card_x, card_y))
            
            w = mobile_server.winner
            winner_name = w.get('name', 'PILOT')
            race_m = w.get('race_marks', 0)
            quiz_m = w.get('quiz_marks', 0)
            total_m = w.get('total', 0)
            
            draw_text("UPLINK COMPLETE", font_title, SUCCESS_COLOR, card_x + 240, card_y + 120)
            draw_text(f"WINNER: {winner_name}", font_menu, WHITE, card_x + 250, card_y + 180)
            
            # Marks Breakdown
            draw_text(f"Race Marks: {race_m}/50", font_text, TEXT_SUBCOLOR, card_x + 300, card_y + 230)
            draw_text(f"Quiz Marks: {quiz_m}/50", font_text, TEXT_SUBCOLOR, card_x + 300, card_y + 270)
            
            # Total Score
            draw_glow_rect(card_x + 280, card_y + 310, 240, 60, SUCCESS_COLOR, layers=3)
            pygame.draw.rect(screen, (10, 30, 20), (card_x + 280, card_y + 310, 240, 60), border_radius=10)
            draw_text(f"TOTAL: {total_m}/100", font_menu, SUCCESS_COLOR, card_x + 305, card_y + 325)
            
            draw_text("PRESS R TO RESET FOR NEW STUDENTS", font_tiny, WARNING_COLOR, card_x + 265, card_y + 400)
            
            # Reset Button in Finish State
            reset_btn_rect = pygame.Rect(card_x + 300, card_y + 440, 200, 50)
            if reset_btn_rect.collidepoint((mx, my)):
                pygame.draw.rect(screen, (30, 80, 120), reset_btn_rect, border_radius=10)
            pygame.draw.rect(screen, CYAN, reset_btn_rect, 2, border_radius=10)
            draw_text("NEW SESSION", font_small, CYAN, reset_btn_rect.x + 45, reset_btn_rect.y + 12)

    elif game_state == "settings":
        settings_screen.update()
        settings_screen.draw(screen)
    elif game_state == "level_select":
        progress_data = load_progress()

        completed_levels = []
        for level_key, pdata in progress_data.items():
            if pdata.get("completed"):
                try:
                    completed_levels.append(int(level_key))
                except ValueError:
                    pass

        if completed_levels:
            highest_completed = max(completed_levels)
            level_select_screen.total_levels = max(18, highest_completed + 6)
        else:
            level_select_screen.total_levels = 18

        max_page = max(0, (level_select_screen.total_levels - 1) // level_select_screen.cards_per_page)
        if level_select_screen.current_page > max_page:
            level_select_screen.current_page = max_page

        level_select_screen.set_progress_data(progress_data)
        level_select_screen.create_level_cards()
        level_select_screen.update()
        level_select_screen.draw(screen)
    elif game_state == STATE_PLAYING:
        draw_play_screen()
    elif game_state == STATE_PAUSED:
        draw_play_screen()
        draw_pause_overlay()
    elif game_state == STATE_WON:
        draw_play_screen()
        if win_rewatch_mode:
            info_rect = pygame.Rect(24, 18, 560, 44)
            pygame.draw.rect(screen, (9, 18, 44), info_rect, border_radius=14)
            pygame.draw.rect(screen, PANEL_BORDER_COLOR, info_rect, 1, border_radius=14)
            replay_total = max(1, len(player_replay_path))
            replay_now = min(replay_index, replay_total)
            draw_text(f"Rewatching run... {replay_now}/{replay_total}  (auto-next when done)", font_small, CYAN, 38, 31)
        else:
            draw_win_overlay()
    elif game_state == STATE_LOST:
        draw_play_screen()
        draw_lose_overlay()
    pygame.display.flip()

pygame.quit()
sys.exit()
