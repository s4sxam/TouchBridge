"""TouchBridge Data Models and Configuration Schemas.

Defines profiles, keybindings, touch contacts, and coordinate structures.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any


class ControlType(str, Enum):
    """Types of virtual game controls mapped onto the touch screen."""
    TAP = "tap"
    JOYSTICK = "joystick"
    MOUSE_LOOK = "mouse_look"
    HOLD = "hold"
    TOGGLE = "toggle"
    SWIPE = "swipe"


class ScreenOrientation(str, Enum):
    """Screen orientation for key mapping."""
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


@dataclass
class Binding:
    """Individual key or mouse mapping to a virtual touch screen element."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Control"
    control_type: ControlType = ControlType.TAP

    # Normalized screen coordinates [0.0, 1.0]
    norm_x: float = 0.5
    norm_y: float = 0.5
    radius: float = 0.05  # Normalized size/radius

    # Primary physical bindings
    key: Optional[str] = None           # e.g., "space", "r", "f", "shift"
    mouse_button: Optional[str] = None  # e.g., "left", "right", "middle"

    # Directional keys for JOYSTICK control type
    up_key: str = "w"
    down_key: str = "s"
    left_key: str = "a"
    right_key: str = "d"

    # Mouse Look configuration
    sensitivity_x: float = 1.0
    sensitivity_y: float = 1.0
    deadzone: float = 0.01
    zone_width: float = 0.40   # Look zone width [0.0..1.0]
    zone_height: float = 0.60  # Look zone height [0.0..1.0]

    # Behaviors
    hold: bool = False
    toggle: bool = False
    repeat_rate_ms: int = 0    # 0 = no repeat; >0 = auto-repeat tap interval

    def clamp_coordinates(self) -> None:
        """Clamp normalized coordinates safely within [0.0, 1.0]."""
        self.norm_x = max(0.0, min(1.0, float(self.norm_x)))
        self.norm_y = max(0.0, min(1.0, float(self.norm_y)))
        self.radius = max(0.01, min(0.5, float(self.radius)))

    def to_dict(self) -> Dict[str, Any]:
        """Convert binding to dictionary."""
        d = asdict(self)
        d["control_type"] = self.control_type.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Binding:
        """Create a Binding from dictionary with schema tolerance."""
        c_type = data.get("control_type", ControlType.TAP.value)
        if isinstance(c_type, str):
            try:
                c_type_enum = ControlType(c_type)
            except ValueError:
                c_type_enum = ControlType.TAP
        else:
            c_type_enum = c_type

        b = cls(
            id=str(data.get("id", str(uuid.uuid4())[:8])),
            name=str(data.get("name", "Control")),
            control_type=c_type_enum,
            norm_x=float(data.get("norm_x", 0.5)),
            norm_y=float(data.get("norm_y", 0.5)),
            radius=float(data.get("radius", 0.05)),
            key=data.get("key"),
            mouse_button=data.get("mouse_button"),
            up_key=str(data.get("up_key", "w")),
            down_key=str(data.get("down_key", "s")),
            left_key=str(data.get("left_key", "a")),
            right_key=str(data.get("right_key", "d")),
            sensitivity_x=float(data.get("sensitivity_x", 1.0)),
            sensitivity_y=float(data.get("sensitivity_y", 1.0)),
            deadzone=float(data.get("deadzone", 0.01)),
            zone_width=float(data.get("zone_width", 0.40)),
            zone_height=float(data.get("zone_height", 0.60)),
            hold=bool(data.get("hold", False)),
            toggle=bool(data.get("toggle", False)),
            repeat_rate_ms=int(data.get("repeat_rate_ms", 0)),
        )
        b.clamp_coordinates()
        return b


@dataclass
class Profile:
    """Game-specific or universal key mapping profile."""
    name: str = "Default Profile"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    package_name: Optional[str] = None  # e.g. "com.dts.freefireth" or None for generic
    orientation: ScreenOrientation = ScreenOrientation.LANDSCAPE
    ref_width: int = 2400
    ref_height: int = 1080
    mouse_sensitivity: float = 1.0
    smoothing: bool = True
    emergency_stop_key: str = "f12"
    mouse_toggle_key: str = "ctrl+`"
    version: int = 1
    bindings: List[Binding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dict."""
        return {
            "version": self.version,
            "id": self.id,
            "name": self.name,
            "package_name": self.package_name,
            "orientation": self.orientation.value,
            "ref_width": self.ref_width,
            "ref_height": self.ref_height,
            "mouse_sensitivity": self.mouse_sensitivity,
            "smoothing": self.smoothing,
            "emergency_stop_key": self.emergency_stop_key,
            "mouse_toggle_key": self.mouse_toggle_key,
            "bindings": [b.to_dict() for b in self.bindings],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Profile:
        """Create Profile from dictionary safely."""
        orient = data.get("orientation", ScreenOrientation.LANDSCAPE.value)
        try:
            orient_enum = ScreenOrientation(orient)
        except ValueError:
            orient_enum = ScreenOrientation.LANDSCAPE

        bindings_raw = data.get("bindings", [])
        bindings = [Binding.from_dict(b) for b in bindings_raw if isinstance(b, dict)]

        return cls(
            version=int(data.get("version", 1)),
            id=str(data.get("id", str(uuid.uuid4()))),
            name=str(data.get("name", "Untitled Profile")),
            package_name=data.get("package_name"),
            orientation=orient_enum,
            ref_width=int(data.get("ref_width", 2400)),
            ref_height=int(data.get("ref_height", 1080)),
            mouse_sensitivity=float(data.get("mouse_sensitivity", 1.0)),
            smoothing=bool(data.get("smoothing", True)),
            emergency_stop_key=str(data.get("emergency_stop_key", "f12")),
            mouse_toggle_key=str(data.get("mouse_toggle_key", "ctrl+`")),
            bindings=bindings,
        )


@dataclass
class TouchContact:
    """An active simulated touch pointer contact on Android screen."""
    pointer_id: int
    x: int
    y: int
    norm_x: float
    norm_y: float
    is_down: bool = True
    binding_id: Optional[str] = None
    pressure: float = 1.0
