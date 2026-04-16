# settings.py
# -------------------------------------------------
# Global settings for the Adaptive Intelligent Maze Navigation Game
# -------------------------------------------------

# -----------------------------
# WINDOW SETTINGS
# -----------------------------
WIDTH = 1280
HEIGHT = 820
FPS = 60
TITLE = "Adaptive Intelligent Maze Navigation Game"

# -----------------------------
# MAZE SETTINGS
# -----------------------------
ROWS = 15
COLS = 20
CELL_SIZE = 35

# -----------------------------
# LAYOUT SETTINGS
# -----------------------------
MAZE_OFFSET_X = 50
MAZE_OFFSET_Y = 90

SIDE_PANEL_X = 830
SIDE_PANEL_Y = 70
SIDE_PANEL_WIDTH = 390
SIDE_PANEL_HEIGHT = 720

# -----------------------------
# FUTURISTIC COLOR PALETTE
# -----------------------------
BG_COLOR = (4, 6, 18)
BG_ACCENT_1 = (10, 16, 40)
BG_ACCENT_2 = (20, 24, 68)
BG_ACCENT_3 = (70, 35, 130)

GRID_COLOR = (65, 125, 255)
GRID_SOFT_COLOR = (32, 58, 110)
GRID_FAINT = (20, 35, 75)

WALL_COLOR = (58, 105, 235)
WALL_INNER_COLOR = (78, 145, 255)
WALL_GLOW_COLOR = (85, 120, 255)

PATH_COLOR = (8, 14, 30)
PATH_ALT_COLOR = (12, 20, 42)
PATH_GLOW_COLOR = (30, 70, 145)

START_COLOR = (90, 255, 180)
START_GLOW_COLOR = (0, 255, 200)

GOAL_COLOR = (255, 80, 190)
GOAL_GLOW_COLOR = (255, 120, 220)

PLAYER_COLOR = (0, 245, 255)
PLAYER_CORE_COLOR = (220, 255, 255)
PLAYER_TRAIL_COLOR = (0, 180, 255)

EXPLORED_COLOR = (255, 196, 0)
WIN_COLOR = (0, 255, 150)
AI_PATH_COLOR = (0, 255, 180)

HINT_COLOR = (130, 245, 255)
HINT_STRONG_COLOR = (255, 225, 120)

PANEL_COLOR = (10, 16, 34)
PANEL_INNER_COLOR = (8, 12, 28)
PANEL_BORDER_COLOR = (70, 145, 255)
PANEL_GLOW_COLOR = (0, 170, 255)

TEXT_COLOR = (240, 247, 255)
TEXT_SUBCOLOR = (175, 220, 255)
TEXT_MUTED = (130, 165, 220)
TEXT_HIGHLIGHT = (120, 255, 220)

SUCCESS_COLOR = (0, 255, 150)
WARNING_COLOR = (255, 210, 90)
DANGER_COLOR = (255, 110, 140)

# Fog of war
FOG_COLOR = (3, 5, 14)
FOG_ALPHA = 205
VISION_RADIUS = 2

# Splash / Loading Screen
SPLASH_DURATION = 6500  # milliseconds

# Extra futuristic colors
DEEP_SPACE = (5, 8, 20)
CYAN = (0, 255, 255)
SOFT_CYAN = (120, 255, 255)
ELECTRIC_BLUE = (0, 140, 255)
WHITE = (240, 245, 255)
GLOW_BLUE = (40, 120, 255)
PURPLE_GLOW = (165, 90, 255)
PINK_GLOW = (255, 100, 210)

# -----------------------------
# OPTIONAL UI EFFECT VALUES
# -----------------------------
BORDER_RADIUS = 12
PANEL_RADIUS = 24
CELL_PADDING = 2
GLOW_STRENGTH = 10
WALL_GLOW_STRENGTH = 12
PLAYER_GLOW_STRENGTH = 16
GOAL_PULSE_SPEED = 0.004
PLAYER_PULSE_SPEED = 0.005

