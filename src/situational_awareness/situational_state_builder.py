"""
ELIOS-SAR
Phase 6 - Situational Awareness

Converts fused sensor information into a high-level
situational state.

This module does NOT perform risk analysis.

Responsibilities:
    - Determine whether a person is present
    - Determine environmental status
    - Determine obstacle status
    - Determine overall situation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SituationalState:
    """High-level representation of the current drone situation."""

    person_present: bool
    person_count: int
    gas_status: str
    temperature_status: str
    humidity_status: str
    obstacle_status: str
    overall_state: str


class SituationalStateBuilder:
    """Build a SituationalState from fused sensor information."""

    def __init__(
        self,
        gas_warning_threshold: float = 1000.0,
        gas_critical_threshold: float = 2000.0,
        temperature_warning_threshold: float = 40.0,
        temperature_critical_threshold: float = 50.0,
        humidity_warning_threshold: float = 80.0,
        obstacle_warning_distance: float = 2.0,
    ) -> None:
        self.gas_warning_threshold = gas_warning_threshold
        self.gas_critical_threshold = gas_critical_threshold
        self.temperature_warning_threshold = temperature_warning_threshold
        self.temperature_critical_threshold = temperature_critical_threshold
        self.humidity_warning_threshold = humidity_warning_threshold
        self.obstacle_warning_distance = obstacle_warning_distance

    def evaluate_person(self, person_count: int) -> tuple[bool, int]:
        person_count = max(0, int(person_count))
        return person_count > 0, person_count

    def evaluate_gas(self, methane_ppm: Optional[float]) -> str:
        if methane_ppm is None:
            return "UNKNOWN"
        if methane_ppm >= self.gas_critical_threshold:
            return "CRITICAL"
        if methane_ppm >= self.gas_warning_threshold:
            return "WARNING"
        return "NORMAL"

    def evaluate_temperature(self, temperature_c: Optional[float]) -> str:
        if temperature_c is None:
            return "UNKNOWN"
        if temperature_c >= self.temperature_critical_threshold:
            return "CRITICAL"
        if temperature_c >= self.temperature_warning_threshold:
            return "WARNING"
        return "NORMAL"

    def evaluate_humidity(self, humidity_percent: Optional[float]) -> str:
        if humidity_percent is None:
            return "UNKNOWN"
        if humidity_percent >= self.humidity_warning_threshold:
            return "WARNING"
        return "NORMAL"

    def evaluate_obstacle(
        self,
        nearest_obstacle_distance: Optional[float],
    ) -> str:
        if nearest_obstacle_distance is None:
            return "UNKNOWN"
        if nearest_obstacle_distance <= 0:
            return "CRITICAL"
        if nearest_obstacle_distance <= self.obstacle_warning_distance:
            return "WARNING"
        return "CLEAR"

    def determine_overall_state(
        self,
        gas_status: str,
        temperature_status: str,
        humidity_status: str,
        obstacle_status: str,
        person_present: bool,
    ) -> str:
        statuses = [
            gas_status,
            temperature_status,
            humidity_status,
            obstacle_status,
        ]

        if "CRITICAL" in statuses:
            return "CRITICAL"
        if "WARNING" in statuses:
            return "HAZARDOUS"
        if person_present:
            return "PERSON_PRESENT"
        if all(status == "UNKNOWN" for status in statuses):
            return "UNKNOWN"
        return "NORMAL"

    def build_state(
        self,
        person_count: int = 0,
        methane_ppm: Optional[float] = None,
        temperature_c: Optional[float] = None,
        humidity_percent: Optional[float] = None,
        nearest_obstacle_distance: Optional[float] = None,
    ) -> SituationalState:
        person_present, person_count = self.evaluate_person(person_count)
        gas_status = self.evaluate_gas(methane_ppm)
        temperature_status = self.evaluate_temperature(temperature_c)
        humidity_status = self.evaluate_humidity(humidity_percent)
        obstacle_status = self.evaluate_obstacle(nearest_obstacle_distance)
        overall_state = self.determine_overall_state(
            gas_status=gas_status,
            temperature_status=temperature_status,
            humidity_status=humidity_status,
            obstacle_status=obstacle_status,
            person_present=person_present,
        )

        return SituationalState(
            person_present=person_present,
            person_count=person_count,
            gas_status=gas_status,
            temperature_status=temperature_status,
            humidity_status=humidity_status,
            obstacle_status=obstacle_status,
            overall_state=overall_state,
        )
