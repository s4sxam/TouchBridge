# TouchBridge Universal — Device & Game Compatibility Matrix

**Document Version:** 1.0.0  

---

## 1. Operating System & Firmware Compatibility

| Android Version | API Level | Status | Notes / Prerequisites |
| :--- | :--- | :--- | :--- |
| **Android 15 (Vanilla Ice Cream)** | 35 | ✅ Supported | Requires 64-bit scrcpy server. Private space must be unlocked. |
| **Android 14 (Upside Down Cake)** | 34 | ✅ Supported | Full support for scrcpy control socket and ADB forward. |
| **Android 13 (Tiramisu)** | 33 | ✅ Supported | Standard ADB authorization. |
| **Android 12 / 12L (Snow Cone)** | 31–32 | ✅ Supported | Low-latency injection supported. |
| **Android 11 (Red Velvet Cake)** | 30 | ✅ Supported | Wireless ADB and USB ADB supported. |
| **Android 10 (Queen Cake)** | 29 | ✅ Supported | Direct `/dev/input` restricted; scrcpy control socket recommended. |
| **Android 9.0 (Pie)** | 28 | ✅ Supported | Minimum supported version for scrcpy 2.x control socket. |
| **Android 8.1 & below** | <= 27 | ⚠️ Partial | Legacy ADB shell injection fallback only. |

---

## 2. Manufacturer & Skin Specific Details

### 2.1 Xiaomi / Redmi / POCO (MIUI 12, 13, 14 & Xiaomi HyperOS)
- **Status:** Fully Supported with Security Settings Configuration.
- **The Xiaomi Security Gate:**
  Xiaomi places an extra security lock in Developer Options called **"USB debugging (Security settings)"** (Simulate input via USB).
  If this toggle is OFF:
  - Video stream mirrors fine.
  - ADB commands like `getprop` and `screencap` succeed.
  - **All touch injection commands are silently dropped by MIUI!**
- **How to Enable on Xiaomi Devices:**
  1. Ensure a working SIM card is inserted into the phone.
  2. Log in to your Mi Account.
  3. Go to **Settings** > **Additional Settings** > **Developer Options**.
  4. Turn ON **USB Debugging**.
  5. Scroll down to **USB Debugging (Security settings)**.
  6. Tap through three 5-second security confirmation prompts.
  7. Optional: Enable **Don't use lock screen** and **Stay awake**.

### 2.2 Samsung Galaxy (OneUI 3, 4, 5, 6)
- **Status:** Flawless out-of-the-box.
- Enable **USB Debugging** in Developer options.
- Disable **Game Booster** touch protection overlay if it interferes with edge touches.

### 2.3 Google Pixel (Stock Android 10–15)
- **Status:** Flawless reference implementation.
- Lowest input jitter recorded (< 2ms).

### 2.4 OnePlus / Oppo / Realme (OxygenOS / ColorOS)
- **Status:** Fully Supported.
- Ensure **Disable Permission Monitoring** is toggled ON if touches intermittently pause.

---

## 3. Game Compatibility Matrix

TouchBridge works on the OS display layer and is **100% game-agnostic**. Any game that accepts standard capacitive touchscreen multi-touch can be mapped.

| Game Title | Genre | Mapping Recommendation | Notes / Best Practices |
| :--- | :--- | :--- | :--- |
| **Free Fire / Free Fire MAX** | Battle Royale | Joystick + Mouse Look + Buttons | Set in-game HUD to classic layout. Adjust mouse sensitivity to 0.4. |
| **PUBG Mobile / BGMI** | Battle Royale | Joystick + Mouse Look + Micro-flick | Enable smooth look interpolation in TouchBridge. |
| **Call of Duty: Mobile** | Tactical FPS | Joystick + Mouse Look + Dedicated ADS | Supports separate Hip-fire and ADS mouse buttons. |
| **Genshin Impact** | Action RPG | WASD Movement + Skill Keybinds | Native touch layout is spacious; ideal for keymap overlay. |
| **Brawl Stars** | MOBA / Brawler | Dual Virtual Joystick | Assign left joystick to WASD, right aiming to Arrow keys or Mouse. |
| **Mobile Legends: Bang Bang** | MOBA | Left Joystick + Skill Smart Cast | Assign Q, W, E, R to skill buttons with quick-cast toggle. |
| **Asphalt 9 / Real Racing 3** | Racing | Left/Right Steer + Drift/Nitro | Steer mapped to A/D or Left/Right arrows, Space for Nitro. |

---

## 4. Anti-Cheat Risk Assessment & Guidelines

| Risk Level | Factor | Details |
| :--- | :--- | :--- |
| **🟢 Safe (No Ban Risk)** | OS Level Injection | TouchBridge uses Android's native `InputManager` through shell UID. It does not hook `libunity.so`, `libil2cpp.so`, or modify memory. |
| **🟢 Safe (No Root)** | Device Integrity | SafeNet / Play Integrity / hardware attestation pass completely unmodified. |
| **🟡 Caution (Player Behavior)** | Micro-second clicks | If you use rapid-fire macro repeaters with 0ms delay, server-side anomaly detection may flag impossible click frequency. Keep repeat interval above 35ms. |
| **🟡 Caution (Tournament Play)** | Terms of Service | In competitive esports tournaments, playing touch mobile games with keyboard and mouse may violate tournament rules. |
