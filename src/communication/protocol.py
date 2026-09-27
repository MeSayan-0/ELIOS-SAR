from dataclasses import dataclass, field
from typing import Any, Dict
from datetime import datetime


MESSAGE_DRONE_STATE = "DRONE_STATE"
MESSAGE_VEHICLE_STATE = "VEHICLE_STATE"
MESSAGE_PERSON_DETECTION = "PERSON_DETECTION"
MESSAGE_HAZARD = "HAZARD"
MESSAGE_SENSOR_STATE = "SENSOR_STATE"
MESSAGE_MAP_UPDATE = "MAP_UPDATE"
MESSAGE_RISK_EVENT = "RISK_EVENT"
MESSAGE_MISSION_EVENT = "MISSION_EVENT"
MESSAGE_MISSION_STATE = "MISSION_STATE"
MESSAGE_COMMAND = "COMMAND"
MESSAGE_COMMAND_ACK = "COMMAND_ACK"
MESSAGE_ACK = "ACK"


@dataclass
class CommunicationMessage:
    message_type: str
    source: str
    timestamp: str
    payload: Dict[str, Any] = field(default_factory=dict)
    message_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


def create_message(
    message_type: str,
    source: str,
    payload: Dict[str, Any],
    message_id: str = "",
) -> CommunicationMessage:

    return CommunicationMessage(
        message_type=message_type,
        source=source,
        timestamp=datetime.utcnow().isoformat(),
        payload=payload,
        message_id=message_id,
    )
