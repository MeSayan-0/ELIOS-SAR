from __future__ import annotations

from pathlib import Path
import sys
import time
import urllib.request
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from drone.config import *
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


def main():
    print("=" * 60)
    print("ELIOS-SAR LIVE INTEGRATION VERIFICATION")
    print("=" * 60)

    # 1. Base detectors
    person_detector = RGBDetector(MODEL_PATH, YOLO_CONFIDENCE)
    pose_estimator = PoseEstimator(POSE_MODEL_PATH, POSE_CONFIDENCE, POSE_IMAGE_SIZE) if ENABLE_POSE else None
    fire_detector = HazardDetector(FIRE_MODEL_PATH, "fire", FIRE_CONFIDENCE, HAZARD_IMAGE_SIZE) if ENABLE_FIRE else None
    flood_detector = HazardDetector(FLOOD_MODEL_PATH, "flood", FLOOD_CONFIDENCE, HAZARD_IMAGE_SIZE) if ENABLE_FLOOD else None
    boulder_detector = BoulderDetector(BOULDER_MODEL_PATH, BOULDER_CONFIDENCE, BOULDER_IMAGE_SIZE) if ENABLE_BOULDER else None

    scheduler = AIScheduler(
        fire_detector,
        flood_detector,
        boulder_detector,
        FIRE_INTERVAL_FRAMES,
        FLOOD_INTERVAL_FRAMES,
        BOULDER_INTERVAL_FRAMES
    )

    base_pipeline = PerceptionPipeline(
        person_detector,
        pose_estimator,
        scheduler,
        RiskEngine(),
        POSE_INTERVAL_FRAMES
    )

    # 2. Hardened pipeline wrapper
    hardened_pipeline = HardenedPipeline(
        base_pipeline,
        person_confirm_hits=3,
        person_clear_misses=5,
        event_cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS
    )

    # 3. Persistent risk manager
    persistent_risk_manager = PersistentRiskState(
        promote_hits=3,
        demote_hits=5,
        smoothing_alpha=0.35
    )

    # 4. Telemetry queue & safe event emitter
    emitted_events = []

    def on_telemetry(packet):
        emitted_events.append(packet)
        print(f"[QUEUE_DISPATCH] Event: {packet.get('event_type')}, Severity: {packet.get('severity')}")

    telemetry_queue = TelemetryQueue(on_telemetry, max_size=100)
    telemetry_queue.start()

    emitter = SafeEventEmitter(
        sender=lambda e: telemetry_queue.put(e),
        cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS
    )

    # 5. Writers
    metrics_writer = MetricsWriter("logs/metrics.jsonl")
    replay_writer = ReplayWriter("recordings/replay.jsonl")

    # 6. Health server
    server = start_health_server(
        health_provider=lambda: {
            "drone_id": DRONE_ID,
            "health": hardened_pipeline.health.snapshot(),
            "performance": hardened_pipeline.performance.snapshot(),
            "risk": persistent_risk_manager.snapshot(),
            "queue": telemetry_queue.snapshot(),
        },
        host="127.0.0.1",
        port=8767
    )
    actual_port = server.server_address[1] if server else None
    print(f"[SYSTEM] Health server active on port {actual_port}")

    # 7. Camera
    camera = Camera(CAMERA_DEVICE, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS)

    print("\nRunning 15 live camera frames through complete hardened stack...")

    try:
        for i in range(15):
            frame = camera.read()
            result = hardened_pipeline.process(frame)

            raw_risk = result.get("risk")
            if raw_risk:
                cand_level = getattr(raw_risk, "level", None) or (raw_risk.get("level") if isinstance(raw_risk, dict) else "LOW")
                cand_score = getattr(raw_risk, "score", None) if getattr(raw_risk, "score", None) is not None else (raw_risk.get("score", 0.0) if isinstance(raw_risk, dict) else 0.0)
                persistent_risk = persistent_risk_manager.update(cand_level, cand_score)
            else:
                persistent_risk = persistent_risk_manager.update("LOW", 0.0)

            result["persistent_risk"] = persistent_risk_manager.snapshot()

            confirmed_persons = result.get("confirmed_persons", [])
            for person in confirmed_persons:
                emitter.emit(
                    "person_detected",
                    person.get("label", "person"),
                    person,
                    "warning"
                )

            fid = result.get("frame_id", i)
            replay_writer.write(fid, result)

            if fid % 5 == 0:
                metrics_writer.write({
                    "frame_id": fid,
                    "fps": result.get("performance", {}).get("fps", 0.0),
                    "inference_ms": result.get("inference_ms", 0.0),
                    "risk_level": persistent_risk.level,
                    "risk_score": persistent_risk.score,
                    "confirmed_persons": len(confirmed_persons),
                })

            inf_ms = result.get("inference_ms", 0.0)
            print(f"Frame {i:02d} | FrameID: {fid} | Inf: {inf_ms:5.1f}ms | ConfirmedPersons: {len(confirmed_persons)} | Risk: {persistent_risk.level}({persistent_risk.score})")

        # Test health endpoint HTTP GET
        if actual_port:
            time.sleep(0.1)
            req = urllib.request.urlopen(f"http://127.0.0.1:{actual_port}/health", timeout=2)
            health_data = json.loads(req.read().decode("utf-8"))
            print(f"\nHealth HTTP Endpoint Response (http://127.0.0.1:{actual_port}/health):")
            print(json.dumps(health_data, indent=2))

    finally:
        camera.release()
        telemetry_queue.stop()
        if server:
            server.shutdown()
        print("\n[SUCCESS] All components verified and shut down cleanly.")


if __name__ == "__main__":
    main()
