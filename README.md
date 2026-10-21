# TouchBridge Universal
> **Universal Android Keyboard & Mouse Mapping Bridge for Windows PC**

TouchBridge Universal is a real-time, low-latency, game-independent input bridge that allows you to play Android games on your physical Android phone using a keyboard and mouse on Windows 10/11 through USB/ADB.

---

## ⚡ Key Highlights & Architecture

- **Sub-3ms Input Latency:** Directly communicates with scrcpy's binary control socket (`INJECT_TOUCH_EVENT`), bypassing the heavy process-spawn overhead of `adb shell input`.
- **True Multi-Touch Pipeline:** Up to 10 simultaneous independent touch pointers. Hold WASD for continuous 360° joystick movement while pressing Space (jump), Left Click (fire), Right Click (ADS scope), and moving the mouse (camera aim) without touch drops or key-state corruption.
- **Universal & Game-Agnostic:** Not restricted to any single title. Create, edit, duplicate, import, and export profiles for Battle Royale (Free Fire, PUBG Mobile, Call of Duty: Mobile), MOBAs (Mobile Legends, Brawl Stars), Action RPGs (Genshin Impact), and Arcade Racing games.
- **Xiaomi / Redmi / POCO Specialized Diagnostic:** Built-in guidance for MIUI/HyperOS "USB debugging (Security settings)" requirements.
- **Fail-Safe Safety Supervisor:** Press **F12** or **Escape** anytime for instantaneous emergency release of all touch contacts. Automatic contact release on window focus loss or USB cable disconnection.
- **Companion Android App & Diagnostic Suite:** Runs on the phone with a live multi-touch visualizer, frequency meter, Xiaomi setup wizard, and in-game HUD overlay calibrator.

---

## 🚀 Quick Start Guide

### 1. Requirements
- **Windows PC:** Windows 10 or 11 (64-bit).
- **Python:** 3.10+ (Python 3.11/3.12 recommended).
- **scrcpy:** [scrcpy v2.0+](https://github.com/Genymobile/scrcpy) installed or placed in `C:\scrcpy`.
- **Android Device:** Android 9.0 to 15.0 with USB Debugging enabled.

### 2. On Your Android Phone
1. Enable **Developer Options** (Settings > About Phone > Tap *Build Number* 7 times).
2. Enable **USB Debugging** (Settings > Developer Options > USB Debugging).
3. **Xiaomi/Redmi/POCO Users:** Also enable **USB debugging (Security settings)**.
4. Launch the **TouchBridge** Android app on your phone.

### 3. On Your Windows PC
Install dependencies:
```cmd
cd desktop
pip install -r requirements.txt
```

Launch TouchBridge Desktop:
```cmd
run_desktop.bat
```
*(Or on Linux/Mac: `./run_desktop.sh`)*

---

## 🎮 Default Game Profiles Included

1. **Generic Mobile FPS (`profiles/generic_fps.json`):**
   - Movement: `W`, `A`, `S`, `D` (Analog Joystick)
   - Aiming: Mouse Movement (Relative mouse-look zone)
   - Primary Fire: `Left Mouse Button`
   - Scope / ADS: `Right Mouse Button` (Toggle)
   - Jump: `Space`
   - Crouch: `C`
   - Sprint: `Shift`
   - Reload: `R`

2. **Battle Royale Shooter (`profiles/battle_royale_shooter.json`):**
   - Includes standard FPS controls + Interact (`F`), Backpack (`Tab`), Medkit (`4`), Grenade (`G`).

3. **Generic Mobile MOBA (`profiles/generic_moba.json`):**
   - Movement: `W`, `A`, `S`, `D`
   - Basic Attack: `Space` or `Left Click`
   - Skill 1: `Q`, Skill 2: `E`, Ultimate: `R`
   - Battle Spell: `F`, Recall: `B`

4. **Arcade Racing (`profiles/racing_arcade.json`):**
   - Steer Left: `A`, Steer Right: `D`
   - Nitro: `Space`, Drift/Brake: `Shift`

---

## 🛠️ Project File Tree

```
touchbridge/
├── desktop/                         # Windows Desktop Application
│   ├── touchbridge/
│   │   ├── core/                   # Input pipeline, profiles, models, failsafe
│   │   ├── transport/              # Scrcpy binary socket, companion TCP, fallback
│   │   ├── adb/                    # ADB device detection, scrcpy process manager
│   │   └── gui/                    # PySide6 Dashboard, live keymap editor, HUD
│   ├── profiles/                   # Bundled game-agnostic profiles (JSON)
│   ├── tests/                      # Automated unit test suite (15 tests)
│   ├── requirements.txt            # Python dependencies
│   ├── pyproject.toml              # Packaging metadata
│   ├── run_desktop.bat             # Windows launcher batch script
│   └── run_desktop.sh              # Unix launcher script
├── app/                            # Android Companion & Diagnostic Suite (Kotlin)
│   ├── src/main/java/com/example/
│   │   ├── MainActivity.kt         # M3 Compose UI & Tabs
│   │   ├── server/                 # Coroutine TCP Server (port 28200)
│   │   ├── model/                  # Data classes & metrics
│   │   └── ui/screens/             # Dashboard, Multi-Touch Canvas, Xiaomi Guide, HUD
│   └── src/test/                   # Android Robolectric tests
├── FEASIBILITY.md                  # Comprehensive feasibility investigation
├── ARCHITECTURE.md                 # System architecture and scrcpy packet spec
├── COMPATIBILITY.md                # Device matrix and anti-cheat guidelines
├── TESTING.md                      # Test instructions and hardware checklist
└── TROUBLESHOOTING.md              # Troubleshooting guide
```

---

## 🧪 Running Automated Tests

### Python Desktop Test Suite:
```bash
PYTHONPATH=desktop python3 -m unittest discover -s desktop/tests -v
```

### Android Companion Robolectric Test Suite:
```bash
gradle :app:testDebugUnitTest
```
