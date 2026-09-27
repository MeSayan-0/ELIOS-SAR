from __future__ import annotations

import argparse
from datetime import datetime, timezone
import logging
from pathlib import Path
import queue
import sys
import threading
import time
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from drone.config import (
    GCS_HOST,
    VIDEO_PORT,
    AI_PORT,
    DRONE_ID,
    CAMERA_DEVICE,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    MODEL_PATH,
    YOLO_CONFIDENCE,
    POSE_MODEL_PATH,
    POSE_CONFIDENCE,
    POSE_IMAGE_SIZE,
    POSE_INTERVAL_FRAMES,
    FIRE_MODEL_PATH,
    FLOOD_MODEL_PATH,
    BOULDER_MODEL_PATH,
    FIRE_CONFIDENCE,
    FLOOD_CONFIDENCE,
    BOULDER_CONFIDENCE,
    HAZARD_IMAGE_SIZE,
    BOULDER_IMAGE_SIZE,
    FIRE_INTERVAL_FRAMES,
    FLOOD_INTERVAL_FRAMES,
    BOULDER_INTERVAL_FRAMES,
    FIRE_RATE,
    FLOOD_RATE,
    BOULDER_RATE,
    ENABLE_FIRE,
    ENABLE_FLOOD,
    ENABLE_BOULDER,
    ENABLE_POSE,
    PERSON_RISK_SCORE,
    RISK_EVENT_COOLDOWN_SECONDS,
)

