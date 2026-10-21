# TouchBridge Universal — Troubleshooting Guide

Common issues, diagnosis procedures, and solutions.

---

## 1. Touches Are Not Registering in the Game

### Symptom:
The scrcpy mirror window displays the game smoothly, but pressing WASD or mouse buttons does nothing inside the game.

### Causes & Fixes:
1. **Xiaomi / Redmi / POCO Devices (Most Common):**
   - *Cause:* MIUI/HyperOS has an extra permission called **"USB debugging (Security settings)"** that blocks USB touch injection by default.
   - *Fix:*
     1. Insert a working SIM card (required by Xiaomi security).
     2. Log in to your Mi Account.
     3. Go to **Settings** > **Additional Settings** > **Developer Options**.
     4. Turn ON **USB debugging (Security settings)**. Accept the three 5-second countdown prompts.
2. **Device Unauthorized:**
   - *Check:* In TouchBridge Desktop Dashboard, verify device status is `Authorized`.
   - *Fix:* Check your phone screen for the prompt *"Allow USB debugging?"*, check *"Always allow from this computer"*, and tap **Allow**.
3. **Mapping Not Started:**
   - *Fix:* Ensure you clicked **"▶ START MAPPING"** in the Runtime Controls tab of the desktop app.

---

## 2. Stuck Touches or Continual Movement After Key Release

### Symptom:
Player character continues walking in one direction or a button stays held down.

### Fixes:
1. **Immediate Remedy:** Press **F12** or **Escape** on your Windows keyboard. This invokes the Emergency Failsafe, which transmits `ACTION_UP` packets to every pointer ID from 0 to 9.
2. **Focus Loss Guard:** If you alt-tabbed away, TouchBridge automatically releases contacts. If this fails, toggle the emergency stop button in the desktop HUD or companion app.
3. **Unplug/Replug Recovery:** If USB connection stuttered, unplugging and re-plugging the USB cable resets the Android kernel's `InputManager` contacts.

---

## 3. Mouse Aim Stutters or Snaps Back to Center

### Symptom:
When looking around in a 3D shooter, the camera rotates and then snaps back.

### Fixes:
1. **Boundary Micro-Flick Sensitivity:**
   - In the Profile Manager, increase the **Mouse Look Zone** width and height to 0.45 and 0.65.
   - Lower your Windows mouse DPI or decrease TouchBridge mouse sensitivity to `0.7` to `1.0`.
2. **Scrcpy Window Scale:**
   - Ensure the reference resolution in the profile matches your device's physical aspect ratio (e.g. 2400x1080).

---

## 4. `adb devices` Shows Device as "Offline"

### Fixes:
1. Restart ADB server:
   ```cmd
   adb kill-server
   adb start-server
   ```
2. Unplug and reconnect USB cable, preferably into a motherboard USB 3.0 port (avoid unpowered USB hubs).
3. Change USB configuration on phone from "Charging only" to "File Transfer (MTP)" or "MIDI".
