# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HOMER Training System is a full-screen kiosk application built with Python/tkinter that serves as a launcher for rehabilitation training games (Pluto and Mars). It manages authentication, device expiry validation, demo/training game selection, and system lifecycle.

## Common Commands

### Development
- **Run the app**: `python launcher.py`
  - Starts the application in fullscreen mode with kiosk-like behavior
  - Used for local testing and development

### Building
- **Build executable**: `pyinstaller launcher.spec`
  - Creates a standalone .exe in the `dist/` directory
  - Bundles all PNG assets and dependencies
  - Produces `dist/launcher.exe` ready for deployment

### Running Built Version
- **Run as .exe**: `dist/launcher.exe` (after building)
  - Runs the compiled standalone executable
  - For end-user distribution and production deployment

### Debug
- Add `print()` statements to see debug output in console
- The app logs authentication and game state to stdout with `[DEBUG]` prefix
- Use `Shift+Escape` to exit the full-screen kiosk mode (hidden exit key)

## Architecture

### Application Flow

The launcher follows a state machine pattern with these main screens:

1. **Animation Screen** - HOMER title animation with letter-by-letter typing and growth effect
2. **Authentication Screen** - Password dialog (only shown once, cached to disk)
3. **Demo Games Screen** - Pluto and Mars demo games (skipped if both already completed)
4. **Training Games Screen** - Select Pluto or Mars for actual training
5. **Completion Screen** - Shows when both training programs are finished, triggers system shutdown

### Key Modules & Components

**Password & Config Management** (`get_password`, `save_password`, `ask_password`)
- Reads/writes password from `C:\DeviceSetups\config.ini` for persistent authentication
- First run shows password dialog; subsequent runs skip if cached
- Password hardcoded as "BIOREHAB" for validation

**Device Expiry Validation** (`is_training_completed`)
- Validates training is not expired before launching games
- Reads device setup file: `C:\DeviceSetups\{Device}\uploadStatus.txt`
- Extracts project path and checks `data/configdata.csv` for EndDate
- Supports multiple date formats (YYYY-MM-DD, DD-MM-YYYY, with/without time)
- Returns `False` (expired) if: file missing, path invalid, date in past, or parse error
- See `EXPIRY_VALIDATION.md` for detailed validation logic

**Demo Game Tracking** (`is_demo_completed`)
- Checks for flag files: `C:\DeviceSetups\{Mars,Pluto}\{mars,pluto}_demo_done.txt`
- When both demos have flag files, skips demo screen and goes straight to training/auth

**Game Launch** (`launch_game`)
- Spawns game executable via `subprocess.Popen`
- For **demo games**: waits for process exit, checks if both demos complete, returns to demo screen or advances
- For **training games**: closes launcher immediately after spawning (player closes game when done)
- Uses threading to prevent UI blocking while waiting for game to close

**UI Components**
- **Colors**: Dark theme with accent colors (Pluto: `#2bd887` green, Mars: `#ff8e55` orange)
- **Images**: Mars.png, Pluto.png, marsBg.png, plutoBg.png bundled with `launcher.spec`
- **Hover Effects**: Cards expand border on hover, buttons highlight on interaction
- **Animations**: Letter-by-letter typing with font growth using cubic easing

### Critical File Paths (Hardcoded)

**Configuration:**
- Config: `C:\DeviceSetups\config.ini` (password storage)

**Device Setup:**
- Mars: `C:\DeviceSetups\Mars\uploadStatus.txt`
- Pluto: `C:\DeviceSetups\Pluto\uploadStatus.txt`
- Both reference a project path → `data/configdata.csv` with EndDate

**Game Executables:**
- Demo Pluto: `C:\HOMER_DEMO_PLUTO\PLUTO.exe`
- Demo Mars: `C:\HOMER_DEMO_MARS\MARS.exe`
- Training Pluto: `C:\HOMER_PLUTO\PLUTO.exe`
- Training Mars: `C:\HOMER_MARS\MARS.exe`

**Demo Completion Flags:**
- Mars: `C:\DeviceSetups\Mars\mars_demo_done.txt`
- Pluto: `C:\DeviceSetups\Pluto\pluto_demo_done.txt`

### PyInstaller Integration

The `resource_path()` function handles asset loading for both `.py` and `.exe` modes:
- In development: loads PNG files from current directory
- When built as .exe: loads from bundled resources via `sys._MEIPASS`
- `launcher.spec` includes all PNG files in `datas` list

### System Lifecycle

**Shutdown Trigger:**
- When both training programs are completed (based on EndDate), completion screen shows
- Manual shutdown via "⏻ Shutdown" button calls `shutdown_system()`
- Can auto-trigger with `shutdown_system(delay=N)` for timed shutdown
- Uses `os.system("shutdown /s /t 0")` to shutdown the device

**Kiosk Mode:**
- Full-screen fullscreen mode: `root.attributes("-fullscreen", True)`
- Disables window controls (minimize, maximize, close)
- Intercepts window close: `root.protocol("WM_DELETE_WINDOW", lambda: None)` blocks normal close
- Only way out: Shift+Escape exit key or game completion → shutdown

## Dependencies

```
tkinter          (Python stdlib - GUI framework)
PIL / Pillow     (image handling)
subprocess       (Python stdlib - game launching)
os, sys, datetime (Python stdlib)
PyInstaller      (build tool)
```

## State Management

Key variables tracking application state:
- `mars_completed` / `pluto_completed` - computed from `is_training_completed()` at startup
- `result[0]` - password dialog result (closed scope variable)
- `anim_state` - animation frame/letter tracking during title animation
- `process` - subprocess handle for running game

## Testing Notes

**To test password functionality:**
- Delete `C:\DeviceSetups\config.ini` to force password prompt on next run
- Correct password is "BIOREHAB"

**To test demo games:**
- Delete demo flag files to show demo screen
- Verify flag files are written by games to `C:\DeviceSetups\{Device}/{mars,pluto}_demo_done.txt`

**To test device expiry:**
- Modify configdata.csv EndDate to past date to block training games
- Verify error message "Project expired. Contact support." appears

**To test kiosk exit:**
- Press Shift+Escape to exit full-screen mode (hidden for end-users)

## Build & Distribution

After modifying `launcher.py`:
1. Test locally with `python launcher.py`
2. Build: `pyinstaller launcher.spec`
3. Verify `dist/launcher.exe` exists
4. Test the .exe before distribution
5. The .exe is self-contained and can run on any Windows machine with the required paths/files

## Notes

- The app runs in full-screen kiosk mode to prevent unauthorized access or navigation
- All external game paths are absolute (not relative) as they point to separate installations
- Date parsing is defensive—any unrecognized format blocks game launch (fail-safe expiry check)
- Threading is used only for demo game exit waiting to keep UI responsive
- Password is cached to disk; delete config file to reset authentication
