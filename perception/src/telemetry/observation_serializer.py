from __future__ import annotations

import time
from dataclasses import asdict, is_dataclass
from typing import Any


def convert_value(value: Any):
    if is_dataclass(value):
        data = asdict(value)
        data.pop("mask", None)
        return convert_value(data)

    if isinstance(value, dict):
        return {
            key: convert_value(item)
            for key, item in value.items()
            if key != "mask"
        }

    if isinstance(value, list):
        return [
            convert_value(item)
            for item in value
        ]

    if hasattr(value, "tolist"):
        return value.tolist()

    if hasattr(value, "item"):
        return value.item()

    return value


class ObservationSerializer:
    def __init__(self, drone_id: str):
        self.drone_id = drone_id
        self.frame_id = 0

    def build(
        self,
        persons=None,
        hazards=None,
        drone_pose=None,
        sensors=None,
        risk=None,
        timestamp=None,
    ) -> dict:
        self.frame_id += 1

        return {
            "type": "ai_observation",
            "source": "ELIOS",
            "drone_id": self.drone_id,
            "timestamp": (
                float(timestamp)
                if timestamp is not None
                else time.time()
            ),
            "frame_id": self.frame_id,
            "persons": convert_value(persons or []),
            "hazards": convert_value(hazards or {}),
            "drone_pose": convert_value(drone_pose),
            "sensors": convert_value(sensors or {}),
            "risk": convert_value(risk or {}),
        }
