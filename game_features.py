# game_features.py
# -------------------------------------------------
# Gameplay feature layer for the Intelligent Maze Game
# Adds:
# - traps
# - power-ups
# - checkpoints
# -------------------------------------------------

import random


class Trap:
    def __init__(self, row, col, trap_type="static", damage=10):
        self.row = row
        self.col = col
        self.trap_type = trap_type
        self.damage = damage
        self.active = True
        self.pulse = random.randint(0, 100)
        self.move_dir = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
        self.move_cooldown = 0

    def update(self, maze=None, blocked_cells=None, speed_bonus=0):
        self.pulse = (self.pulse + 1) % 100
        blocked = set(blocked_cells or [])

        if self.trap_type == "blink":
            # Blinking traps create safe windows and sudden danger spikes.
            self.active = (self.pulse % 36) < 24
            return

        self.active = True

        if self.trap_type != "moving" or maze is None:
            return

        self.move_cooldown += 1
        threshold = max(8, 24 - int(speed_bonus) * 3)
        if self.move_cooldown < threshold:
            return

        self.move_cooldown = 0
        rows = len(maze)
        cols = len(maze[0]) if rows else 0

        directions = [self.move_dir, (self.move_dir[1], -self.move_dir[0]), (-self.move_dir[1], self.move_dir[0]), (-self.move_dir[0], -self.move_dir[1])]
        for dr, dc in directions:
            nr = self.row + dr
            nc = self.col + dc
            if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0 and (nr, nc) not in blocked:
                self.row = nr
                self.col = nc
                self.move_dir = (dr, dc)
                return

        self.move_dir = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])

    def position(self):
        return (self.row, self.col)


class PowerUp:
    def __init__(self, row, col, kind="reveal"):
        self.row = row
        self.col = col
        self.kind = kind
        self.collected = False
        self.pulse = random.randint(0, 100)

    def update(self):
        self.pulse = (self.pulse + 1) % 100

    def position(self):
        return (self.row, self.col)


class Checkpoint:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.activated = False

    def position(self):
        return (self.row, self.col)


def get_open_cells(maze, start_pos, goal_pos):
    cells = []
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if maze[r][c] == 0 and (r, c) != start_pos and (r, c) != goal_pos:
                cells.append((r, c))
    return cells


def place_traps(maze, start_pos, goal_pos, count=3):
    open_cells = get_open_cells(maze, start_pos, goal_pos)
    random.shuffle(open_cells)

    traps = []
    trap_pattern = ["static", "blink", "moving", "static", "moving"]
    for i, (row, col) in enumerate(open_cells[:count]):
        trap_type = trap_pattern[i % len(trap_pattern)]
        traps.append(Trap(row, col, trap_type=trap_type, damage=12))
    return traps


def place_powerups(maze, start_pos, goal_pos, count=2):
    open_cells = get_open_cells(maze, start_pos, goal_pos)
    random.shuffle(open_cells)

    powerups = []
    kinds = ["reveal", "shield", "score_boost"]

    for i, (row, col) in enumerate(open_cells[:count]):
        powerups.append(PowerUp(row, col, kind=kinds[i % len(kinds)]))
    return powerups


def place_checkpoint(maze, start_pos, goal_pos):
    """
    Place one checkpoint roughly around the middle of the maze.
    """
    open_cells = get_open_cells(maze, start_pos, goal_pos)

    if not open_cells:
        return None

    target_row = len(maze) // 2
    target_col = len(maze[0]) // 2

    best_cell = min(
        open_cells,
        key=lambda cell: abs(cell[0] - target_row) + abs(cell[1] - target_col)
    )

    return Checkpoint(best_cell[0], best_cell[1])
