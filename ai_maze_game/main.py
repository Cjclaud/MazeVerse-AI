# main.py
import sys
import time
import random
from collections import deque, Counter

import pygame

from settings import *
from splash_screen import SplashScreen
from main_menu import MainMenu
from settings_menu import SettingsMenu
from level_select import LevelSelect
from maze import generate_maze
from solver import bfs_solve, a_star_solve
from score_manager import get_best_score, update_best_score
from progress_manager import load_progress

# -------------------------------------------------
# PYGAME INITIALIZATION
# -------------------------------------------------
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# -------------------------------------------------
# BACKGROUND IMAGE
# -------------------------------------------------
try:
    bg_image = pygame.image.load("assets/images/game_bg.png").convert()
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
if SOUND_ENABLED:
    move_sound = pygame.mixer.Sound("assets/sounds/move.wav")
    win_sound = pygame.mixer.Sound("assets/sounds/win.wav")
    click_sound = pygame.mixer.Sound("assets/sounds/click.wav")

    move_sound.set_volume(SOUND_VOLUME)
    win_sound.set_volume(SOUND_VOLUME)
    click_sound.set_volume(SOUND_VOLUME)
else:
    move_sound = None
    win_sound = None
    click_sound = None

# -------------------------------------------------
# Background Music
# -------------------------------------------------
if MUSIC_ENABLED:
    pygame.mixer.music.load("assets/sounds/bg_music.mp3")
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    pygame.mixer.music.play(-1)  # loop forever

# -------------------------------------------------
# GAME STATES
# -------------------------------------------------
STATE_SPLASH = "splash"
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_WON = "won"

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
# SCORE / RECORDS / FOG
# -------------------------------------------------
score = 0
total_score = 0
best_score = 0
new_record = False
level_reward_applied = False

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
level_select_screen = LevelSelect(total_levels=20)

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


def get_dynamic_cell_size(current_rows, current_cols):
    max_maze_width = 720
    max_maze_height = 620

    size_by_width = max_maze_width // current_cols
    size_by_height = max_maze_height // current_rows
    return max(MIN_CELL_SIZE, min(size_by_width, size_by_height))


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


def create_level():
    global rows, cols, cell_size, start_pos, goal_pos, current_maze
    global player_row, player_col, moves_count
    global ai_path, ai_explored, ai_mode
    global visible_explored, visible_path
    global animating, animation_stage, animation_index, animation_counter
    global start_time, player_time, final_player_time, ai_time, timer_running, win_time
    global score, manual_hints_used, auto_hints_used, new_record, best_score
    global render_player_x, render_player_y, target_player_x, target_player_y

    base_rows, base_cols = difficulty_config[difficulty]

    # Endless scaling
    size_growth = (level - 1) // 2
    rows = min(base_rows + size_growth, MAX_ROWS)
    cols = min(base_cols + size_growth, MAX_COLS)

    cell_size = get_dynamic_cell_size(rows, cols)

    start_pos = (0, 0)
    goal_pos = (rows - 1, cols - 1)

    current_maze = generate_maze(rows, cols, start_pos, goal_pos, level=level, difficulty=difficulty)

    player_row, player_col = start_pos
    render_player_x = MAZE_OFFSET_X + player_col * cell_size + cell_size // 2
    render_player_y = MAZE_OFFSET_Y + player_row * cell_size + cell_size // 2
    target_player_x = render_player_x
    target_player_y = render_player_y
    moves_count = 0

    ai_path = []
    ai_explored = []
    ai_mode = "Not active"

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
    timer_running = True
    win_time = None

    score = BASE_LEVEL_SCORE + (level - 1) * LEVEL_BONUS
    if fog_enabled:
        score += FOG_BONUS

    manual_hints_used = 0
    auto_hints_used = 0
    new_record = False
    best_score = get_best_score(difficulty)

    reset_player_tracking()


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
            register_move_distance()

            target_player_x = MAZE_OFFSET_X + player_col * cell_size + cell_size // 2
            target_player_y = MAZE_OFFSET_Y + player_row * cell_size + cell_size // 2
            
            if SOUND_ENABLED and move_sound:
                move_sound.play()


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
    global level, game_state
    level += 1
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

    hint_path = full_path[1:1 + HINT_PREVIEW_STEPS]
    hint_level = 1
    hint_message = "Hint: best next path"
    update_score(-5)

    if auto:
        auto_hints_used += 1
        last_auto_hint_time = time.time()
    else:
        manual_hints_used += 1


