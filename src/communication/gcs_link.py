from __future__ import annotations

from typing import Any, Optional

from src.communication.protocol import (
    CommunicationMessage,
    MESSAGE_ACK,
    MESSAGE_DRONE_STATE,
    MESSAGE_HAZARD,
    MESSAGE_MAP_UPDATE,
    MESSAGE_MISSION_EVENT,
    MESSAGE_PERSON_DETECTION,
    MESSAGE_RISK_EVENT,
    MESSAGE_SENSOR_STATE,
)
from src.communication.serializer import MessageSerializer
from src.communication.transport import LocalTransport


class GCSLink:
    """
    Simulated communication endpoint representing the ELIOS-SAR
    Ground Control Station.
    """

    def __init__(
        self,
        gcs_id: str,
        transport: LocalTransport,
    ) -> None:
        self.gcs_id = gcs_id
        self.transport = transport
        self.serializer = MessageSerializer()

        self.last_drone_state: Optional[dict[str, Any]] = None
        self.last_sensor_state: Optional[dict[str, Any]] = None
        self.last_map_update: Optional[dict[str, Any]] = None

        self.person_detections: list[dict[str, Any]] = []
        self.hazards: list[dict[str, Any]] = []
        self.risk_events: list[dict[str, Any]] = []
        self.mission_events: list[dict[str, Any]] = []

    def connect(self) -> None:
        """Connect the GCS communication endpoint."""
        self.transport.connect()

    def disconnect(self) -> None:
        """Disconnect the GCS communication endpoint."""
        self.transport.disconnect()

    def receive_message(self) -> Optional[CommunicationMessage]:
        """
        Receive and process one message from the drone.
        """

        serialized = self.transport.receive()

        if serialized is None:
            return None

        message = self.serializer.deserialize(serialized)

        self.process_message(message)

        return message

    def process_message(
        self,
        message: CommunicationMessage,
    ) -> None:
        """
        Route incoming drone messages to the appropriate GCS state.
        """

        message_type = message.message_type

        if message_type == MESSAGE_DRONE_STATE:
            self.last_drone_state = message.payload

        elif message_type == MESSAGE_PERSON_DETECTION:
            self.person_detections.append(message.payload)

        elif message_type == MESSAGE_HAZARD:
            self.hazards.append(message.payload)

        elif message_type == MESSAGE_SENSOR_STATE:
            self.last_sensor_state = message.payload

        elif message_type == MESSAGE_MAP_UPDATE:
            self.last_map_update = message.payload

        elif message_type == MESSAGE_RISK_EVENT:
            self.risk_events.append(message.payload)

        elif message_type == MESSAGE_MISSION_EVENT:
            self.mission_events.append(message.payload)

    def get_latest_drone_state(self) -> Optional[dict[str, Any]]:
        return self.last_drone_state

    def get_latest_sensor_state(self) -> Optional[dict[str, Any]]:
        return self.last_sensor_state

    def get_latest_map(self) -> Optional[dict[str, Any]]:
        return self.last_map_update

    def get_person_detections(self) -> list[dict[str, Any]]:
        return list(self.person_detections)

    def get_hazards(self) -> list[dict[str, Any]]:
        return list(self.hazards)

    def get_risk_events(self) -> list[dict[str, Any]]:
        return list(self.risk_events)

    def get_mission_events(self) -> list[dict[str, Any]]:
        return list(self.mission_events)
