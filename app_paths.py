import os
import shutil
import sys
import tempfile

APP_NAME = "MazeverseAI"


def _project_root():
    return os.path.dirname(os.path.abspath(__file__))


def get_bundle_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return _project_root()


def get_asset_path(relative_path):
    normalized = relative_path.replace("/", os.sep).replace("\\", os.sep)
    return os.path.join(get_bundle_dir(), normalized)


def resolve_existing_path(path):
    if not path:
        return path
    if os.path.isabs(path) and os.path.exists(path):
        return path
    if os.path.exists(path):
        return path

    bundled = get_asset_path(path)
    if os.path.exists(bundled):
        return bundled
    return path


def get_data_dir():
    candidates = [
        os.getenv("APPDATA"),
        os.getenv("LOCALAPPDATA"),
        os.path.expanduser("~"),
        tempfile.gettempdir(),
    ]

    for base_dir in candidates:
        if not base_dir:
            continue
        data_dir = os.path.join(base_dir, APP_NAME)
        try:
            os.makedirs(data_dir, exist_ok=True)
            return data_dir
        except OSError:
            continue

    fallback = os.path.join(_project_root(), ".user-data")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def get_data_file(*parts):
    path = os.path.join(get_data_dir(), *parts)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def get_user_audio_dir():
    return get_data_file("CustomAudio")


def get_user_sound_dir():
    return get_data_file("CustomAudio", "sounds")


def get_user_music_dir():
    return get_data_file("CustomAudio", "music")


def ensure_user_audio_readme():
    readme_path = get_data_file("CustomAudio", "README.txt")
    if os.path.exists(readme_path):
        return readme_path

    content = """Mazeverse AI Custom Audio

You can add your own music and sound files here.

Folders:
- sounds
- music

Supported sound override filenames:
- sounds\\move.wav
- sounds\\win.wav
- sounds\\click.wav
- sounds\\wall_hit.wav
- sounds\\trap_hit.wav
- sounds\\powerup.wav

You can also use .mp3 or .ogg for these names.

Music override examples:
- music\\menu_theme_1.mp3
- music\\menu_theme_2.mp3
- music\\bg_music.mp3
- music\\game_easy.mp3
- music\\game_medium.mp3
- music\\game_hard.mp3

The game checks custom files first, then falls back to built-in audio.
"""

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    return readme_path


def migrate_legacy_file(relative_path):
    legacy_path = os.path.join(_project_root(), relative_path)
    target_path = get_data_file(*relative_path.split("/"))

    if os.path.exists(target_path) or not os.path.exists(legacy_path):
        return target_path

    try:
        shutil.copy2(legacy_path, target_path)
    except OSError:
        return target_path

    return target_path
