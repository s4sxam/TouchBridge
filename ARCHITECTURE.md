# TouchBridge Universal — System Architecture

**Document Version:** 1.0.0  
**Authors:** Senior Desktop & Low-Latency Input Systems Engineering Team  

---

## 1. High-Level System Architecture

TouchBridge Universal is composed of two primary subsystems:
1. **Host Subsystem (Windows 10/11 Desktop):**
   - High-FPS asynchronous user interface built with PySide6 (Qt for Python).
   - Low-latency Keyboard & Mouse capture engine operating at raw input polling rates (up to 1000Hz).
   - Virtual Control State Machine converting discrete key presses and relative mouse movements into normalized touch contact actions.
   - Dual-channel Transport layer (scrcpy binary control socket & Companion TCP socket).
   - Failsafe Safety Supervisor ensuring zero stuck touches under any condition (focus loss, window close, connection drop, emergency hotkey).

2. **Client Subsystem (Android 9.0–15.0 Companion & Display Device):**
   - Live Multi-Touch Visualizer and Contact State Inspector.
   - Screen coordinate, DPI, aspect ratio, and refresh rate calibrator.
   - Xiaomi / Redmi MIUI & HyperOS security permission diagnostic helper.
   - Embedded high-throughput TCP receiver on port 28200 (`TouchBridgeServer`).
   - Floating keymap calibration HUD overlay for in-game alignment.

---

## 2. Input Pipeline & Data Flow

```
+---------------------------------------------------------------------------------+
|                                WINDOWS HOST                                     |
|                                                                                 |
|  [Physical Keyboard & Mouse]                                                    |
|           |                                                                     |
|           v                                                                     |
|  [Low-Latency Input Hook / Listener]                                            |
|           |                                                                     |
|           v                                                                     |
|  [Input Pipeline State Machine]                                                 |
|     - Key De-duplication (filter OS repeat events)                              |
|     - WASD Vector Composer (Normalized X/Y direction calculation)              |
|     - Mouse-Look Relative Delta Integrator with Micro-Flick Boundary Reset     |
|     - Contact ID Pool Manager (Allocates IDs 0..9, guarantees release)          |
|           |                                                                     |
|           +-----------------------------------+                                 |
|           |                                   |                                 |
|           v (Primary Channel)                 v (Secondary Channel)             |
|  [scrcpy Control Transport]          [Companion TCP Transport]                  |
|     Binary Packet Protocol (32B)       JSON / Binary Packet Stream              |
|     Port 27183 / Local Pipe            Port 28200 (ADB Forward)                 |
+-----------+-----------------------------------+---------------------------------+
            |                                   |
            | USB 3.0 / USB 2.0 (ADB Tunnel)    |
            v                                   v
+---------------------------------------------------------------------------------+
|                                ANDROID DEVICE                                   |
|                                                                                 |
|  [scrcpy-server.jar]                 [TouchBridge Companion Server]             |
|  (UID 2000 Shell Injector)           (Foreground Companion Service)             |
|           |                                   |                                 |
|           +-----------------+-----------------+                                 |
|                             |                                                   |
|                             v                                                   |
|             [Android InputManager / WindowManager]                              |
|                             |                                                   |
|                             v                                                   |
|                     [Active Game App]                                           |
|       (Free Fire, PUBG Mobile, Call of Duty, Genshin, etc.)                     |
+---------------------------------------------------------------------------------+
```

---

## 3. Scrcpy Binary Control Packet Specification

When communicating over the scrcpy control socket, TouchBridge serializes touch events using the exact scrcpy binary protocol (`INJECT_TOUCH_EVENT`):

