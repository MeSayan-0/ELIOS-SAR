"""
ELIOS-SAR
Phase 8 - Mission Event Generation

Converts risk assessments and situational states into mission events.
This layer does not directly control motors or flight.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.risk.risk_engine import RiskAssessment
from src.situational_awareness.situational_state_builder import SituationalState


@dataclass
class MissionEvent:
    """Event sent to later mission, communication, and GCS layers."""

    event_type: str
    severity: str
    priority_score: int
    person_count: int
    description: str
    requires_attention: bool


class MissionEventGenerator:
    """Convert system state and risk into mission events."""

    def generate_person_event(
        self,
        state: SituationalState,
        risk: RiskAssessment,
    ) -> MissionEvent:
        return MissionEvent(
            event_type="PERSON_DETECTED",
            severity=risk.person_risk,
            priority_score=risk.priority_score,
            person_count=state.person_count,
            description=f"{state.person_count} person(s) detected.",
            requires_attention=True,
        )

    def generate_hazard_event(
        self,
        state: SituationalState,
        risk: RiskAssessment,
    ) -> MissionEvent:
        return MissionEvent(
            event_type="HAZARD_DETECTED",
            severity=risk.hazard_risk,
            priority_score=risk.priority_score,
            person_count=state.person_count,
            description="Environmental or structural hazard detected.",
            requires_attention=True,
        )

    def generate_critical_event(
        self,
        state: SituationalState,
        risk: RiskAssessment,
    ) -> MissionEvent:
        return MissionEvent(
            event_type="CRITICAL_SITUATION",
            severity="CRITICAL",
            priority_score=100,
            person_count=state.person_count,
            description="Critical situation requires immediate attention.",
            requires_attention=True,
        )

    def generate_normal_event(
        self,
        state: SituationalState,
        risk: RiskAssessment,
    ) -> MissionEvent:
        return MissionEvent(
            event_type="NORMAL_OPERATION",
            severity="LOW",
            priority_score=risk.priority_score,
            person_count=state.person_count,
            description="No significant event detected.",
            requires_attention=False,
        )

    def generate_events(
        self,
        state: SituationalState,
        risk: RiskAssessment,
    ) -> list[MissionEvent]:
        events: list[MissionEvent] = []

        if risk.overall_risk == "CRITICAL":
            events.append(self.generate_critical_event(state, risk))
        elif state.person_present:
            events.append(self.generate_person_event(state, risk))

        if risk.hazard_risk in ["HIGH", "CRITICAL"]:
            events.append(self.generate_hazard_event(state, risk))

        if not events:
            events.append(self.generate_normal_event(state, risk))

        return events
