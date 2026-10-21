"""TouchBridge Low-Latency Input Pipeline.

Translates physical keyboard and mouse events into multi-touch gestures on Android.
Handles de-duplication, simultaneous key combos, continuous joystick math,
mouse-look aiming, and contact pool allocation.
"""

from __future__ import annotations
import logging
import math
import threading
from typing import Dict, Optional, Set, Tuple

from .models import Binding, ControlType, Profile
from ..transport.base import InputTransport

logger = logging.getLogger("touchbridge.input_pipeline")

# Reserved Pointer IDs
JOYSTICK_POINTER_ID = 0
MOUSE_LOOK_POINTER_ID = 1
MIN_DYNAMIC_POINTER_ID = 2
MAX_DYNAMIC_POINTER_ID = 9


class InputPipeline:
    """Core state machine managing keyboard, mouse, and touch contact streams."""

    def __init__(self, transport: InputTransport, profile: Profile):
        self.transport = transport
        self.profile = profile
        self.lock = threading.Lock()

        # Keyboard & Mouse state tracking
        self.held_keys: Set[str] = set()
        self.held_mouse_buttons: Set[str] = set()

        # Allocation pool for dynamic touch pointers (IDs 2..9)
        self.available_pointers: list[int] = list(range(MIN_DYNAMIC_POINTER_ID, MAX_DYNAMIC_POINTER_ID + 1))
        self.binding_pointer_map: Dict[str, int] = {}  # binding.id -> pointer_id

        # Joystick State
        self.joystick_binding: Optional[Binding] = None
        self.joystick_active: bool = False
        self.joystick_keys: Dict[str, bool] = {"up": False, "down": False, "left": False, "right": False}

        # Mouse Look State
        self.mouse_look_binding: Optional[Binding] = None
        self.mouse_look_active: bool = False
        self.mouse_look_pos: Tuple[int, int] = (0, 0)
        self.mouse_look_center: Tuple[int, int] = (0, 0)
        self.mouse_look_bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)  # min_x, min_y, max_x, max_y

        # Toggle bindings state
        self.toggle_states: Dict[str, bool] = {}  # binding.id -> is_toggled_on

        # Active mapping flag
        self.is_running: bool = False

        self._configure_profile(profile)

    def _configure_profile(self, profile: Profile) -> None:
        """Parse bindings from active profile."""
        self.profile = profile
        self.transport.update_screen_size(profile.ref_width, profile.ref_height)
        self.joystick_binding = None
        self.mouse_look_binding = None

        for b in profile.bindings:
            if b.control_type == ControlType.JOYSTICK and not self.joystick_binding:
                self.joystick_binding = b
            elif b.control_type == ControlType.MOUSE_LOOK and not self.mouse_look_binding:
                self.mouse_look_binding = b
                # Compute pixel bounds for mouse look zone
                cx = int(b.norm_x * self.profile.ref_width)
                cy = int(b.norm_y * self.profile.ref_height)
                hw = int((b.zone_width * self.profile.ref_width) / 2)
                hh = int((b.zone_height * self.profile.ref_height) / 2)
                self.mouse_look_center = (cx, cy)
                self.mouse_look_pos = (cx, cy)
                self.mouse_look_bounds = (cx - hw, cy - hh, cx + hw, cy + hh)

    def start(self) -> None:
        """Start accepting and routing input events."""
        with self.lock:
            self.is_running = True
            logger.info("Input pipeline started for profile: %s", self.profile.name)

    def stop(self) -> None:
        """Stop routing input and release all contacts."""
        with self.lock:
            self.is_running = False
            self._release_all_internal()
            logger.info("Input pipeline stopped")

    def _release_all_internal(self) -> None:
        """Release all internal states and active pointers."""
        self.held_keys.clear()
        self.held_mouse_buttons.clear()
        self.available_pointers = list(range(MIN_DYNAMIC_POINTER_ID, MAX_DYNAMIC_POINTER_ID + 1))
        self.binding_pointer_map.clear()
        self.joystick_active = False
        self.joystick_keys = {"up": False, "down": False, "left": False, "right": False}
        self.mouse_look_active = False
        self.toggle_states.clear()
        self.transport.release_all()

    def emergency_release(self) -> None:
        """Emergency failsafe invocation."""
        with self.lock:
            self._release_all_internal()

    # -------------------------------------------------------------------------
    # Physical Key Event Handlers
    # -------------------------------------------------------------------------

    def on_key_down(self, key_name: str) -> None:
        """Handle physical key press."""
        norm_key = key_name.lower().strip()
        with self.lock:
            if not self.is_running:
                return

            # Check emergency stop hotkey
            if norm_key == self.profile.emergency_stop_key.lower():
                logger.warning("Emergency stop key pressed: %s", norm_key)
                self._release_all_internal()
                return

            # Ignore OS auto-repeat for already held keys
            if norm_key in self.held_keys:
                return
            self.held_keys.add(norm_key)

            # Check Joystick
            if self.joystick_binding and self._is_joystick_key(norm_key):
                self._update_joystick_state(norm_key, pressed=True)
                return

            # Check Tap / Hold / Toggle bindings
            for b in self.profile.bindings:
                if b.key and b.key.lower() == norm_key:
                    self._handle_binding_down(b)

    def on_key_up(self, key_name: str) -> None:
        """Handle physical key release."""
        norm_key = key_name.lower().strip()
        with self.lock:
            if not self.is_running:
                return

            if norm_key not in self.held_keys:
                return
            self.held_keys.remove(norm_key)

            # Check Joystick
            if self.joystick_binding and self._is_joystick_key(norm_key):
                self._update_joystick_state(norm_key, pressed=False)
                return

            # Check Tap / Hold / Toggle bindings
            for b in self.profile.bindings:
                if b.key and b.key.lower() == norm_key:
                    self._handle_binding_up(b)

    # -------------------------------------------------------------------------
    # Physical Mouse Event Handlers
    # -------------------------------------------------------------------------

    def on_mouse_down(self, button_name: str) -> None:
        """Handle physical mouse click down (left, right, middle)."""
        btn = button_name.lower().strip()
        with self.lock:
            if not self.is_running:
                return

            if btn in self.held_mouse_buttons:
                return
            self.held_mouse_buttons.add(btn)

            for b in self.profile.bindings:
                if b.mouse_button and b.mouse_button.lower() == btn:
                    self._handle_binding_down(b)

    def on_mouse_up(self, button_name: str) -> None:
        """Handle physical mouse click release."""
        btn = button_name.lower().strip()
        with self.lock:
            if not self.is_running:
                return

            if btn not in self.held_mouse_buttons:
                return
            self.held_mouse_buttons.remove(btn)

            for b in self.profile.bindings:
                if b.mouse_button and b.mouse_button.lower() == btn:
                    self._handle_binding_up(b)

    def on_mouse_move(self, dx: float, dy: float) -> None:
        """Handle relative mouse movement for camera aiming."""
        with self.lock:
            if not self.is_running or not self.mouse_look_binding:
                return

            if abs(dx) < 0.001 and abs(dy) < 0.001:
                return

            b = self.mouse_look_binding
            scaled_dx = int(dx * b.sensitivity_x * self.profile.mouse_sensitivity)
            scaled_dy = int(dy * b.sensitivity_y * self.profile.mouse_sensitivity)

            min_x, min_y, max_x, max_y = self.mouse_look_bounds
            cx, cy = self.mouse_look_center
            curr_x, curr_y = self.mouse_look_pos

            new_x = curr_x + scaled_dx
            new_y = curr_y + scaled_dy

            # Check if contact is near the boundary -> Micro-Flick Reset
            margin_x = int((max_x - min_x) * 0.15)
            margin_y = int((max_y - min_y) * 0.15)

            if new_x < min_x + margin_x or new_x > max_x - margin_x or new_y < min_y + margin_y or new_y > max_y - margin_y:
                # Boundary reached: instant reset
                if self.mouse_look_active:
                    self.transport.touch_up(MOUSE_LOOK_POINTER_ID, curr_x, curr_y)
                self.mouse_look_pos = (cx, cy)
                self.transport.touch_down(MOUSE_LOOK_POINTER_ID, cx, cy)
                self.mouse_look_active = True
                return

            # Standard move
            self.mouse_look_pos = (new_x, new_y)
            if not self.mouse_look_active:
                self.transport.touch_down(MOUSE_LOOK_POINTER_ID, new_x, new_y)
                self.mouse_look_active = True
            else:
                self.transport.touch_move(MOUSE_LOOK_POINTER_ID, new_x, new_y)

    # -------------------------------------------------------------------------
    # Joystick Vector Calculation
    # -------------------------------------------------------------------------

    def _is_joystick_key(self, key: str) -> bool:
        if not self.joystick_binding:
            return False
        b = self.joystick_binding
        return key in (b.up_key.lower(), b.down_key.lower(), b.left_key.lower(), b.right_key.lower())

    def _update_joystick_state(self, key: str, pressed: bool) -> None:
        b = self.joystick_binding
        if not b:
            return

        if key == b.up_key.lower():
            self.joystick_keys["up"] = pressed
        elif key == b.down_key.lower():
            self.joystick_keys["down"] = pressed
        elif key == b.left_key.lower():
            self.joystick_keys["left"] = pressed
        elif key == b.right_key.lower():
            self.joystick_keys["right"] = pressed

        # Calculate directional vector (vx, vy)
        vx = 0.0
        vy = 0.0

        if self.joystick_keys["up"]:
            vy -= 1.0
        if self.joystick_keys["down"]:
            vy += 1.0
        if self.joystick_keys["left"]:
            vx -= 1.0
        if self.joystick_keys["right"]:
            vx += 1.0

        cx = int(b.norm_x * self.profile.ref_width)
        cy = int(b.norm_y * self.profile.ref_height)
        radius = int(b.radius * self.profile.ref_height)

        is_moving = (vx != 0.0 or vy != 0.0)

        if is_moving:
            # Normalize diagonal movement so speed is consistent
            magnitude = math.sqrt(vx * vx + vy * vy)
            nx = vx / magnitude
            ny = vy / magnitude

            tx = int(cx + nx * radius)
            ty = int(cy + ny * radius)

            if not self.joystick_active:
                self.transport.touch_down(JOYSTICK_POINTER_ID, tx, ty)
                self.joystick_active = True
            else:
                self.transport.touch_move(JOYSTICK_POINTER_ID, tx, ty)
        else:
            if self.joystick_active:
                self.transport.touch_up(JOYSTICK_POINTER_ID, cx, cy)
                self.joystick_active = False

    # -------------------------------------------------------------------------
    # Dynamic Button Pointer Allocation
    # -------------------------------------------------------------------------

    def _handle_binding_down(self, binding: Binding) -> None:
        if binding.toggle:
            # Toggle mode: flip state
            is_on = self.toggle_states.get(binding.id, False)
            if is_on:
                self._release_binding_pointer(binding.id)
                self.toggle_states[binding.id] = False
            else:
                self._engage_binding_pointer(binding)
                self.toggle_states[binding.id] = True
        else:
            # Standard tap / hold mode
            self._engage_binding_pointer(binding)

    def _handle_binding_up(self, binding: Binding) -> None:
        if binding.toggle:
            # Toggles do not release on key-up
            return
        self._release_binding_pointer(binding.id)

    def _engage_binding_pointer(self, binding: Binding) -> None:
        if binding.id in self.binding_pointer_map:
            return  # Already engaged

        if not self.available_pointers:
            logger.warning("Pointer pool exhausted! Max 8 simultaneous button contacts reached.")
            return

        pid = self.available_pointers.pop(0)
        self.binding_pointer_map[binding.id] = pid

        px = int(binding.norm_x * self.profile.ref_width)
        py = int(binding.norm_y * self.profile.ref_height)
        self.transport.touch_down(pid, px, py)

    def _release_binding_pointer(self, binding_id: str) -> None:
        if binding_id not in self.binding_pointer_map:
            return

        pid = self.binding_pointer_map.pop(binding_id)
        # Find binding for coordinates
        b = next((x for x in self.profile.bindings if x.id == binding_id), None)
        if b:
            px = int(b.norm_x * self.profile.ref_width)
            py = int(b.norm_y * self.profile.ref_height)
        else:
            px = self.profile.ref_width // 2
            py = self.profile.ref_height // 2

        self.transport.touch_up(pid, px, py)
        self.available_pointers.append(pid)
        self.available_pointers.sort()
