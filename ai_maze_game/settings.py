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
SIDE_PANEL_HEIGHT = 700

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
MAX_ROWS = 26
MAX_COLS = 34
MIN_CELL_SIZE = 18

# -----------------------------
# SCORING
# -----------------------------
BASE_LEVEL_SCORE = 100
MOVE_PENALTY = 1
LEVEL_BONUS = 15
FOG_BONUS = 10

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