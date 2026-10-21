# TouchBridge Universal — Testing Guide & Verification Checklist

**Document Version:** 1.0.0  

---

## 1. Automated Test Suite

TouchBridge provides comprehensive automated test suites for both the **Python Desktop Host** and the **Android Companion App**.

### 1.1 Running the Desktop Python Test Suite
The desktop test suite tests:
- Profile loading, validation, boundary clamping, and JSON migration.
- Input pipeline key-state tracking, WASD diagonal vector math, and key-repeat suppression.
- Simultaneous multi-touch allocation (e.g., Joystick + Space + Mouse Click = 3 concurrent pointers).
- Mouse-look relative delta integration and boundary micro-flick resets.
- Emergency stop release of all allocated contacts.
- Scrcpy binary packet serializer matching the official C scrcpy server struct layout.
- ADB device list parsing and unauthorized state detection.

**Command to run desktop tests:**
```bash
python3 -m unittest discover -s desktop/tests -v
```

### 1.2 Running Android Companion Robolectric Tests
```bash
gradle :app:testDebugUnitTest
```

---

## 2. Physical Device Testing Checklist (Windows 10/11 & Real Android Phone)

Follow this step-by-step checklist when performing end-to-end hardware verification on a physical device:

### Phase 1: ADB & Authorization Check
- [ ] Connect phone to PC via USB cable.
- [ ] Ensure USB mode is set to "File Transfer" or "MIDI" (not charge only).
- [ ] Run `adb devices`. Verify device is listed as `device` (not `unauthorized` or `offline`).
- [ ] If `unauthorized`: check phone screen and accept the RSA key prompt "Always allow from this computer".
- [ ] On Xiaomi/Redmi devices: verify "USB debugging (Security settings)" is enabled.

### Phase 2: Touch Injection Prototype Test
- [ ] Launch `TouchBridge` companion app on the Android phone.
- [ ] Switch to the **Multi-Touch & Latency Tester** tab.
- [ ] Send test command from desktop or ADB:
  ```bash
  adb shell input tap 500 500
  ```
- [ ] Verify the tap point displays on the companion app's live touch canvas with coordinate readout.

### Phase 3: Continuous Movement & Simultaneous Touches
- [ ] Start mapping with the `Generic FPS` profile.
- [ ] Hold `W` on Windows keyboard: observe Contact ID 0 active at top position of joystick.
- [ ] While holding `W`, press `D`: observe Contact ID 0 moves diagonally (45° angle) without releasing or re-tapping.
- [ ] While holding `W` and `D`, press `Space` (Jump): observe Contact ID 2 activates at the Jump button location while Contact ID 0 remains held and active.
- [ ] Release `Space`: observe Contact ID 2 releases (`ACTION_UP`) while Contact ID 0 remains steadily held.
- [ ] Release `W` and `D`: observe Contact ID 0 releases (`ACTION_UP`).

### Phase 4: Mouse-Look Aiming
- [ ] Click the mouse into the scrcpy viewport or enable mouse capture (Hotkey: `Ctrl + ~` or Middle Click).
- [ ] Move mouse horizontally left and right: observe camera rotation in-game or cursor swipe in the tester canvas.
- [ ] Verify that swiping continuously across a wide distance triggers the micro-flick reset without camera snapback.

### Phase 5: Failsafe & Emergency Stop
- [ ] Hold down movement keys so active contacts are engaged.
- [ ] Press the Emergency Stop hotkey (`F12` or `Escape`).
- [ ] Verify ALL contacts immediately transition to UP state (no stuck touches).
- [ ] Unplug the USB cable while mapping is active: verify desktop UI safely detects disconnection and transitions to disconnected state without crashing.
