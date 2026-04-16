**Desktop Build**

This project is ready to package as a Windows desktop game.

**What changed**

- Save data now goes to `%APPDATA%\MazeverseAI`
- A new laptop or new Windows user starts with fresh progress automatically
- Existing local JSON save files are copied into app data on first run on the current machine

**Build EXE**

1. Install PyInstaller:
```powershell
python -m pip install pyinstaller
```
2. Build the app:
```powershell
.\build_windows.ps1
```
3. The desktop build will be created in:
```text
dist\MazeverseAI
```

**Create Installer**

1. Install Inno Setup
2. Open `installer.iss`
3. Build it in Inno Setup
4. The installer will be created in:
```text
installer-dist
```

**Fresh installs**

- Installs do not bundle your current `progress.json`, `best_scores.json`, or analytics data
- Progress is stored per user in `%APPDATA%\MazeverseAI`
- A different laptop starts from zero unless you manually copy that app-data folder
