"""Base Abstract Input Transport Interface."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Set


class InputTransport(ABC):
    """Abstract base class for all Android input transports."""

    def __init__(self, screen_width: int = 2400, screen_height: int = 1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active_pointers: Set[int] = set()

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the input receiver on the Android device."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection and clean up resources."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if connection is alive and ready to send packets."""
        pass

    @abstractmethod
    def touch_down(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        """Emit ACTION_DOWN for the specified pointer ID."""
        pass

    @abstractmethod
    def touch_move(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        """Emit ACTION_MOVE for the specified pointer ID."""
        pass

    @abstractmethod
    def touch_up(self, pointer_id: int, x: int, y: int) -> bool:
        """Emit ACTION_UP for the specified pointer ID."""
        pass

    @abstractmethod
    def release_all(self) -> None:
        """Emergency failsafe: immediately emit ACTION_UP for all active pointers."""
        pass

    def update_screen_size(self, width: int, height: int) -> None:
        """Update resolution dynamically if screen orientation or geometry changes."""
        self.screen_width = max(1, width)
        self.screen_height = max(1, height)

    def get_latency_ms(self) -> float:
        """Return recent average input injection latency in milliseconds."""
        return 0.0
