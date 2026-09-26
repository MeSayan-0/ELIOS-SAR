"""
ELIOS-SAR
Phase 10 - Flight Command Definitions

Defines high-level commands that can later be translated into PX4/Pixhawk
commands.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FlightCommand:
    """High-level flight instruction."""

    command: str
    target_x: float | None = None
    target_y: float | None = None
    target_z: float | None = None
    yaw: float | None = None
    reason: str = ""
