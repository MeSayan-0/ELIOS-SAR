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
    create_message,
)
from src.communication.serializer import MessageSerializer
from src.communication.transport import LocalTransport


class DroneLink:
    """
    Simulated communication endpoint representing ELIOS-SAR onboard drone.
    """

    def __init__(
        self,
        drone_id: str,
        transport: LocalTransport,
    ) -> None:
        self.drone_id = drone_id
        self.transport = transport
        self.serializer = MessageSerializer()

    def connect(self) -> None:
        """Connect the drone communication endpoint."""
        self.transport.connect()

    def disconnect(self) -> None:
        """Disconnect the drone communication endpoint."""
        self.transport.disconnect()

    def send_message(
        self,
        message_type: str,
        payload: dict[str, Any],
    ) -> CommunicationMessage:
        """
        Create, serialize, and send a message from the drone.
        """

        message = create_message(
            message_type=message_type,
            source=self.drone_id,
            payload=payload,
        )

        serialized = self.serializer.serialize(message)
        self.transport.send(serialized)

        return message

    def send_drone_state(
        self,
        position: dict[str, float],
        battery: float,
        armed: bool,
        flight_mode: str,
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_DRONE_STATE,
            {
                "drone_id": self.drone_id,
                "position": position,
                "battery": battery,
                "armed": armed,
                "flight_mode": flight_mode,
            },
        )

    def send_person_detection(
        self,
        person_id: str,
        position: dict[str, float],
        confidence: float,
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_PERSON_DETECTION,
            {
                "person_id": person_id,
                "position": position,
                "confidence": confidence,
            },
        )

    def send_hazard(
        self,
        hazard_type: str,
        position: dict[str, float],
        severity: str,
        confidence: float,
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_HAZARD,
            {
                "hazard_type": hazard_type,
                "position": position,
                "severity": severity,
                "confidence": confidence,
            },
        )

    def send_sensor_state(
        self,
        gas: Optional[float],
        temperature: Optional[float],
        humidity: Optional[float],
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_SENSOR_STATE,
            {
                "gas": gas,
                "temperature": temperature,
                "humidity": humidity,
            },
        )

    def send_map_update(
        self,
        drone_position: dict[str, float],
        map_data: dict[str, Any],
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_MAP_UPDATE,
            {
                "drone_position": drone_position,
                "map": map_data,
            },
        )

    def send_risk_event(
        self,
        risk_level: str,
        score: float,
        affected_person_id: Optional[str],
        reason: str,
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_RISK_EVENT,
            {
                "risk_level": risk_level,
                "score": score,
                "affected_person_id": affected_person_id,
                "reason": reason,
            },
        )

    def send_mission_event(
        self,
        mission_id: str,
        event_type: str,
        description: str,
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_MISSION_EVENT,
            {
                "mission_id": mission_id,
                "event_type": event_type,
                "description": description,
            },
        )

    def receive_message(self) -> Optional[CommunicationMessage]:
        """
        Receive the next message available on the transport.
        """

        serialized = self.transport.receive()

        if serialized is None:
            return None

        return self.serializer.deserialize(serialized)

    def send_ack(
        self,
        acknowledged_message_id: str,
    ) -> CommunicationMessage:

        return self.send_message(
            MESSAGE_ACK,
            {
                "acknowledged_message_id": acknowledged_message_id,
            },
        )