| Offset (Bytes) | Field Type | Name | Description |
| :--- | :--- | :--- | :--- |
| `0x00` (1B) | `uint8` | `type` | Constant `0x02` (`INJECT_TOUCH_EVENT`) |
| `0x01` (1B) | `uint8` | `action` | `0` = DOWN, `1` = UP, `2` = MOVE |
| `0x02` (8B) | `uint64_be` | `pointer_id` | Identifier for the touch contact (`0` to `9`) |
| `0x0A` (4B) | `int32_be` | `x` | Screen X coordinate in physical device pixels |
| `0x0E` (4B) | `int32_be` | `y` | Screen Y coordinate in physical device pixels |
| `0x12` (2B) | `uint16_be` | `screen_width` | Screen width in physical pixels (e.g., `2400`) |
| `0x14` (2B) | `uint16_be` | `screen_height`| Screen height in physical pixels (e.g., `1080`) |
| `0x16` (2B) | `uint16_be` | `pressure` | Touch pressure (fixed-point `0x0000` to `0xFFFF`, typically `0xFFFF`) |
| `0x18` (4B) | `uint32_be` | `action_button`| Button mask (`1` for primary touch) |
| `0x1C` (4B) | `uint32_be` | `buttons` | Active buttons bitmask |

Total packet size: **32 bytes**. Transmission time over USB 2.0/3.0 is **under 0.2 milliseconds**.

---

## 4. Virtual Control Types & State Handling

### 4.1 Tap Control (e.g., Jump, Reload, Crouch)
- **Key Down:** Assign pointer ID from pool (e.g., ID 2). Send `DOWN(x, y, id)`.
- **Key Up:** Send `UP(x, y, id)`. Return pointer ID to pool.
- **Repeat Keys:** If the OS emits auto-repeat key-down events while held, the state machine drops them. Only initial key-down and physical key-up trigger events.

### 4.2 Joystick Control (WASD)
- Continuous contact with dedicated pointer ID (ID 0).
- State tracked as bitflags: `UP (W)`, `DOWN (S)`, `LEFT (A)`, `RIGHT (D)`.
- When any movement key is pressed:
  - If no movement keys were previously active: Send `DOWN(x, y, ID_0)`.
  - While keys change (e.g., player transitions from `W` to `W+D`): Emits `MOVE(new_x, new_y, ID_0)` at 60Hz/120Hz tick interval.
- When all 4 movement keys are released: Emits `UP(center_x, center_y, ID_0)` and releases ID 0.

### 4.3 Mouse-Look Relative Aiming Zone
- Dedicated pointer ID (ID 1).
- Active touch is maintained inside a defined right-screen bounding box (e.g., normalized `[0.55, 0.20]` to `[0.95, 0.85]`).
- As the player moves the mouse:
  - $\Delta x, \Delta y$ are scaled by sensitivity and DPI factors.
  - New target position: $X = X + \Delta x$, $Y = Y + \Delta y$.
  - Emits `MOVE(X, Y, ID_1)`.
  - **Flick Boundary Guard:** If $(X, Y)$ crosses 85% of the zone radius, an instantaneous reset is performed:
    1. Send `UP(X, Y, ID_1)`.
    2. Reset coordinates to center of zone $(X_0, Y_0)$.
    3. Send `DOWN(X_0, Y_0, ID_1)`.
    4. Duration is < 2ms, virtually imperceptible in-game.

### 4.4 Hold & Toggle Controls
- Configurable per binding in the profile.
- Tap to toggle (e.g., toggle ADS scope) or hold-to-activate (e.g., hold right mouse button to aim).

---

## 5. Failsafe & Emergency Release Engine

Stuck touches ruin gameplay and can lock up an Android device until rebooted. TouchBridge implements a four-tiered failsafe supervisor:

1. **Physical Emergency Hotkey:** Configurable (default `F12` or `Escape`). When pressed, instantly triggers `transport.release_all()` regardless of key states.
2. **Window Focus Loss:** When the scrcpy display window or TouchBridge loses operating system focus, all active contacts are immediately released via `UP` events.
3. **ADB Disconnection Monitor:** A background heartbeat thread monitors device connection. If USB is unplugged, active touch states are cleared in memory.
4. **App Shutdown Hook:** `atexit` and Qt `closeEvent` guarantee that any open contacts send `UP` packets and flush the socket before process termination.
