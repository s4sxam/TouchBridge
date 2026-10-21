"""Mock Input Transport for Testing and Headless Environments."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .base import InputTransport


@dataclass
class RecordedEvent:
    action: str  # "DOWN", "MOVE", "UP"
    pointer_id: int
    x: int
    y: int
    pressure: float


class MockTransport(InputTransport):
    """In-memory mock transport recording all touch events for verification."""

    def __init__(self, screen_width: int = 2400, screen_height: int = 1080):
        super().__init__(screen_width, screen_height)
        self.connected = False
        self.events: List[RecordedEvent] = []
        self.current_positions: Dict[int, Tuple[int, int]] = {}
        self.down_counts: Dict[int, int] = {}
        self.up_counts: Dict[int, int] = {}

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self) -> None:
        self.release_all()
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def touch_down(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        if not self.connected:
            return False
        self.active_pointers.add(pointer_id)
        self.current_positions[pointer_id] = (x, y)
        self.down_counts[pointer_id] = self.down_counts.get(pointer_id, 0) + 1
        self.events.append(RecordedEvent("DOWN", pointer_id, x, y, pressure))
        return True

    def touch_move(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        if not self.connected:
            return False
        self.active_pointers.add(pointer_id)
        self.current_positions[pointer_id] = (x, y)
        self.events.append(RecordedEvent("MOVE", pointer_id, x, y, pressure))
        return True

    def touch_up(self, pointer_id: int, x: int, y: int) -> bool:
        if not self.connected:
            return False
        self.active_pointers.discard(pointer_id)
        self.current_positions.pop(pointer_id, None)
        self.up_counts[pointer_id] = self.up_counts.get(pointer_id, 0) + 1
        self.events.append(RecordedEvent("UP", pointer_id, x, y, 0.0))
        return True

    def release_all(self) -> None:
        for pid in list(self.active_pointers):
            pos = self.current_positions.get(pid, (0, 0))
            self.touch_up(pid, pos[0], pos[1])
        self.active_pointers.clear()
        self.current_positions.clear()

    def get_latency_ms(self) -> float:
        return 0.5