def request_manual_hint():
    apply_hint(auto=False)


def update_adaptive_help():
    if not auto_help_enabled or game_state != STATE_PLAYING:
        return

    state, shortest_path = determine_help_state()
    _ = shortest_path

    now = time.time()
    if now - last_auto_hint_time < 4.0:
        return

    if state in ("Needs guidance", "Struggling"):
        apply_hint(auto=True)


def finish_level_rewards():
    global total_score, new_record, best_score
    total_score += score
    new_record, best_score = update_best_score(difficulty, total_score)


def calculate_ai_score():
    base = 100

    # penalties
    hint_penalty = manual_hints_used * 12 + auto_hints_used * 18
    move_penalty = max(0, moves_count - (ROWS + COLS)) * 0.6
    time_penalty = final_player_time * 0.25
    wrong_penalty = wrong_turns * 4 if 'wrong_turns' in globals() else 0

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
        pygame.draw.rect(screen, BG_ACCENT_1, (0, 0, WIDTH, HEIGHT // 3))
        pygame.draw.rect(screen, BG_ACCENT_2, (0, HEIGHT // 3, WIDTH, HEIGHT // 6))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((4, 8, 20, 120))
    screen.blit(overlay, (0, 0))

    t = pygame.time.get_ticks()
    glow1_x = 160 + int(18 * pygame.math.Vector2(1, 0).rotate(t * 0.02).x)
    glow2_x = 710 + int(12 * pygame.math.Vector2(1, 0).rotate(t * 0.03).x)
    glow3_x = 1080 + int(16 * pygame.math.Vector2(1, 0).rotate(t * 0.025).x)

    draw_glow_circle(glow1_x, 90, 55, PANEL_GLOW_COLOR, layers=6)
    draw_glow_circle(glow2_x, 70, 40, GOAL_COLOR, layers=5)
    draw_glow_circle(glow3_x, 110, 55, PLAYER_COLOR, layers=6)

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
                # 🔥 WALL TILE (Layered Neon Effect)
                draw_glow_rect(
                    inner_rect.x,
                    inner_rect.y,
                    inner_rect.width,
                    inner_rect.height,
                    WALL_GLOW_COLOR,
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
                # 🌌 PATH TILE (Soft futuristic panel)
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

                # subtle glow center
                draw_glow_rect(
                    inner_rect.x + 6,
                    inner_rect.y + 6,
                    inner_rect.width - 12,
                    inner_rect.height - 12,
                    PATH_GLOW_COLOR,
                    layers=1,
                    radius=BORDER_RADIUS
                )

    # 🔥 START TILE
    sx = MAZE_OFFSET_X + start_pos[1] * cell_size
    sy = MAZE_OFFSET_Y + start_pos[0] * cell_size

    draw_glow_rect(sx, sy, cell_size, cell_size, START_GLOW_COLOR, layers=4)
    pygame.draw.rect(screen, START_COLOR, (sx, sy, cell_size, cell_size), border_radius=BORDER_RADIUS)

    # 🔥 GOAL TILE (PULSING)
    gx = MAZE_OFFSET_X + goal_pos[1] * cell_size
    gy = MAZE_OFFSET_Y + goal_pos[0] * cell_size

    pulse = int((pygame.time.get_ticks() % 1000) * 0.01)
    size_offset = pulse % 4

    draw_glow_rect(
        gx - size_offset,
        gy - size_offset,
        cell_size + size_offset * 2,
        cell_size + size_offset * 2,
        GOAL_GLOW_COLOR,
        layers=5
    )

    pygame.draw.rect(
        screen,
        GOAL_COLOR,
        (gx, gy, cell_size, cell_size),
        border_radius=BORDER_RADIUS
    )


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


def draw_fog_of_war():
    if not fog_enabled:
        return

    fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fog_surface.fill((*FOG_COLOR, FOG_ALPHA))

    for row in range(len(current_maze)):
        for col in range(len(current_maze[0])):
            distance = abs(row - player_row) + abs(col - player_col)

            if distance <= VISION_RADIUS:
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
    pygame.draw.circle(fog_surface, (0, 0, 0, 0), (px, py), cell_size * (VISION_RADIUS + 1))

    screen.blit(fog_surface, (0, 0))


def draw_side_panel():
    draw_glow_rect(SIDE_PANEL_X, SIDE_PANEL_Y, SIDE_PANEL_WIDTH, SIDE_PANEL_HEIGHT, PANEL_GLOW_COLOR, layers=5, radius=PANEL_RADIUS)

    panel_rect = pygame.Rect(SIDE_PANEL_X, SIDE_PANEL_Y, SIDE_PANEL_WIDTH, SIDE_PANEL_HEIGHT)
    pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=PANEL_RADIUS)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, panel_rect, 2, border_radius=PANEL_RADIUS)

    shown_time = final_player_time if not timer_running and player_won() else player_time

    draw_text("GAME INFO", font_title, TEXT_COLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 20)
    draw_text(f"Difficulty: {difficulty}", font_text, TEXT_SUBCOLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 80)
    draw_text(f"Level: {level}", font_text, TEXT_SUBCOLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 115)
    draw_text(f"Moves: {moves_count}", font_text, TEXT_COLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 150)
    draw_text(f"Score: {score}", font_text, SUCCESS_COLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 185)
    draw_text(f"Total Score: {total_score}", font_small, TEXT_SUBCOLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 215)
    draw_text(f"Best Score: {best_score}", font_small, WARNING_COLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 240)
    draw_text(f"Fog: {'ON' if fog_enabled else 'OFF'}", font_small, TEXT_COLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 265)
    draw_text(f"AI: {ai_mode}", font_small, TEXT_COLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 290)
    draw_text(f"Path length: {len(ai_path)}", font_small, TEXT_COLOR, SIDE_PANEL_X + 20, SIDE_PANEL_Y + 315)

    timing_box = pygame.Rect(SIDE_PANEL_X + 18, SIDE_PANEL_Y + 345, SIDE_PANEL_WIDTH - 36, 110)
    pygame.draw.rect(screen, BG_ACCENT_1, timing_box, border_radius=18)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, timing_box, 1, border_radius=18)
    draw_text("PERFORMANCE", font_text, TEXT_COLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 358)
    draw_text(f"Player Time: {shown_time}s", font_small, TEXT_SUBCOLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 394)
    draw_text(f"AI Time: {ai_time}s", font_small, TEXT_SUBCOLOR, SIDE_PANEL_X + 190, SIDE_PANEL_Y + 394)
    draw_text(f"Wrong Turns: {wrong_turns}", font_small, TEXT_SUBCOLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 418)

    help_color = SUCCESS_COLOR if help_state == "Normal" else WARNING_COLOR if help_state == "Needs guidance" else DANGER_COLOR
    draw_text(f"Help: {help_state}", font_small, help_color, SIDE_PANEL_X + 190, SIDE_PANEL_Y + 418)

    hint_box = pygame.Rect(SIDE_PANEL_X + 18, SIDE_PANEL_Y + 470, SIDE_PANEL_WIDTH - 36, 110)
    pygame.draw.rect(screen, BG_ACCENT_1, hint_box, border_radius=18)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, hint_box, 1, border_radius=18)
    draw_text("HINT SYSTEM", font_text, TEXT_COLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 483)
    draw_text("Hint Mode: Standard", font_small, HINT_STRONG_COLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 519)
    draw_text(hint_message[:32], font_small, TEXT_SUBCOLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 543)
    draw_text(f"Manual: {manual_hints_used} | Auto: {auto_hints_used}", font_small, TEXT_MUTED, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 565)

    controls_box = pygame.Rect(SIDE_PANEL_X + 18, SIDE_PANEL_Y + 595, SIDE_PANEL_WIDTH - 36, 105)
    pygame.draw.rect(screen, BG_ACCENT_1, controls_box, border_radius=18)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, controls_box, 1, border_radius=18)

    draw_text("CONTROLS", font_text, TEXT_COLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 607)
    draw_text("Move = Arrows/WASD | H = Hint | J = Auto Help", font_tiny, TEXT_SUBCOLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 641)
    draw_text("F = Fog | B = BFS | P = A* | R = Reset | ESC = Exit", font_tiny, TEXT_SUBCOLOR, SIDE_PANEL_X + 30, SIDE_PANEL_Y + 663)

    if new_record:
        draw_text("NEW BEST SCORE!", font_tiny, SUCCESS_COLOR, SIDE_PANEL_X + 190, SIDE_PANEL_Y + 80)


