import json

from .protocol import CommunicationMessage


class MessageSerializer:

    @staticmethod
    def serialize(message: CommunicationMessage) -> str:
        return json.dumps(message.to_dict())

    @staticmethod
    def deserialize(data: str) -> CommunicationMessage:

        decoded = json.loads(data)

        required_fields = [
            "message_type",
            "source",
            "timestamp",
            "payload",
        ]

        for field in required_fields:
            if field not in decoded:
                raise ValueError(
                    f"Missing communication field: {field}"
                )

        return CommunicationMessage(
            message_id=decoded.get("message_id", ""),
            message_type=decoded["message_type"],
            source=decoded["source"],
            timestamp=decoded["timestamp"],
            payload=decoded["payload"],
        )
