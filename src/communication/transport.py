from collections import deque
from typing import Optional

from .protocol import CommunicationMessage


class LocalTransport:

    def __init__(self):
        self._queue = deque()
        self.connected = False

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def send(self, message: CommunicationMessage) -> None:

        if not self.connected:
            raise ConnectionError(
                "Communication transport is not connected."
            )

        self._queue.append(message)

    def receive(self) -> Optional[CommunicationMessage]:

        if not self.connected:
            raise ConnectionError(
                "Communication transport is not connected."
            )

        if not self._queue:
            return None

        return self._queue.popleft()

    def pending_messages(self) -> int:
        return len(self._queue)
