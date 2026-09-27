from __future__ import annotations

from pathlib import Path
import os
import signal
import sys
import threading
import time
import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from drone.config import (
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
    ENABLE_FIRE,
    ENABLE_FLOOD,
    ENABLE_BOULDER,
    ENABLE_POSE,
    DRONE_ID,
    CAMERA_DEVICE,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    RISK_EVENT_COOLDOWN_SECONDS
)

from src.perception.camera import Camera
from src.perception.rgb_detector import RGBDetector
from src.perception.pose_estimator import PoseEstimator
from src.perception.hazard_detector import HazardDetector
from src.perception.boulder_detector import BoulderDetector
from src.perception.ai_scheduler import AIScheduler
from src.perception.risk_engine import RiskEngine
from src.perception.perception_pipeline import PerceptionPipeline
from src.perception.hardened_pipeline import HardenedPipeline
from src.core.risk_state import PersistentRiskState
from src.core.safe_emitter import SafeEventEmitter
from src.monitoring.metrics_writer import MetricsWriter
from src.testing.replay_writer import ReplayWriter
from src.communication.telemetry_queue import TelemetryQueue
from apps.health_server import start_health_server

shutdown_event = threading.Event()


def handle_shutdown(signum, frame):
    print("\n[SYSTEM] Shutdown signal received. Stopping cleanly...")
    shutdown_event.set()


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def draw_results(frame, result, persistent_risk=None):
    # Draw persons
    for person in result.get("persons", []):
        bbox = person.get("bbox", [0, 0, 0, 0])
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            confirmed = person.get("confirmed", False)
            color = (0, 255, 0) if confirmed else (0, 200, 200)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{person.get('label', 'PERSON').upper()} {person.get('confidence', 0):.2f}"
            if confirmed:
                label += " [CONFIRMED]"

            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2
            )

    # Draw poses
    for pose in result.get("poses", []):
        cv2.putText(
            frame,
            f"POSTURE: {pose.get('posture', 'unknown').upper()}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 0),
            2
        )

    # Draw hazards
    hazards = result.get("hazards", {})
    if isinstance(hazards, dict):
        for hazard_type, detections in hazards.items():
            for detection in detections:
                bbox = detection.get("bbox", [])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = map(int, bbox)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    text = f"{hazard_type.upper()} {detection.get('confidence', 0):.2f}"
                    if hazard_type == "boulder":
                        text += f" {detection.get('obstruction_level', 'low').upper()}"

                    cv2.putText(
                        frame,
                        text,
                        (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 0, 255),
                        2
                    )

    # Draw persistent risk
    risk_info = persistent_risk if persistent_risk else result.get("risk")
    if risk_info:
        level = getattr(risk_info, "level", None) or (risk_info.get("level") if isinstance(risk_info, dict) else "LOW")
        score = getattr(risk_info, "score", None) if getattr(risk_info, "score", None) is not None else (risk_info.get("score", 0) if isinstance(risk_info, dict) else 0)

        risk_color = (0, 255, 0)
        if level in ("HIGH", "CRITICAL"):
            risk_color = (0, 0, 255)
        elif level == "MEDIUM":
            risk_color = (0, 165, 255)

        cv2.putText(
            frame,
            f"RISK: {level.upper()} | SCORE: {score}",
            (20, frame.shape[0] - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            risk_color,
            2
        )

    # Draw FPS & Performance
    perf = result.get("performance", {})
    fps = perf.get("fps", 0.0)
    inf_ms = result.get("inference_ms", 0.0)
    cv2.putText(
        frame,
        f"FPS: {fps:.1f} | INFERENCE: {inf_ms:.1f}ms",
        (frame.shape[1] - 280, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    return frame


def main():
    print("=" * 60)
    print("ELIOS-SAR HARDENED LIVE UNIFIED AI PIPELINE")
    print("=" * 60)

    # 1. Initialize base detectors
    person_detector = RGBDetector(
        model_path=MODEL_PATH,
        confidence=YOLO_CONFIDENCE
    )

    pose_estimator = None
    if ENABLE_POSE:
        pose_estimator = PoseEstimator(
            model_path=POSE_MODEL_PATH,
            confidence=POSE_CONFIDENCE,
            image_size=POSE_IMAGE_SIZE
        )

    fire_detector = None
    flood_detector = None
    boulder_detector = None

    if ENABLE_FIRE:
        fire_detector = HazardDetector(
            model_path=FIRE_MODEL_PATH,
            hazard_type="fire",
            confidence=FIRE_CONFIDENCE,
            image_size=HAZARD_IMAGE_SIZE
        )

    if ENABLE_FLOOD:
        flood_detector = HazardDetector(
            model_path=FLOOD_MODEL_PATH,
            hazard_type="flood",
            confidence=FLOOD_CONFIDENCE,
            image_size=HAZARD_IMAGE_SIZE
        )

    if ENABLE_BOULDER:
        boulder_detector = BoulderDetector(
            model_path=BOULDER_MODEL_PATH,
            confidence=BOULDER_CONFIDENCE,
            image_size=BOULDER_IMAGE_SIZE
        )

    scheduler = AIScheduler(
        fire_detector=fire_detector,
        flood_detector=flood_detector,
        boulder_detector=boulder_detector,
        fire_interval=FIRE_INTERVAL_FRAMES,
        flood_interval=FLOOD_INTERVAL_FRAMES,
        boulder_interval=BOULDER_INTERVAL_FRAMES
    )

    base_pipeline = PerceptionPipeline(
        person_detector=person_detector,
        pose_estimator=pose_estimator,
        scheduler=scheduler,
        risk_engine=RiskEngine(),
        pose_interval=POSE_INTERVAL_FRAMES
    )

    # 2. Wrap inside HardenedPipeline (Timing, Health, Confirmation, Error Isolation)
    hardened_pipeline = HardenedPipeline(
        base_pipeline=base_pipeline,
        person_confirm_hits=3,
        person_clear_misses=5,
        event_cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS
    )

    # 3. Persistent Risk State Machine (Hysteresis & Smoothing)
    persistent_risk_manager = PersistentRiskState(
        promote_hits=3,
        demote_hits=5,
        smoothing_alpha=0.35
    )

    # 4. Telemetry Queue & Safe Event Emitter
    def network_sender(event_payload):
        # Dispatched to GCS/WebSocket or internal telemetry log
        print(f"[EVENT] [{event_payload.get('severity', 'INFO').upper()}] {event_payload.get('event_type')}: {event_payload.get('payload', {})}")

    telemetry_queue = TelemetryQueue(sender=network_sender, max_size=100)
    telemetry_queue.start()

    emitter = SafeEventEmitter(
        sender=lambda event: telemetry_queue.put(event),
        cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS
    )

    # 5. Metrics & Replay Writers
    metrics_writer = MetricsWriter(path="logs/metrics.jsonl")
    replay_writer = ReplayWriter(path="recordings/replay.jsonl")

    # 6. Start HTTP Health Server on localhost:8080 (or fallback)
    health_server = None
    try:
        health_server = start_health_server(
            health_provider=lambda: {
                "drone_id": DRONE_ID,
                "status": "online",
                "health": hardened_pipeline.health.snapshot(),
                "performance": hardened_pipeline.performance.snapshot(),
                "runtime": hardened_pipeline.runtime.snapshot(),
                "risk": persistent_risk_manager.snapshot(),
                "queue": telemetry_queue.snapshot(),
            },
            host="127.0.0.1",
            port=8080
        )
        print("[SYSTEM] Health endpoint active at http://127.0.0.1:8080/health")
    except Exception as exc:
        print(f"[WARN] Could not start health endpoint: {exc}")

    # 7. Initialize Camera
    camera = Camera(
        device=CAMERA_DEVICE,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        fps=CAMERA_FPS
    )

    print("[SYSTEM] Pipeline ready. Press 'q' in video window or Ctrl+C in console to exit.\n")

    try:
        while not shutdown_event.is_set():
            frame = camera.read()

            if frame is None:
                hardened_pipeline.health.mark_frame(False)
                time.sleep(0.01)
                continue

            # Process through hardened pipeline
            result = hardened_pipeline.process(frame)

            # Update persistent risk state
            raw_risk = result.get("risk")
            if raw_risk:
                candidate_level = getattr(raw_risk, "level", None) or (raw_risk.get("level") if isinstance(raw_risk, dict) else "LOW")
                candidate_score = getattr(raw_risk, "score", None) if getattr(raw_risk, "score", None) is not None else (raw_risk.get("score", 0.0) if isinstance(raw_risk, dict) else 0.0)
                persistent_risk = persistent_risk_manager.update(candidate_level, candidate_score)
            else:
                persistent_risk = persistent_risk_manager.update("LOW", 0.0)

            result["persistent_risk"] = persistent_risk_manager.snapshot()

            # Emit confirmed events
            confirmed_persons = result.get("confirmed_persons", [])
            for person in confirmed_persons:
                emitter.emit(
                    event_type="person_detected",
                    identity=str(person.get("track_id", person.get("label", "person"))),
                    payload=person,
                    severity="warning"
                )

            # Record replay and metrics
            frame_id = result.get("frame_id", 0)
            replay_writer.write(frame_id, result)

            if frame_id % 15 == 0:
                metrics_writer.write({
                    "frame_id": frame_id,
                    "fps": result.get("performance", {}).get("fps", 0.0),
                    "inference_ms": result.get("inference_ms", 0.0),
                    "health": result.get("health", {}),
                    "risk_level": persistent_risk.level,
                    "risk_score": persistent_risk.score,
                    "person_count": len(result.get("persons", [])),
                    "confirmed_person_count": len(confirmed_persons),
                    "queue_size": telemetry_queue.queue.qsize()
                })

            # Render visualization
            annotated = draw_results(frame, result, persistent_risk)
            cv2.imshow("ELIOS Unified AI", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    finally:
        print("\n[SYSTEM] Shutting down and releasing resources...")
        shutdown_event.set()

        try:
            camera.release()
        except Exception:
            pass

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

        try:
            telemetry_queue.stop()
        except Exception:
            pass

        print("[SYSTEM] ELIOS-SAR stopped cleanly.")


if __name__ == "__main__":
    main()