from src.perception.rgb_detector import RGBDetector
from src.perception.pose_estimator import PoseEstimator
from src.perception.hazard_detector import HazardDetector
from src.perception.boulder_detector import BoulderDetector
from src.perception.ai_scheduler import AIScheduler
from src.perception.risk_engine import RiskEngine
from src.perception.perception_pipeline import PerceptionPipeline
from src.perception.hardened_pipeline import HardenedPipeline
from src.core.risk_state import PersistentRiskState
from src.communication.gcs_streamer import GCSTCPStreamer
from src.sources.frame_source import (
    FrameSource,
    OpenCVCameraSource,
    MP4Source,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("ELIOS-SAR")


class CachedDetectionState:
    """
    Thread-safe cache holding the most recent AI detections.
    Implements a freshness timeout so stale detections are not drawn indefinitely.
    """

    def __init__(self, freshness_timeout: float = 1.5):
        self.freshness_timeout = float(freshness_timeout)
        self.lock = threading.Lock()
        self.detections: list[dict[str, Any]] = []
        self.last_updated: float = 0.0
        self.last_frame_id: int = 0

    def update(self, detections: list[dict[str, Any]], frame_id: int):
        with self.lock:
            self.detections = list(detections)
            self.last_updated = time.time()
            self.last_frame_id = frame_id

    def get_fresh_detections(self) -> list[dict[str, Any]]:
        with self.lock:
            if not self.detections:
                return []
            if time.time() - self.last_updated > self.freshness_timeout:
                return []
            return list(self.detections)


def build_perception_pipeline(
    with_risk: bool = False,
    detector: Optional[str] = None,
) -> HardenedPipeline:
    if detector is not None:
        person_detector = None
        pose_estimator = None
        fire_detector = None
        flood_detector = None
        boulder_detector = None

        if detector == "person":
            logger.info("Loading person detector (single-model): %s", MODEL_PATH)
            person_detector = RGBDetector(
                model_path=MODEL_PATH,
                confidence=YOLO_CONFIDENCE,
            )
        elif detector == "boulder":
            logger.info("Loading boulder detector (single-model): %s", BOULDER_MODEL_PATH)
            boulder_detector = BoulderDetector(
                model_path=BOULDER_MODEL_PATH,
                confidence=BOULDER_CONFIDENCE,
                image_size=BOULDER_IMAGE_SIZE,
            )
        elif detector == "fire":
            logger.info("Loading fire detector (single-model): %s", FIRE_MODEL_PATH)
            fire_detector = HazardDetector(
                model_path=FIRE_MODEL_PATH,
                hazard_type="fire",
                confidence=FIRE_CONFIDENCE,
                image_size=HAZARD_IMAGE_SIZE,
            )
        elif detector == "flood":
            logger.info("Loading flood detector (single-model): %s", FLOOD_MODEL_PATH)
            flood_detector = HazardDetector(
                model_path=FLOOD_MODEL_PATH,
                hazard_type="flood",
                confidence=FLOOD_CONFIDENCE,
                image_size=HAZARD_IMAGE_SIZE,
            )

        scheduler = None
        if any((fire_detector, flood_detector, boulder_detector)):
            scheduler = AIScheduler(
                fire_detector=fire_detector,
                flood_detector=flood_detector,
                boulder_detector=boulder_detector,
                fire_rate=1.0 if fire_detector else 0.0,
                flood_rate=1.0 if flood_detector else 0.0,
                boulder_rate=1.0 if boulder_detector else 0.0,
            )
    else:
        logger.info("Loading person detector: %s", MODEL_PATH)
        person_detector = RGBDetector(
            model_path=MODEL_PATH,
            confidence=YOLO_CONFIDENCE,
        )

        pose_estimator = None
        if ENABLE_POSE:
            logger.info("Loading pose estimator: %s", POSE_MODEL_PATH)
            pose_estimator = PoseEstimator(
                model_path=POSE_MODEL_PATH,
                confidence=POSE_CONFIDENCE,
                image_size=POSE_IMAGE_SIZE,
            )

        fire_detector = None
        flood_detector = None
        boulder_detector = None

        if ENABLE_FIRE:
            logger.info("Loading fire detector: %s", FIRE_MODEL_PATH)
            fire_detector = HazardDetector(
                model_path=FIRE_MODEL_PATH,
                hazard_type="fire",
                confidence=FIRE_CONFIDENCE,
                image_size=HAZARD_IMAGE_SIZE,
            )

        if ENABLE_FLOOD:
            logger.info("Loading flood detector: %s", FLOOD_MODEL_PATH)
            flood_detector = HazardDetector(
                model_path=FLOOD_MODEL_PATH,
                hazard_type="flood",
                confidence=FLOOD_CONFIDENCE,
                image_size=HAZARD_IMAGE_SIZE,
            )

        if ENABLE_BOULDER:
            logger.info("Loading boulder detector: %s", BOULDER_MODEL_PATH)
            boulder_detector = BoulderDetector(
                model_path=BOULDER_MODEL_PATH,
                confidence=BOULDER_CONFIDENCE,
                image_size=BOULDER_IMAGE_SIZE,
            )

        scheduler = AIScheduler(
            fire_detector=fire_detector,
            flood_detector=flood_detector,
            boulder_detector=boulder_detector,
            fire_interval=FIRE_INTERVAL_FRAMES,
            flood_interval=FLOOD_INTERVAL_FRAMES,
            boulder_interval=BOULDER_INTERVAL_FRAMES,
            fire_rate=FIRE_RATE,
            flood_rate=FLOOD_RATE,
            boulder_rate=BOULDER_RATE,
        )

    risk_engine = RiskEngine(person_score=PERSON_RISK_SCORE) if with_risk else None

    base_pipeline = PerceptionPipeline(
        person_detector=person_detector,
        pose_estimator=pose_estimator,
        scheduler=scheduler,
        risk_engine=risk_engine,
        pose_interval=POSE_INTERVAL_FRAMES,
    )

    pipeline = HardenedPipeline(
        base_pipeline=base_pipeline,
        person_confirm_hits=3,
        person_clear_misses=5,
        event_cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS,
    )

    logger.info(
        "Perception pipeline initialized (Local risk engine: %s)",
        "ENABLED (Debug Mode)" if with_risk else "DISABLED (GCS Authoritative)",
    )
    return pipeline


def extract_detections(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extracts standardized detection objects preserving bboxes, labels, confidences, and track IDs."""
    detections: list[dict[str, Any]] = []

    for index, person in enumerate(result.get("persons", [])):
        bbox = person.get("bbox", [])
        if len(bbox) != 4:
            continue

        confirmed = bool(person.get("confirmed", False))
        detections.append(
            {
                "id": person.get("id", f"person_{index + 1}"),
                "label": person.get("label", "person"),
                "confidence": round(float(person.get("confidence", 0.0)), 3),
                "bbox": [round(float(value), 1) for value in bbox],
                "track_id": person.get("track_id", 1),
                "confirmed": confirmed,
                "severity": "high" if confirmed else "medium",
            }
        )

    hazards = result.get("hazards", {})
    if isinstance(hazards, dict):
        for hazard_type, items in hazards.items():
            for index, item in enumerate(items):
                if isinstance(item, dict):
                    bbox = item.get("bbox", [])
                    confidence = float(item.get("confidence", 0.0))
                else:
                    bbox = getattr(item, "bbox", [])
                    confidence = float(getattr(item, "confidence", 0.0))

                if len(bbox) != 4:
                    continue

                severity = "high" if hazard_type in {"fire", "flood"} else "medium"
                detections.append(
                    {
                        "id": f"{hazard_type}_{index + 1}",
                        "label": hazard_type,
                        "confidence": round(confidence, 3),
                        "bbox": [round(float(value), 1) for value in bbox],
                        "severity": severity,
                    }
                )

    return detections


def build_ai_packet(
    result: dict[str, Any],
    frame_id: int,
    frame_timestamp: float,
    inference_time_ms: float,
    drone_id: str,
    persistent_risk: Any = None,
) -> dict[str, Any]:
    """Builds AI telemetry packet. Risk field is completely omitted in production unless --local-risk is enabled."""
    detections = extract_detections(result)

    packet: dict[str, Any] = {
        "type": "AI_FRAME",
        "source": drone_id,
        "drone_id": drone_id,
        "frame_id": int(frame_id),
        "timestamp": datetime.fromtimestamp(
            frame_timestamp,
            timezone.utc,
        ).isoformat(),
        "inference_time_ms": round(inference_time_ms, 2),
        "inference_fps": round(
            (1000.0 / inference_time_ms) if inference_time_ms > 0 else 0.0,
            2,
        ),
        "detections": detections,
    }

    # Only attach risk field if local risk analysis was explicitly requested
    if persistent_risk is not None:
        packet["risk"] = {
            "level": getattr(persistent_risk, "level", "LOW"),
            "score": round(float(getattr(persistent_risk, "score", 0.0)), 2),
        }

    return packet


def draw_detections(
    image,
    detections: list[dict[str, Any]],
):
    """
    Draws bounding boxes and labels/confidence/track_id onto a copy of the frame.
    DOES NOT draw any risk scores, levels, or risk assessments.
    Format: LABEL XX% #ID (e.g., PERSON 87% #1)
    """
    import cv2

    output = image.copy()
    if not detections:
        return output

    color_map = {
        "person": (0, 255, 0),       # Green
        "rescuer": (255, 255, 0),    # Cyan
        "civilian": (0, 255, 0),     # Green
        "fire": (0, 0, 255),         # Red
        "smoke": (128, 128, 128),    # Gray
        "water": (255, 0, 0),        # Blue
        "flood": (255, 0, 0),        # Blue
        "rock": (42, 42, 165),       # Brown
        "boulder": (42, 42, 165),    # Brown
    }

    for det in detections:
        bbox = det.get("bbox", [])
        if len(bbox) != 4:
            continue

        x1, y1, x2, y2 = map(int, bbox)
        label_name = str(det.get("label", "unknown")).lower()
        color = color_map.get(label_name, (0, 255, 255))

        # 1. Bounding box rectangle
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

        # 2. Label text: e.g. "PERSON 87% #1"
        conf = float(det.get("confidence", 0.0))
        pct = int(round(conf * 100))
        text = f"{label_name.upper()} {pct}%"
        track_id = det.get("track_id")
        if track_id is not None:
            text += f" #{track_id}"

        # 3. Label badge background
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.55
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
        bg_y1 = max(0, y1 - th - baseline - 4)
        bg_y2 = y1
        cv2.rectangle(output, (x1, bg_y1), (x1 + tw + 6, bg_y2), color, -1)

        # Contrast text: dark on bright colors, white on dark
        text_color = (0, 0, 0) if (color[0] + color[1] + color[2]) > 350 else (255, 255, 255)
        cv2.putText(
            output,
            text,
            (x1 + 3, y1 - baseline - 2),
            font,
            scale,
            text_color,
            thickness,
            cv2.LINE_AA,
        )

    return output


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="ELIOS-SAR Onboard Perception Node (Raspberry Pi 5 Production System)"
    )

    parser.add_argument(
        "--source",
        choices=["webcam", "mp4"],
        default="webcam",
        help="Video frame source: webcam (default) or mp4.",
    )

    parser.add_argument(
        "--detector",
        choices=["person", "boulder", "fire", "flood"],
        default=None,
        help="Select a single AI detector to run exclusively: person, boulder, fire, or flood (default: multi-model).",
    )

    parser.add_argument(
        "--camera-id",
        type=int,
        default=None,
        help=f"Webcam device index (default: {CAMERA_DEVICE} from .env).",
    )

    parser.add_argument(
        "--video",
        type=str,
        default="",
        help="MP4 path when --source mp4 is used.",
    )

    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop the MP4 video when it reaches EOF.",
    )

    parser.add_argument(
        "--width",
        type=int,
        default=CAMERA_WIDTH,
        help=f"Camera frame width (default: {CAMERA_WIDTH} from .env).",
    )

    parser.add_argument(
        "--height",
        type=int,
        default=CAMERA_HEIGHT,
        help=f"Camera frame height (default: {CAMERA_HEIGHT} from .env).",
    )

    parser.add_argument(
        "--fps",
        type=float,
        default=CAMERA_FPS,
        help=f"Camera frame rate (default: {CAMERA_FPS} from .env).",
    )

    parser.add_argument(
        "--freshness-timeout",
        type=float,
        default=1.5,
        help="Detection freshness timeout in seconds before cached boxes expire (default: 1.5).",
    )

    parser.add_argument(
        "--gcs-host",
        type=str,
        default=GCS_HOST,
        help=f"GCS IPv4 address (default: {GCS_HOST} from .env).",
    )

    parser.add_argument(
        "--video-port",
        type=int,
        default=VIDEO_PORT,
        help=f"GCS annotated video TCP port (default: {VIDEO_PORT}).",
    )

    parser.add_argument(
        "--ai-port",
        type=int,
        default=AI_PORT,
        help=f"GCS AI telemetry TCP port (default: {AI_PORT}).",
    )

    parser.add_argument(
        "--drone-id",
        type=str,
        default=DRONE_ID,
        help=f"Drone identifier (default: {DRONE_ID}).",
    )

    parser.add_argument(
        "--display",
        action="store_true",
        default=False,
        help="Enable local OpenCV preview window (default: False / Headless).",
    )

    parser.add_argument(
        "--local-risk",
        action="store_true",
        default=False,
        help="Enable onboard risk engine calculation for local debugging (default: False / GCS Authoritative).",
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        default=False,
        help="Run completely offline without connecting to GCS (default: False).",
    )

    return parser.parse_args()


def create_source(args) -> FrameSource:
    if args.source == "webcam":
        device_id = args.camera_id if args.camera_id is not None else int(CAMERA_DEVICE)
        logger.info(
            "Frame source: WEBCAM (/dev/video%s, %dx%d @ %.1f FPS)",
            device_id,
            args.width,
            args.height,
            args.fps,
        )
        return OpenCVCameraSource(
            device=device_id,
            width=args.width,
            height=args.height,
            fps=int(args.fps),
        )

    video_path = args.video
    if not video_path and Path("test.mp4").exists():
        video_path = "test.mp4"

    if not video_path:
        raise ValueError("--video is required when --source mp4 is selected")

    logger.info("Frame source: MP4 (%s)", video_path)
    return MP4Source(
        path=video_path,
        loop=args.loop,
    )


def main() -> int:
    args = parse_arguments()

    logger.info("==================================================")
    logger.info("ELIOS-SAR ONBOARD PERCEPTION (PRODUCTION NODE)")
    logger.info("==================================================")
    logger.info("Drone ID          : %s", args.drone_id)
    logger.info("Source            : %s", args.source.upper())
    logger.info(
        "Detector          : %s",
        f"SINGLE ({args.detector.upper()})" if args.detector else "MULTI-MODEL (All Enabled)",
    )
    logger.info(
        "Mode              : %s",
        "HEADLESS (Production)" if not args.display else "LOCAL DISPLAY PREVIEW",
    )
    logger.info("Pi Video Overlay  : ENABLED (DRAW FIRST -> ENCODE -> SEND)")
    logger.info("Freshness Timeout : %.1fs", args.freshness_timeout)
    logger.info(
        "Local Risk        : %s",
        "ENABLED (Debug Mode)" if args.local_risk else "DISABLED (GCS Authoritative)",
    )
    logger.info(
        "GCS Stream        : %s",
        "DISABLED (--no-stream)"
        if args.no_stream
        else f"{args.gcs_host} (Video TCP: {args.video_port} | AI TCP: {args.ai_port})",
    )
    logger.info("==================================================")

    source = create_source(args)
    pipeline = build_perception_pipeline(
        with_risk=args.local_risk,
        detector=args.detector,
    )

    risk_manager = (
        PersistentRiskState(
            promote_hits=3,
            demote_hits=5,
            smoothing_alpha=0.35,
        )
        if args.local_risk
        else None
    )

    streamer: Optional[GCSTCPStreamer] = None
    if not args.no_stream:
        streamer = GCSTCPStreamer(
            gcs_host=args.gcs_host,
            video_port=args.video_port,
            ai_port=args.ai_port,
            drone_id=args.drone_id,
            jpeg_quality=70,
        )
        streamer.connect(wait=False)
        logger.info("GCS TCP transport started")

    # Detection cache for asynchronous overlay rendering
    cached_state = CachedDetectionState(freshness_timeout=args.freshness_timeout)

    # Queue for submitting frames to background AI inference worker (drop if busy)
    ai_input_queue: queue.Queue = queue.Queue(maxsize=1)
    running = True

    def ai_worker_loop():
        """Background AI inference loop decoupled from video frame capture rate."""
        logger.info("AI inference worker thread started")
        while running:
            try:
                item = ai_input_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if item is None:
                break

            img_for_ai, f_id, f_ts = item

            try:
                inf_start = time.perf_counter()
                pipeline.runtime.frame_id = f_id - 1
                result = pipeline.process(img_for_ai)
                result["frame_id"] = f_id
                inf_ms = (time.perf_counter() - inf_start) * 1000.0

                # Extract detections and update cached state for overlay
                detections = extract_detections(result)
                cached_state.update(detections, f_id)

                # Optional local risk evaluation (Debug only)
                persistent_risk = None
                if args.local_risk and risk_manager is not None:
                    raw_risk = result.get("risk")
                    if raw_risk:
                        raw_level = getattr(raw_risk, "level", None) or (
                            raw_risk.get("level") if isinstance(raw_risk, dict) else "LOW"
                        )
                        raw_score = (
                            getattr(raw_risk, "score", None)
                            if getattr(raw_risk, "score", None) is not None
                            else (raw_risk.get("score", 0.0) if isinstance(raw_risk, dict) else 0.0)
                        )
                        persistent_risk = risk_manager.update(
                            raw_level or "LOW",
                            raw_score or 0.0,
                        )
                    else:
                        persistent_risk = risk_manager.update("LOW", 0.0)

                # Transmit AI metadata packet over TCP port 8766
                if streamer is not None:
                    ai_packet = build_ai_packet(
                        result=result,
                        frame_id=f_id,
                        frame_timestamp=f_ts,
                        inference_time_ms=inf_ms,
                        drone_id=args.drone_id,
                        persistent_risk=persistent_risk,
                    )
                    streamer.send_ai_data(ai_packet)

            except Exception as exc:
                logger.error("Error in AI inference worker: %s", exc)

    ai_thread = threading.Thread(
        target=ai_worker_loop,
        name="ELIOS-AI-Worker",
        daemon=True,
    )
    ai_thread.start()

    processed_frames = 0
    started_at = time.perf_counter()

    try:
        while True:
            frame = source.read()

            if frame is None:
                if args.source == "mp4":
                    logger.info("MP4 playback complete")
                    break

                time.sleep(0.01)
                continue

            processed_frames += 1
            frame_id = frame.frame_id
            capture_ts = frame.timestamp
            t_ms = int(capture_ts * 1000)

            # Submit frame copy to background AI worker if not busy
            try:
                ai_input_queue.put_nowait((frame.image.copy(), frame_id, capture_ts))
            except queue.Full:
                pass  # AI worker is busy on previous frame; keep video flowing smoothly!

            # -------------------------------------------------------------
            # STEP 1: DRAW FIRST
            # Retrieve latest fresh cached detections and draw bounding boxes.
            # Does NOT draw any risk scores, levels, or risk assessments.
            # -------------------------------------------------------------
            active_detections = cached_state.get_fresh_detections()
            if active_detections:
                annotated_frame = draw_detections(frame.image, active_detections)
            else:
                annotated_frame = frame.image

            # -------------------------------------------------------------
            # STEP 2: ENCODE SECOND & STEP 3: SEND THIRD
            # streamer.send_video_frame internally performs:
            #   cv2.imencode(".jpg", annotated_frame)
            # and transmits the JPEG byte stream with ELIO header to TCP 8765.
            # -------------------------------------------------------------
            if streamer is not None:
                streamer.send_video_frame(
                    annotated_frame,
                    frame_id=frame_id,
                    timestamp_ms=t_ms,
                )

            # Local display window (Debug only)
            if args.display:
                import cv2

                preview = annotated_frame.copy()
                cv2.putText(
                    preview,
                    f"ELIOS-SAR | Frame {frame_id} | {args.source.upper()}",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                cv2.imshow("ELIOS-SAR Local Preview", preview)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    logger.info("Stopped by operator")
                    break

            # Periodic logging
            if processed_frames % 30 == 0:
                elapsed = time.perf_counter() - started_at
                fps = (
                    processed_frames / elapsed
                    if elapsed > 0
                    else 0.0
                )
                logger.info(
                    "video_frame=%d fps=%.2f active_boxes=%d",
                    frame_id,
                    fps,
                    len(active_detections),
                )

    except KeyboardInterrupt:
        logger.info("Interrupted by operator")

    finally:
        logger.info("Shutting down ELIOS-SAR production node")
        running = False

        # Terminate AI worker
        try:
            ai_input_queue.put_nowait(None)
        except queue.Full:
            pass

        ai_thread.join(timeout=2.0)
        source.release()

        if streamer is not None:
            streamer.close()

        if args.display:
            try:
                import cv2

                cv2.destroyAllWindows()
            except Exception:
                pass

    elapsed = time.perf_counter() - started_at
    average_fps = (
        processed_frames / elapsed
        if elapsed > 0
        else 0.0
    )

    logger.info("==================================================")
    logger.info("ELIOS-SAR PRODUCTION NODE STOPPED")
    logger.info("Frames processed : %s", processed_frames)
    logger.info("Elapsed          : %.2fs", elapsed)
    logger.info("Average FPS      : %.2f", average_fps)
    logger.info("==================================================")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
