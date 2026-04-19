# Mazeverse AI

Mazeverse AI is a Python + Pygame desktop maze game that combines procedural maze generation, pathfinding, adaptive assistance, replay tracking, and a player-versus-AI race mode.

## Overview

The project goes beyond a basic maze game. It generates new mazes, solves them with BFS and A*, tracks how the player performs, and lets the user choose between a normal solo experience and a competitive AI rival mode.

## Main Features

- Procedural maze generation with scaling challenge
- `Solo` and `VS AI` game modes
- Mobile Race mode with QR-code phone joining, maze completion, and a short quiz for the final score
- BFS and A* pathfinding
- Rival ghost AI with selectable difficulty
- Adaptive hints and player performance evaluation
- Dynamic traps, power-ups, and checkpoints
- Themed worlds with visual and gameplay variation
- Progress tracking, replay storage, heatmaps, and analytics
- Windows desktop packaging with installer support
- Custom user music and sound overrides with default fallback

## Tech Stack

- Python
- Pygame
- Flask + Flask-SocketIO
- qrcode
- PyInstaller
- Inno Setup

## Project Structure

- [main.py](main.py) contains the main game loop, rendering, states, audio, and gameplay logic
- [maze.py](maze.py) handles maze generation
- [solver.py](solver.py) contains BFS and A* pathfinding
- [ai_engine.py](ai_engine.py) handles adaptive player analysis
- [game_features.py](game_features.py) manages traps, power-ups, and checkpoints
- [progress_manager.py](progress_manager.py), [score_manager.py](score_manager.py), and [advanced_tracking.py](advanced_tracking.py) manage saved progress and analytics
- [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) contains the full project documentation

## Run Locally

1. Install Python 3.11+.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Run the game:

```powershell
python main.py
```

## Build the Desktop App

- PyInstaller spec: [MazeverseAI.spec](MazeverseAI.spec)
- Windows build script: [build_windows.ps1](build_windows.ps1)
- Inno Setup installer script: [installer.iss](installer.iss)
- Build guide: [DESKTOP_BUILD.md](DESKTOP_BUILD.md)

## Saved Data

The game stores progress, best scores, replays, and analytics as per-user data, so a fresh install on a new computer starts from the beginning unless save files are copied manually.

## Repository Notes

- Source code and assets belong in the repo
- Built output folders like `build/`, `dist/`, and `installer-dist/` are ignored
- Installer files are better shared through GitHub Releases instead of committing them into the repo

## Authors

- CJ (Munotida Madanhire)
- Paradise (Rutendo Gandi)
