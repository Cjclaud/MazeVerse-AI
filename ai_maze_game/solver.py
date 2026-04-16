# solver.py
# ---------------------------------------------
# This file contains the AI solving algorithms
# used in the maze game.
#
# Included algorithms:
# - Breadth-First Search (BFS)
# - A* Search
#
# Both algorithms return:
# 1. The final path from start to goal
# 2. The explored nodes during the search
#
# This helps the game:
# - visualize AI thinking
# - compare algorithms
# - animate exploration and final path
# ---------------------------------------------

from collections import deque
import heapq


def get_neighbors(position, maze):
    """
    Return all valid neighboring cells around the current position.

    A valid neighbor must:
    - stay inside maze boundaries
    - be an open path cell (0), not a wall (1)

    Parameters:
    - position: tuple (row, col)
    - maze: 2D list

    Returns:
    - list of valid neighboring (row, col) positions
    """
    row, col = position
    neighbors = []

    # Possible movement directions:
    # up, down, left, right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc

        # Check if inside the maze and not a wall
        if 0 <= new_row < len(maze) and 0 <= new_col < len(maze[0]):
            if maze[new_row][new_col] == 0:
                neighbors.append((new_row, new_col))

    return neighbors


def reconstruct_path(came_from, start, goal):
    """
    Reconstruct the final path from goal back to start.

    The 'came_from' dictionary stores:
    child_cell -> parent_cell

    So once the goal is found, we trace backwards
    until we reach the start.

    Parameters:
    - came_from: dictionary mapping each node to where it came from
    - start: starting cell
    - goal: goal cell

    Returns:
    - list representing the final path from start to goal
    """
    path = []
    current = goal

    # Walk backwards from goal to start
    while current != start:
        path.append(current)
        current = came_from[current]

    # Add the starting node
    path.append(start)

    # Reverse so path goes from start -> goal
    path.reverse()
    return path


# ---------------------------------------------------------
# BFS: BREADTH-FIRST SEARCH
# ---------------------------------------------------------
def bfs_solve(maze, start, goal):
    """
    Solve the maze using Breadth-First Search (BFS).

    BFS explores the maze level by level.
    In an unweighted grid maze like this one,
    BFS guarantees the shortest path in terms of steps.

    Parameters:
    - maze: 2D list
    - start: starting cell (row, col)
    - goal: target cell (row, col)

    Returns:
    - path: final shortest path as a list of cells
    - explored: all nodes visited during the search
    """
    # Queue for BFS frontier
    queue = deque([start])

    # Track visited cells so we do not repeat work
    visited = {start}

    # Track where each node came from for path reconstruction
    came_from = {}

    # Store all explored nodes for visualization
    explored = []

    while queue:
        # Remove the first inserted node
        current = queue.popleft()

        # Record this node as explored
        explored.append(current)

        # If goal found, rebuild and return path
        if current == goal:
            return reconstruct_path(came_from, start, goal), explored

        # Visit each valid neighbor
        for neighbor in get_neighbors(current, maze):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

    # No path found
    return [], explored


# ---------------------------------------------------------
# A* SEARCH
# ---------------------------------------------------------
def heuristic(a, b):
    """
    Manhattan distance heuristic.

    This estimates how far one cell is from another
    in a grid where movement is only:
    - up
    - down
    - left
    - right

    Formula:
    |row1 - row2| + |col1 - col2|

    Parameters:
    - a: cell (row, col)
    - b: cell (row, col)

    Returns:
    - estimated distance as an integer
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star_solve(maze, start, goal):
    """
    Solve the maze using A* Search.

    A* is an informed search algorithm.
    It combines:
    - the actual cost from start to current node (g-score)
    - the estimated cost from current node to goal (heuristic)

    Priority = g_score + heuristic

    This makes A* usually more efficient than BFS
    because it searches in a more goal-directed way.

    Parameters:
    - maze: 2D list
    - start: starting cell (row, col)
    - goal: target cell (row, col)

    Returns:
    - path: final best path as a list of cells
    - explored: all nodes visited during the search
    """
    # Priority queue (min-heap)
    # Each item = (priority, node)
    open_set = []
    heapq.heappush(open_set, (0, start))

    # Track how we reached each node
    came_from = {}

    # Cost from start to each node
    g_score = {start: 0}

    # Keep a record of visited nodes
    visited = set()

    # Store all explored nodes for visualization
    explored = []

    while open_set:
        # Get the node with the lowest priority
        _, current = heapq.heappop(open_set)

        # Skip if already processed
        if current in visited:
            continue

        visited.add(current)
        explored.append(current)

        # Goal reached
        if current == goal:
            return reconstruct_path(came_from, start, goal), explored

        # Check neighbors
        for neighbor in get_neighbors(current, maze):
            # Cost to move from current to neighbor
            tentative_g = g_score[current] + 1

            # If this path is better, update records
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                # Priority = actual cost so far + estimated remaining cost
                priority = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (priority, neighbor))

    # No path found
    return [], explored