"""Integrated drone intelligence pipeline for ELIOS-SAR."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.fusion.sensor_fusion import SensorFusion
from src.mission.drone_decision import DroneDecisionEngine
from src.mission.event_generator import MissionEventGenerator
from src.risk.risk_engine import RiskEngine
from src.situational_awareness.situational_state_builder import (
    SituationalStateBuilder,
)


@dataclass
class IntelligenceResult:
    """Complete result produced by one intelligence cycle."""

    detections: List[Dict[str, Any]] = field(default_factory=list)
    sensor_state: Dict[str, Any] = field(default_factory=dict)
    situational_state: Dict[str, Any] = field(default_factory=dict)
    risk: Dict[str, Any] = field(default_factory=dict)
    mission_events: List[Any] = field(default_factory=list)
    decisions: List[Any] = field(default_factory=list)


class DroneIntelligence:
    """
    Orchestrates the ELIOS-SAR onboard intelligence pipeline.

    This class does not directly control motors or hardware.
    It connects perception, sensors, fusion, risk, mission,
    and decision layers.
    """

    def __init__(
        self,
        sensor_fusion: Optional[SensorFusion] = None,
        situational_state_builder: Optional[SituationalStateBuilder] = None,
        risk_engine: Optional[RiskEngine] = None,
        event_generator: Optional[MissionEventGenerator] = None,
        decision_engine: Optional[DroneDecisionEngine] = None,
    ) -> None:
        self.sensor_fusion = sensor_fusion or SensorFusion()
        self.situational_state_builder = (
            situational_state_builder or SituationalStateBuilder()
        )
        self.risk_engine = risk_engine or RiskEngine()
        self.event_generator = event_generator or MissionEventGenerator()
        self.decision_engine = decision_engine or DroneDecisionEngine()

    def process_cycle(
        self,
        detections: Optional[List[Dict[str, Any]]] = None,
        sensor_snapshot: Optional[Any] = None,
        position: Optional[Dict[str, float]] = None,
    ) -> IntelligenceResult:
        """
        Process one complete intelligence cycle.

        Parameters
        ----------
        detections:
            AI/perception detections.

        sensor_snapshot:
            Current environmental and LiDAR sensor information.

        position:
            Current drone position.

        Returns
        -------
        IntelligenceResult
            Structured result containing every stage of the pipeline.
        """

        detections = detections or []

        # ---------------------------------------------------------
        # STEP 1 — SENSOR FUSION
        # ---------------------------------------------------------
        fusion_state = self.sensor_fusion.fuse(
            detections=detections,
            sensor_snapshot=sensor_snapshot,
        )

        # ---------------------------------------------------------
        # STEP 2 — SITUATIONAL AWARENESS
        # ---------------------------------------------------------
        situational_state = self.situational_state_builder.build(
            fusion_state=fusion_state,
            position=position,
        )

        # ---------------------------------------------------------
        # STEP 3 — RISK ANALYSIS
        # ---------------------------------------------------------
        risk_state = self.risk_engine.evaluate(
            situational_state
        )

        # ---------------------------------------------------------
        # STEP 4 — MISSION EVENT GENERATION
        # ---------------------------------------------------------
        mission_events = self.event_generator.generate(
            situational_state=situational_state,
            risk=risk_state,
        )

        # ---------------------------------------------------------
        # STEP 5 — DRONE DECISION
        # ---------------------------------------------------------
        decisions = self.decision_engine.decide(
            situational_state=situational_state,
            risk=risk_state,
            mission_events=mission_events,
        )

        return IntelligenceResult(
            detections=detections,
            sensor_state=fusion_state,
            situational_state=situational_state,
            risk=risk_state,
            mission_events=mission_events,
            decisions=decisions,
        )
