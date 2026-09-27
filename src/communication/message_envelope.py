from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import json
import uuid


@dataclass(frozen=True)
class MessageEnvelope:
    """
    Common transport envelope for ELIOS-SAR messages.

    The envelope does not generate operational data.
    It only carries a payload produced by another subsystem.
    """

    message_type: str
    source: str
    payload: dict[str, Any]

    message_id: str
    timestamp: str

    def __post_init__(self) -> None:
        if not self.message_type:
            raise ValueError("message_type is required")

        if not self.source:
            raise ValueError("source is required")

        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a dictionary")

        if not self.message_id:
            raise ValueError("message_id is required")

        if not self.timestamp:
            raise ValueError("timestamp is required")

    @classmethod
    def create(
        cls,
        message_type: str,
        source: str,
        payload: dict[str, Any],
    ) -> "MessageEnvelope":
        """
        Create an envelope around an already-existing payload.

        No operational/default data is inserted.
        """

        return cls(
            message_type=message_type,
            source=source,
            payload=dict(payload),
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": dict(self.payload),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "MessageEnvelope":

        if not isinstance(data, dict):
            raise TypeError("message data must be a dictionary")

        required_fields = (
            "message_type",
            "message_id",
            "timestamp",
            "source",
            "payload",
        )

        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(
                    f"{field_name} is required"
                )

        return cls(
            message_type=data["message_type"],
            message_id=data["message_id"],
            timestamp=data["timestamp"],
            source=data["source"],
            payload=dict(data["payload"]),
        )

    @classmethod
    def from_json(
        cls,
        value: str,
    ) -> "MessageEnvelope":

        data = json.loads(value)

        return cls.from_dict(data)
