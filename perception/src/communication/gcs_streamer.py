from __future__ import annotations

import json
import logging
import queue
import socket
import struct
import threading
import time
from typing import Any, Optional

import cv2

logger = logging.getLogger("ELIOS-SAR-TCP")

VIDEO_MAGIC = b"ELIO"
VIDEO_PROTOCOL_VERSION = 1
VIDEO_HEADER_FORMAT = "!4sBQQI"
VIDEO_HEADER_SIZE = struct.calcsize(VIDEO_HEADER_FORMAT)


class GCSTCPStreamer:

    def __init__(
        self,
        gcs_host: str,
        video_port: int = 8765,
        ai_port: int = 8766,
        drone_id: str = "DRONE-01",
        jpeg_quality: int = 70,
        video_queue_size: int = 1,
        ai_queue_size: int = 100,
        reconnect_delay: float = 2.0,
        connect_timeout: float = 3.0,
    ) -> None:
        self.gcs_host = gcs_host
        self.video_port = int(video_port)
        self.ai_port = int(ai_port)
        self.drone_id = drone_id
        self.jpeg_quality = int(jpeg_quality)
        self.reconnect_delay = reconnect_delay
        self.connect_timeout = connect_timeout

        self.video_queue: queue.Queue[bytes] = queue.Queue(maxsize=video_queue_size)
        self.ai_queue: queue.Queue[str] = queue.Queue(maxsize=ai_queue_size)

        self.video_socket: Optional[socket.socket] = None
        self.ai_socket: Optional[socket.socket] = None

        self.video_lock = threading.Lock()
        self.ai_lock = threading.Lock()

        self.running = False
        self._frame_counter = 0
        self.video_thread: Optional[threading.Thread] = None
        self.ai_thread: Optional[threading.Thread] = None

    def connect(self, wait: bool = False) -> None:
        if self.running:
            return

        self.running = True

        self.video_thread = threading.Thread(
            target=self._video_worker,
            name="ELIOS-Video-TCP",
            daemon=True,
        )
        self.ai_thread = threading.Thread(
            target=self._ai_worker,
            name="ELIOS-AI-TCP",
            daemon=True,
        )

        self.video_thread.start()
        self.ai_thread.start()

        if wait:
            time.sleep(0.1)

    def send_video_frame(
        self,
        frame: Any,
        frame_id: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
    ) -> None:
        if not self.running:
            return

        try:
            success, encoded = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality],
            )
            if not success:
                logger.warning("Video JPEG encoding failed")
                return

            jpeg_bytes = encoded.tobytes()

            if frame_id is None:
                self._frame_counter += 1
                fid = self._frame_counter
            else:
                fid = int(frame_id)

            if timestamp_ms is None:
                t_ms = int(time.time() * 1000)
            else:
                t_ms = int(timestamp_ms)

            header = struct.pack(
                VIDEO_HEADER_FORMAT,
                VIDEO_MAGIC,
                VIDEO_PROTOCOL_VERSION,
                fid,
                t_ms,
                len(jpeg_bytes),
            )
            payload = header + jpeg_bytes

            try:
                self.video_queue.put_nowait(payload)
                return
            except queue.Full:
                try:
                    self.video_queue.get_nowait()
                except queue.Empty:
                    pass

                try:
                    self.video_queue.put_nowait(payload)
                except queue.Full:
                    pass

        except Exception as exc:
            logger.warning("Video preparation failed: %s", exc)

    def send_ai_data(self, packet: dict[str, Any]) -> None:
        if not self.running:
            return

        try:
            message = json.dumps(
                packet,
                separators=(",", ":"),
                ensure_ascii=False,
            ) + "\n"

            try:
                self.ai_queue.put_nowait(message)
            except queue.Full:
                try:
                    self.ai_queue.get_nowait()
                except queue.Empty:
                    pass

                try:
                    self.ai_queue.put_nowait(message)
                except queue.Full:
                    pass

        except Exception as exc:
            logger.warning("AI message preparation failed: %s", exc)

    def _video_worker(self) -> None:
        while self.running:
            try:
                payload = self.video_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not payload:
                continue

            if not self._ensure_video_connection():
                continue

            try:
                with self.video_lock:
                    if self.video_socket is None:
                        continue
                    self.video_socket.sendall(payload)
            except Exception as exc:
                logger.warning("Video TCP send failed: %s", exc)
                self._close_video_socket()

    def _ai_worker(self) -> None:
        while self.running:
            try:
                message = self.ai_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not message:
                continue

            if not self._ensure_ai_connection():
                continue

            try:
                with self.ai_lock:
                    if self.ai_socket is None:
                        continue
                    self.ai_socket.sendall(message.encode("utf-8"))
            except Exception as exc:
                logger.warning("AI TCP send failed: %s", exc)
                self._close_ai_socket()

    def _ensure_video_connection(self) -> bool:
        with self.video_lock:
            if self.video_socket is not None:
                return True

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.connect_timeout)
                sock.connect((self.gcs_host, self.video_port))
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(3.0)
                self.video_socket = sock
                logger.info("VIDEO TCP connected to %s:%s", self.gcs_host, self.video_port)
                return True
            except Exception as exc:
                logger.debug("VIDEO TCP connection failed: %s", exc)
                try:
                    sock.close()
                except Exception:
                    pass
                self.video_socket = None
                time.sleep(self.reconnect_delay)
                return False

    def _ensure_ai_connection(self) -> bool:
        with self.ai_lock:
            if self.ai_socket is not None:
                return True

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.connect_timeout)
                sock.connect((self.gcs_host, self.ai_port))
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(3.0)
                self.ai_socket = sock
                logger.info("AI TCP connected to %s:%s", self.gcs_host, self.ai_port)
                return True
            except Exception as exc:
                logger.debug("AI TCP connection failed: %s", exc)
                try:
                    sock.close()
                except Exception:
                    pass
                self.ai_socket = None
                time.sleep(self.reconnect_delay)
                return False

    def _close_video_socket(self) -> None:
        with self.video_lock:
            if self.video_socket is not None:
                try:
                    self.video_socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.video_socket.close()
                except Exception:
                    pass
            self.video_socket = None

    def _close_ai_socket(self) -> None:
        with self.ai_lock:
            if self.ai_socket is not None:
                try:
                    self.ai_socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.ai_socket.close()
                except Exception:
                    pass
            self.ai_socket = None

    def close(self) -> None:
        self.running = False
        self._close_video_socket()
        self._close_ai_socket()

        try:
            self.video_queue.put_nowait(b"")
        except queue.Full:
            pass

        try:
            self.ai_queue.put_nowait("")
        except queue.Full:
            pass

        if self.video_thread is not None:
            self.video_thread.join(timeout=2.0)

        if self.ai_thread is not None:
            self.ai_thread.join(timeout=2.0)

        self.video_thread = None
        self.ai_thread = None
        logger.info("GCS TCP transport closed")
