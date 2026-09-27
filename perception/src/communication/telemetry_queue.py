from __future__ import annotations

from queue import Queue, Full, Empty
from threading import Thread, Event, Lock
from typing import Any, Callable
import time


class TelemetryQueue:
    """
    Non-blocking communication queue.

    The AI loop should never wait indefinitely for networking.
    """

    def __init__(
        self,
        sender: Callable[[dict[str, Any]], None],
        max_size: int = 100,
    ):
        self.sender = sender
        self.queue: Queue = Queue(maxsize=max_size)
        self.stop_event = Event()
        self.worker: Thread | None = None
        self.lock = Lock()
        self.dropped_messages = 0
        self.sent_messages = 0
        self.error_count = 0
        self.last_error = ""

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            return

        self.stop_event.clear()

        self.worker = Thread(
            target=self._worker_loop,
            daemon=True,
        )

        self.worker.start()

    def put(
        self,
        message: dict[str, Any],
        priority: str = "normal",
    ) -> bool:

        packet = {
            "priority": priority,
            "timestamp": time.time(),
            "message": message,
        }

        try:
            self.queue.put_nowait(packet)
            return True

        except Full:
            self.dropped_messages += 1
            return False

    def _worker_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                packet = self.queue.get(
                    timeout=0.2
                )

            except Empty:
                continue

            try:
                self.sender(packet["message"])
                self.sent_messages += 1

            except Exception as exc:
                self.error_count += 1
                self.last_error = str(exc)

            finally:
                self.queue.task_done()

    def stop(self) -> None:
        self.stop_event.set()

        if self.worker:
            self.worker.join(timeout=2.0)

    def snapshot(self) -> dict:
        return {
            "queue_size": self.queue.qsize(),
            "dropped_messages": self.dropped_messages,
            "sent_messages": self.sent_messages,
            "error_count": self.error_count,
            "last_error": self.last_error,
        }