def draw_play_screen():
    draw_background()
    draw_particles()
    draw_text(TITLE, font_title, TEXT_COLOR, 45, 28)
    draw_maze()
    draw_hover_tile()
    draw_explored()
    draw_ai_path()
    draw_hint_path()
    draw_player()
    draw_fog_of_war()
    draw_side_panel()


def draw_win_overlay():
    overlay_rect = pygame.Rect(120, 220, 720, 220)
    draw_glow_rect(120, 220, 720, 220, SUCCESS_COLOR, layers=5, radius=24)
    pygame.draw.rect(screen, PANEL_COLOR, overlay_rect, border_radius=24)
    pygame.draw.rect(screen, PANEL_BORDER_COLOR, overlay_rect, 2, border_radius=24)

    draw_text("MISSION COMPLETE", font_title, SUCCESS_COLOR, 160, 245)
    draw_text(f"Level {level} finished in {final_player_time}s with {moves_count} moves.", font_text, TEXT_COLOR, 160, 295)
    draw_text(f"Level Score: {score}", font_text, WARNING_COLOR, 160, 330)
    draw_text(f"Total Score: {total_score}", font_text, TEXT_SUBCOLOR, 160, 365)

    if new_record:
        draw_text("New Best Score Achieved!", font_text, SUCCESS_COLOR, 160, 398)
    elif ENDLESS_MODE:
        draw_text("Next level loading automatically...", font_text, TEXT_SUBCOLOR, 160, 398)
    else:
        draw_text("Press N for Next Level or R to Replay", font_text, TEXT_SUBCOLOR, 160, 398)


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

    if game_state == STATE_PLAYING and timer_running:
        player_time = int(time.time() - start_time)
        update_adaptive_help()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == STATE_MENU:
            action = menu_screen.handle_event(event)
            if action == "start":
                print("Start Game clicked")
                level = 1
                total_score = 0
                best_score = get_best_score(difficulty)
                new_record = False
                
                create_level()
                level_reward_applied = False
                game_state = STATE_PLAYING
            elif action == "level_select":
                game_state = "level_select"
            elif action == "settings":
                game_state = "settings"
            elif action == "exit":
                pygame.quit()
                raise SystemExit

        elif game_state == "settings":
            action = settings_screen.handle_event(event)
            if action == "back":
                print(settings_screen.get_settings())
                game_state = "menu"

        elif game_state == "level_select":
            result = level_select_screen.handle_event(event)

            if result:
                if result["action"] == "back":
                    game_state = "menu"

                elif result["action"] == "play_level":
                    selected_level = result["level"]
                    current_level = selected_level
                    print(f"Opening Level {current_level}")
                    game_state = STATE_PLAYING

        elif event.type == pygame.KEYDOWN:
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
                    hint_message = f"Auto Help {'enabled' if auto_help_enabled else 'disabled'}"
                elif event.key == pygame.K_f:
                    fog_enabled = not fog_enabled
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

        elif game_state == STATE_WON:
            if event.key == pygame.K_n and not ENDLESS_MODE:
                next_level()
                level_reward_applied = False
            elif event.key == pygame.K_r:
                create_level()
                level_reward_applied = False
                game_state = STATE_PLAYING

            if event.key == pygame.K_ESCAPE:
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
            
            if SOUND_ENABLED and win_sound:
                win_sound.play()
                pygame.mixer.music.pause()  # dramatic effect
            
            if not level_reward_applied:
                finish_level_rewards()

                ai_score = calculate_ai_score()

                from progress_manager import update_level_progress

                update_level_progress(
                    level=level,
                    score=score,
                    ai_score=ai_score,
                    time_taken=final_player_time,
                    items_used=["Hints" if manual_hints_used else "None"]
                )

                level_reward_applied = True

            game_state = STATE_WON

    elif game_state == STATE_WON and ENDLESS_MODE and win_time is not None:
        if time.time() - win_time >= AUTO_ADVANCE_DELAY:
            next_level()
            level_reward_applied = False

    if game_state == STATE_SPLASH:
        pass
    elif game_state == STATE_MENU:
        menu_screen.update()
        menu_screen.draw(screen)
    elif game_state == "settings":
        settings_screen.update()
        settings_screen.draw(screen)
    elif game_state == "level_select":
        progress_data = load_progress()
        level_select_screen.set_progress_data(progress_data)
        level_select_screen.update()
        level_select_screen.draw(screen)
    elif game_state == STATE_PLAYING:
        draw_play_screen()
    elif game_state == STATE_WON:
        draw_play_screen()
        draw_win_overlay()
    pygame.display.flip()

pygame.quit()
sys.exit()
