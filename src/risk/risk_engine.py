"""
ELIOS-SAR
Phase 7 - Risk Analysis

Converts a SituationalState into a risk assessment.

The thresholds in this prototype are engineering/demo thresholds.
They are not certified mine-safety limits.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.situational_awareness.situational_state_builder import SituationalState


@dataclass
class RiskAssessment:
    """Result produced by the risk-analysis layer."""

    person_risk: str
    hazard_risk: str
    environmental_risk: str
    isolation_risk: str
    overall_risk: str
    priority_score: int
    explanation: str


class RiskEngine:
    """Evaluate urgency while keeping each risk dimension explicit."""

    RISK_ORDER = {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
        "CRITICAL": 3,
        "UNKNOWN": -1,
    }

    def calculate_person_risk(self, state: SituationalState) -> str:
        if not state.person_present:
            return "LOW"
        if state.gas_status == "CRITICAL":
            return "CRITICAL"
        if state.gas_status == "WARNING":
            return "HIGH"
        if state.temperature_status == "CRITICAL":
            return "CRITICAL"
        if state.temperature_status == "WARNING":
            return "HIGH"
        if state.obstacle_status == "CRITICAL":
            return "HIGH"
        if state.obstacle_status == "WARNING":
            return "MEDIUM"
        return "LOW"

    def calculate_hazard_risk(self, state: SituationalState) -> str:
        statuses = [
            state.gas_status,
            state.temperature_status,
            state.humidity_status,
            state.obstacle_status,
        ]
        if "CRITICAL" in statuses:
            return "CRITICAL"
        if "WARNING" in statuses:
            return "HIGH"
        if all(status == "UNKNOWN" for status in statuses):
            return "UNKNOWN"
        return "LOW"

    def calculate_environmental_risk(self, state: SituationalState) -> str:
        statuses = [
            state.gas_status,
            state.temperature_status,
            state.humidity_status,
        ]
        critical_count = sum(status == "CRITICAL" for status in statuses)
        warning_count = sum(status == "WARNING" for status in statuses)

        if critical_count >= 1 or warning_count >= 2:
            return "CRITICAL"
        if warning_count == 1:
            return "HIGH"
        if all(status == "UNKNOWN" for status in statuses):
            return "UNKNOWN"
        return "LOW"

    def calculate_isolation_risk(self, person_count: int) -> str:
        if person_count <= 0:
            return "LOW"
        if person_count == 1:
            return "HIGH"
        if person_count <= 3:
            return "MEDIUM"
        return "LOW"

    def calculate_overall_risk(
        self,
        person_risk: str,
        hazard_risk: str,
        environmental_risk: str,
        isolation_risk: str,
        person_present: bool,
    ) -> str:
        risks = [person_risk, hazard_risk, environmental_risk]
        highest_risk = max(
            risks,
            key=lambda risk: self.RISK_ORDER.get(risk, -1),
            default="LOW",
        )
        if person_present and isolation_risk == "HIGH":
            if highest_risk == "LOW":
                highest_risk = "MEDIUM"
            elif highest_risk == "MEDIUM":
                highest_risk = "HIGH"
        return highest_risk

    def calculate_priority_score(self, overall_risk: str, person_present: bool) -> int:
        base_scores = {
            "LOW": 10,
            "MEDIUM": 40,
            "HIGH": 70,
            "CRITICAL": 100,
            "UNKNOWN": 0,
        }
        score = base_scores.get(overall_risk, 0)
        if person_present:
            score += 10
        return min(score, 100)

    def generate_explanation(
        self,
        person_risk: str,
        hazard_risk: str,
        environmental_risk: str,
        isolation_risk: str,
        overall_risk: str,
    ) -> str:
        return (
            f"Person risk={person_risk}; hazard risk={hazard_risk}; "
            f"environmental risk={environmental_risk}; "
            f"isolation risk={isolation_risk}; overall risk={overall_risk}."
        )

    def assess(self, state: SituationalState) -> RiskAssessment:
        person_risk = self.calculate_person_risk(state)
        hazard_risk = self.calculate_hazard_risk(state)
        environmental_risk = self.calculate_environmental_risk(state)
        isolation_risk = self.calculate_isolation_risk(state.person_count)
        overall_risk = self.calculate_overall_risk(
            person_risk=person_risk,
            hazard_risk=hazard_risk,
            environmental_risk=environmental_risk,
            isolation_risk=isolation_risk,
            person_present=state.person_present,
        )
        priority_score = self.calculate_priority_score(
            overall_risk=overall_risk,
            person_present=state.person_present,
        )
        explanation = self.generate_explanation(
            person_risk=person_risk,
            hazard_risk=hazard_risk,
            environmental_risk=environmental_risk,
            isolation_risk=isolation_risk,
            overall_risk=overall_risk,
        )
        return RiskAssessment(
            person_risk=person_risk,
            hazard_risk=hazard_risk,
            environmental_risk=environmental_risk,
            isolation_risk=isolation_risk,
            overall_risk=overall_risk,
            priority_score=priority_score,
            explanation=explanation,
        )