# -----------------------------
# GAME PROGRESSION
# -----------------------------
ENDLESS_MODE = True
AUTO_ADVANCE_DELAY = 2.5

# Smart endless growth:
# Maze keeps growing for a long time, then size stops increasing
# and difficulty continues through traps / fewer helpful items.
MAX_ROWS = 40
MAX_COLS = 52
MIN_CELL_SIZE = 12

# -----------------------------
# SCORING
# -----------------------------
BASE_LEVEL_SCORE = 100
MOVE_PENALTY = 1
LEVEL_BONUS = 15
FOG_BONUS = 10

# -----------------------------
# TRAP / TIMER RULES
# -----------------------------
TRAP_RESPAWN_ENABLED = True
TRAP_SCORE_PENALTY = 12
DEADLY_TRAPS_START_LEVEL = 10

USE_TIME_GRADING = True
NORMAL_MODE_TIME_FAIL = False
HARD_MODE_TIME_FAIL = True
TIMER_WARNING_SECONDS = 10

# -----------------------------
# RIVAL AI / WOW FACTORS
# -----------------------------
RIVAL_GHOST_ENABLED = True
RIVAL_GHOST_BASE_DELAY = 8
RIVAL_GHOST_MIN_DELAY = 4
RIVAL_GHOST_TOUCH_PENALTY = 15

# Rotating world themes. Each theme slightly changes visuals and gameplay.
THEME_ROTATION = [
    "Neon Circuit",
    "Frost Vault",
    "Ember Core",
    "Void Grid",
]

THEME_RULES = {
    "Neon Circuit": {
        "bg_top": (10, 18, 52),
        "bg_mid": (18, 34, 92),
        "path_glow": (30, 90, 170),
        "wall_glow": (85, 140, 255),
        "trap_color": (255, 110, 150),
        "fog_alpha": 190,
        "vision_bonus": 0,
        "timer_bonus": 4,
        "trap_bonus": 0,
        "powerup_bonus": 0,
        "ghost_delay": 8,
        "reveal_bonus_frames": 0,
        "checkpoint_reward": "score",
        "moving_trap_bonus": 0,
    },
    "Frost Vault": {
        "bg_top": (12, 28, 56),
        "bg_mid": (24, 62, 120),
        "path_glow": (90, 210, 255),
        "wall_glow": (150, 235, 255),
        "trap_color": (140, 225, 255),
        "fog_alpha": 165,
        "vision_bonus": 1,
        "timer_bonus": 8,
        "trap_bonus": 0,
        "powerup_bonus": 1,
        "ghost_delay": 9,
        "reveal_bonus_frames": 120,
        "checkpoint_reward": "shield",
        "moving_trap_bonus": 0,
    },
    "Ember Core": {
        "bg_top": (42, 16, 8),
        "bg_mid": (88, 30, 14),
        "path_glow": (170, 70, 20),
        "wall_glow": (255, 130, 60),
        "trap_color": (255, 95, 40),
        "fog_alpha": 205,
        "vision_bonus": 0,
        "timer_bonus": -4,
        "trap_bonus": 1,
        "powerup_bonus": 0,
        "ghost_delay": 7,
        "reveal_bonus_frames": 0,
        "checkpoint_reward": "none",
        "moving_trap_bonus": 1,
    },
    "Void Grid": {
        "bg_top": (16, 10, 34),
        "bg_mid": (44, 22, 78),
        "path_glow": (120, 70, 210),
        "wall_glow": (200, 90, 255),
        "trap_color": (210, 120, 255),
        "fog_alpha": 225,
        "vision_bonus": -1,
        "timer_bonus": 0,
        "trap_bonus": 1,
        "powerup_bonus": 0,
        "ghost_delay": 6,
        "reveal_bonus_frames": 0,
        "checkpoint_reward": "reveal",
        "moving_trap_bonus": 1,
    },
}

AI_DIFFICULTY_SETTINGS = {
    "Easy": {
        "delay_bonus": 2,
        "collision_penalty": 10,
    },
    "Medium": {
        "delay_bonus": 0,
        "collision_penalty": 15,
    },
    "Hard": {
        "delay_bonus": -1,
        "collision_penalty": 20,
    },
    "Insane": {
        "delay_bonus": -2,
        "collision_penalty": 25,
    },
}

