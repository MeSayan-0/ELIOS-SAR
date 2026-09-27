from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Optional

import cv2


@dataclass
class Frame:
    image: Any
    frame_id: int
    timestamp: float


class FrameSource(ABC):

    @abstractmethod
    def read(self) -> Optional[Frame]:
        raise NotImplementedError

    @abstractmethod
    def release(self) -> None:
        raise NotImplementedError


class OpenCVCameraSource(FrameSource):

    def __init__(
        self,
        device: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 15,
    ) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps

        self.capture = cv2.VideoCapture(device)

        if not self.capture.isOpened():
            raise RuntimeError(f"Unable to open camera device {device}")

        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, fps)
        self.frame_id = 0

    def read(self) -> Optional[Frame]:
        ok, image = self.capture.read()
        if not ok or image is None:
            return None

        self.frame_id += 1
        return Frame(
            image=image,
            frame_id=self.frame_id,
            timestamp=time.time(),
        )

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()


class MP4Source(FrameSource):

    def __init__(
        self,
        path: str,
        loop: bool = False,
    ) -> None:
        self.path = Path(path).expanduser().resolve()
        self.loop = loop

        if not self.path.exists():
            raise FileNotFoundError(f"MP4 file not found: {self.path}")

        self.capture = cv2.VideoCapture(str(self.path))

        if not self.capture.isOpened():
            raise RuntimeError(f"Unable to open MP4 file: {self.path}")

        self.frame_id = 0

    def read(self) -> Optional[Frame]:
        ok, image = self.capture.read()

        if not ok or image is None:
            if not self.loop:
                return None

            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, image = self.capture.read()

            if not ok or image is None:
                return None

        self.frame_id += 1
        return Frame(
            image=image,
            frame_id=self.frame_id,
            timestamp=time.time(),
        )

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
