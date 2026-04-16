# maze.py
import random
from settings import DEAD_END_BRANCH_ATTEMPTS, DEAD_END_MAX_LENGTH


def create_empty_maze(rows, cols):
    return [[1 for _ in range(cols)] for _ in range(rows)]


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def neighbors(cell, rows, cols):
    r, c = cell
    result = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            result.append((nr, nc))
    return result


def add_dead_end_branches(maze, guaranteed_path, rows, cols, level):
    """
    Add small side branches that end in dead ends.
    This makes the maze feel more realistic and more challenging.
    """
    path_set = set(guaranteed_path)
    attempts = DEAD_END_BRANCH_ATTEMPTS + min(level, 10)

    for _ in range(attempts):
        branch_start = random.choice(guaranteed_path[:-1]) if len(guaranteed_path) > 1 else guaranteed_path[0]

        possible = []
        for nr, nc in neighbors(branch_start, rows, cols):
            if maze[nr][nc] == 1:
                possible.append((nr, nc))

        if not possible:
            continue

        current = random.choice(possible)
        branch_length = random.randint(1, DEAD_END_MAX_LENGTH)
        prev = branch_start

        for _ in range(branch_length):
            cr, cc = current
            maze[cr][cc] = 0

            next_options = []
            for nr, nc in neighbors(current, rows, cols):
                if (nr, nc) != prev and maze[nr][nc] == 1 and (nr, nc) not in path_set:
                    next_options.append((nr, nc))

            if not next_options:
                break

            prev = current
            current = random.choice(next_options)

    return maze


def generate_maze(rows, cols, start_pos, goal_pos, level=1, difficulty="Medium"):
    maze = create_empty_maze(rows, cols)

    difficulty_bias = {
        "Easy": 0.08,
        "Medium": 0.00,
        "Hard": -0.08,
    }.get(difficulty, 0.0)

    level_bias = min(level * 0.008, 0.16)

    open_probability = clamp(0.67 + difficulty_bias - level_bias, 0.35, 0.78)
    wall_probability = clamp(0.26 - difficulty_bias + level_bias, 0.16, 0.44)

    guaranteed_path = []
    row, col = start_pos
    maze[row][col] = 0
    guaranteed_path.append((row, col))

    while (row, col) != goal_pos:
        move_options = []

        if row < goal_pos[0]:
            move_options.append((row + 1, col))
        if col < goal_pos[1]:
            move_options.append((row, col + 1))

        if not move_options:
            break

        row, col = random.choice(move_options)
        maze[row][col] = 0
        guaranteed_path.append((row, col))

    for r in range(rows):
        for c in range(cols):
            if (r, c) not in [start_pos, goal_pos]:
                if random.random() < open_probability:
                    maze[r][c] = 0

    for r in range(rows):
        for c in range(cols):
            if (r, c) not in [start_pos, goal_pos]:
                if random.random() < wall_probability:
                    maze[r][c] = 1

    for r, c in guaranteed_path:
        maze[r][c] = 0

    sr, sc = start_pos
    gr, gc = goal_pos

    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = sr + dr, sc + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            maze[nr][nc] = 0

        nr, nc = gr + dr, gc + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            maze[nr][nc] = 0

    maze = add_dead_end_branches(maze, guaranteed_path, rows, cols, level)

    return maze