# -----------------------------
# HINT SETTINGS
# -----------------------------
HINT_PREVIEW_STEPS = 3
AUTO_HELP_DEFAULT = True
AUTO_HELP_COLOR = (180, 100, 255)
IDLE_HINT_THRESHOLD = 10.0
WRONG_TURN_HINT_THRESHOLD = 3
LOOP_HINT_THRESHOLD = 2
LONG_ROUTE_HINT_FACTOR = 1.5

# -----------------------------
# FOG OF WAR
# -----------------------------
FOG_OF_WAR_ENABLED = True

# -----------------------------
# DEAD-END GENERATION
# -----------------------------
DEAD_END_BRANCH_ATTEMPTS = 12
DEAD_END_MAX_LENGTH = 4

# -----------------------------
# Audio Settings
# -----------------------------
SOUND_ENABLED = True
MUSIC_ENABLED = True

SOUND_VOLUME = 0.5
MUSIC_VOLUME = 0.4

# Per-sound effect multipliers (0.0 to 1.5+)
SFX_MOVE_VOLUME_MULT = 0.65
SFX_WIN_VOLUME_MULT = 1.0
SFX_CLICK_VOLUME_MULT = 0.8
SFX_WALL_HIT_VOLUME_MULT = 0.75
SFX_TRAP_HIT_VOLUME_MULT = 1.0
SFX_POWERUP_VOLUME_MULT = 0.95

# Music shaping
MUSIC_MENU_VOLUME_MULT = 0.85
MUSIC_GAMEPLAY_VOLUME_MULT = 1.0

# Ducking: lowers music briefly while SFX plays
MUSIC_DUCKING_ENABLED = True
MUSIC_DUCK_VOLUME_MULT = 0.45
MUSIC_DUCK_DURATION_SEC = 0.25

# Extra emphasis for wall-hit feedback
WALL_HIT_MUSIC_DUCK_MULT = 0.20
WALL_HIT_MUSIC_DUCK_DURATION_SEC = 0.32

# -----------------------------
# Sound File Configuration
# -----------------------------
# You can replace these with your own files.
MOVE_SOUND_FILE = "assets/sounds/move.wav"
WIN_SOUND_FILE = "assets/sounds/win.wav"
CLICK_SOUND_FILE = "assets/sounds/click.wav"

# New event sounds (with fallback in code if files are missing)
WALL_HIT_SOUND_FILE = "assets/sounds/wall_hit.wav.mp3"
TRAP_HIT_SOUND_FILE = "assets/sounds/trap_hit.wav.mp3"
POWERUP_SOUND_FILE = "assets/sounds/powerup.wav.mp3"

# -----------------------------
# Music Playlists
# -----------------------------
# Main menu rotates through this list instead of repeating one song forever.
MENU_MUSIC_PLAYLIST = [
    "assets/sounds/menu_theme_1.mp3",
    "assets/sounds/menu_theme_2.mp3",
    "assets/sounds/bg_music.mp3",
]

# Gameplay music by user mode / difficulty.
# You can point each mode to one or multiple tracks.
GAMEPLAY_MUSIC_BY_DIFFICULTY = {
    "Easy": [
        "assets/sounds/game_easy.mp3",
        "assets/sounds/bg_music.mp3",
    ],
    "Medium": [
        "assets/sounds/game_medium.mp3",
        "assets/sounds/bg_music.mp3",
    ],
    "Hard": [
        "assets/sounds/game_hard.mp3",
        "assets/sounds/bg_music.mp3",
    ],
}

# -----------------------------
# BACKGROUND SETTINGS
# -----------------------------
SETTINGS_BG_IMAGE = "assets/backgrounds/settings_bg.png"

# Parallax / animation
STAR_SCROLL_SPEED = 0.02
NEBULA_PULSE_SPEED = 0.0015
BACKGROUND_DIM_ALPHA = 120  # dark overlay for readability
