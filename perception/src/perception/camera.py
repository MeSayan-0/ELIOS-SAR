from __future__ import annotations

import cv2


class Camera:
    """
    Camera abstraction for ELIOS-SAR.

    Raspberry Pi:
        Uses Picamera2 when available.

    Other systems:
        Falls back to OpenCV VideoCapture.

    Output:
        OpenCV BGR numpy frame.
    """

    def __init__(
        self,
        device: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 20,
    ) -> None:

        self.width = width
        self.height = height
        self.fps = fps

        self.picam2 = None
        self.cap = None

        # ---------------------------------------------------------
        # Try Raspberry Pi Camera through Picamera2
        # ---------------------------------------------------------
        try:
            from picamera2 import Picamera2

            self.picam2 = Picamera2()

            configuration = self.picam2.create_video_configuration(
                main={
                    "size": (width, height),
                    "format": "RGB888",
                }
            )

            self.picam2.configure(configuration)

            self.picam2.start()

            print(
                f"[CAMERA] Raspberry Pi camera started: "
                f"{width}x{height}@{fps} FPS"
            )

            return

        except ImportError:
            print(
                "[CAMERA] Picamera2 not available. "
                "Falling back to OpenCV."
            )

        except Exception as error:
            print(
                f"[CAMERA] Picamera2 initialization failed: {error}"
            )
            print(
                "[CAMERA] Falling back to OpenCV."
            )

            self.picam2 = None

        # ---------------------------------------------------------
        # OpenCV fallback
        # ---------------------------------------------------------
        self.cap = cv2.VideoCapture(device)

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            width,
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            height,
        )

        self.cap.set(
            cv2.CAP_PROP_FPS,
            fps,
        )

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera device {device}"
            )

        print(
            f"[CAMERA] OpenCV camera started: "
            f"{width}x{height}"
        )

    def read(self):
        """
        Capture one frame.

        Returns:
            OpenCV BGR frame.
        """

        # ---------------------------------------------------------
        # Raspberry Pi Camera
        # ---------------------------------------------------------
        if self.picam2 is not None:

            # Picamera2 configured as RGB888.
            rgb_frame = self.picam2.capture_array()

            if rgb_frame is None:
                raise RuntimeError(
                    "Failed to capture frame from Raspberry Pi camera"
                )

            # Convert RGB -> BGR for OpenCV / YOLO pipeline.
            frame = cv2.cvtColor(
                rgb_frame,
                cv2.COLOR_RGB2BGR,
            )

            return frame

        # ---------------------------------------------------------
        # OpenCV fallback
        # ---------------------------------------------------------
        if self.cap is not None:

            ok, frame = self.cap.read()

            if not ok:
                raise RuntimeError(
                    "Failed to read camera frame"
                )

            return frame

        raise RuntimeError(
            "Camera is not initialized"
        )

    def release(self) -> None:

        if self.picam2 is not None:

            try:
                self.picam2.stop()
            except Exception:
                pass

            try:
                self.picam2.close()
            except Exception:
                pass

            self.picam2 = None

        if self.cap is not None:

            self.cap.release()
            self.cap = None
