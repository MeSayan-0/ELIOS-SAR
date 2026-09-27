"""
ELIOS-SAR
Phase 9 - Drone Decision Logic

Converts mission events into high-level drone actions.
This module does not directly control the flight motors.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.mission.event_generator import MissionEvent


@dataclass
class DroneCommand:
    """High-level command for a later drone-controller adapter."""

    command: str
    priority: int
    reason: str
    requires_operator: bool


class DroneDecisionEngine:
    """Determine drone intent from mission events."""

    def emergency_return(self) -> DroneCommand:
        return DroneCommand(
            command="EMERGENCY_RETURN",
            priority=100,
            reason="Critical situation detected.",
            requires_operator=True,
        )

    def investigate_person(self, event: MissionEvent) -> DroneCommand:
        return DroneCommand(
            command="INVESTIGATE_PERSON",
            priority=80,
            reason=event.description,
            requires_operator=True,
        )

    def investigate_hazard(self, event: MissionEvent) -> DroneCommand:
        return DroneCommand(
            command="INVESTIGATE_HAZARD",
            priority=70,
            reason=event.description,
            requires_operator=True,
        )

    def continue_mission(self) -> DroneCommand:
        return DroneCommand(
            command="CONTINUE_MISSION",
            priority=10,
            reason="No urgent event detected.",
            requires_operator=False,
        )

    def decide(self, events: list[MissionEvent]) -> DroneCommand:
        if not events:
            return self.continue_mission()

        highest_priority_event = max(
            events,
            key=lambda event: event.priority_score,
        )

        if highest_priority_event.event_type == "CRITICAL_SITUATION":
            return self.emergency_return()
        if highest_priority_event.event_type == "PERSON_DETECTED":
            return self.investigate_person(highest_priority_event)
        if highest_priority_event.event_type == "HAZARD_DETECTED":
            return self.investigate_hazard(highest_priority_event)
        return self.continue_mission()
