from __future__ import annotations

from pathlib import Path
import argparse
import sys
import time
from datetime import datetime, timezone
from typing import Optional
import cv2
import os

# Ensure project root is in sys.path
FILE_DIR = Path(__file__).resolve().parent
if (FILE_DIR / "src").exists():
    PROJECT_ROOT = FILE_DIR
elif (FILE_DIR.parent / "src").exists():
    PROJECT_ROOT = FILE_DIR.parent
elif (FILE_DIR.parent.parent / "src").exists():
    PROJECT_ROOT = FILE_DIR.parent.parent
else:
    PROJECT_ROOT = FILE_DIR

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    FIRE_RATE,
    FLOOD_RATE,
    BOULDER_RATE,
    ENABLE_FIRE,
    ENABLE_FLOOD,
    ENABLE_BOULDER,
    ENABLE_POSE,
    PERSON_RISK_SCORE,
    RISK_EVENT_COOLDOWN_SECONDS,
    DRONE_ID,
    GCS_HOST,
    VIDEO_PORT,
    AI_PORT,
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
from src.core.safe_emitter import SafeEventEmitter
from src.monitoring.metrics_writer import MetricsWriter
from src.testing.replay_writer import ReplayWriter
from src.communication.telemetry_queue import TelemetryQueue
from src.communication.gcs_streamer import GCSTCPStreamer


def build_pipeline():
    print("[INIT] Loading person detector...")
    person_detector = RGBDetector(
        model_path=MODEL_PATH,
        confidence=YOLO_CONFIDENCE,
    )

    pose_estimator = None
    if ENABLE_POSE:
        print("[INIT] Loading pose estimator...")
        pose_estimator = PoseEstimator(
            model_path=POSE_MODEL_PATH,
            confidence=POSE_CONFIDENCE,
            image_size=POSE_IMAGE_SIZE,
        )

    fire_detector = None
    flood_detector = None
    boulder_detector = None

    if ENABLE_FIRE:
        print("[INIT] Loading fire detector...")
        fire_detector = HazardDetector(
            model_path=FIRE_MODEL_PATH,
            hazard_type="fire",
            confidence=FIRE_CONFIDENCE,
            image_size=HAZARD_IMAGE_SIZE,
        )

    if ENABLE_FLOOD:
        print("[INIT] Loading flood detector...")
        flood_detector = HazardDetector(
            model_path=FLOOD_MODEL_PATH,
            hazard_type="flood",
            confidence=FLOOD_CONFIDENCE,
            image_size=HAZARD_IMAGE_SIZE,
        )

    if ENABLE_BOULDER:
        print("[INIT] Loading boulder detector...")
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

    base_pipeline = PerceptionPipeline(
        person_detector=person_detector,
        pose_estimator=pose_estimator,
        scheduler=scheduler,
        risk_engine=RiskEngine(person_score=PERSON_RISK_SCORE),
        pose_interval=POSE_INTERVAL_FRAMES,
    )

    hardened_pipeline = HardenedPipeline(
        base_pipeline=base_pipeline,
        person_confirm_hits=3,
        person_clear_misses=5,
        event_cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS,
    )

    print("[INIT] Hardened pipeline initialized")
    return hardened_pipeline


def draw_results(frame, result, persistent_risk):
    output = frame.copy()

    for person in result.get("persons", []):
        bbox = person.get("bbox", [])
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            confirmed = person.get("confirmed", False)
            color = (0, 255, 0) if confirmed else (0, 200, 200)

            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            label = f"{person.get('label', 'PERSON').upper()} {person.get('confidence', 0):.2f}"
            if confirmed:
                label += " [CONFIRMED]"

            cv2.putText(
                output,
                label,
                (x1, max(20, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

    hazards = result.get("hazards", {})
    if isinstance(hazards, dict):
        for hazard_type, detections in hazards.items():
            for detection in detections:
                bbox = (
                    detection.get("bbox", [])
                    if isinstance(detection, dict)
                    else getattr(detection, "bbox", [])
                )
                if len(bbox) == 4:
                    x1, y1, x2, y2 = map(int, bbox)
                    cv2.rectangle(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    confidence = float(
                        detection.get("confidence", 0.0)
                        if isinstance(detection, dict)
                        else getattr(detection, "confidence", 0.0)
                    )
                    text = f"{hazard_type.upper()} {confidence:.2f}"
                    cv2.putText(
                        output,
                        text,
                        (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 0, 255),
                        2,
                    )

    if persistent_risk:
        level = getattr(persistent_risk, "level", "LOW")
        score = getattr(persistent_risk, "score", 0.0)
        risk_color = (0, 255, 0)
        if level == "MEDIUM":
            risk_color = (0, 165, 255)
        elif level in ("HIGH", "CRITICAL"):
            risk_color = (0, 0, 255)

        cv2.putText(
            output,
            f"RISK: {level} | SCORE: {score:.2f}",
            (20, output.shape[0] - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            risk_color,
            2,
        )

    cv2.putText(
        output,
        f"Frame: {result.get('frame_id', 0)}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        output,
        f"Inference: {result.get('inference_ms', 0.0):.1f} ms",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )

    return output


def extract_detections_for_gcs(result: dict) -> list[dict]:
    """Formats detections into standard GCS detectionNormalizer schema."""
    detections = []

    for person in result.get("persons", []):
        bbox = person.get("bbox", [])
        if len(bbox) == 4:
            detections.append({
                "id": person.get("id", f"person_{len(detections) + 1}"),
                "label": person.get("label", "person"),
                "confidence": round(float(person.get("confidence", 0.0)), 2),
                "bbox": [round(float(c), 1) for c in bbox],
                "track_id": person.get("track_id", 1),
                "severity": "high" if person.get("confirmed") else "medium",
            })

    hazards = result.get("hazards", {})
    if isinstance(hazards, dict):
        for hazard_type, items in hazards.items():
            for item in items:
                bbox = (
                    item.get("bbox", [])
                    if isinstance(item, dict)
                    else getattr(item, "bbox", [])
                )
                conf = float(
                    item.get("confidence", 0.0)
                    if isinstance(item, dict)
                    else getattr(item, "confidence", 0.0)
                )
                if len(bbox) == 4:
                    detections.append({
                        "id": f"{hazard_type}_{len(detections) + 1}",
                        "label": hazard_type,
                        "confidence": round(conf, 2),
                        "bbox": [round(float(c), 1) for c in bbox],
                        "severity": "high" if hazard_type in ("fire", "flood") else "medium",
                    })

    return detections


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="ELIOS-SAR Webcam Pipeline with Real-Time GCS TCP Video and AI Telemetry Streaming"
    )
    parser.add_argument(
        "--camera-id",
        type=int,
        default=0,
        help="Webcam device index (default: 0 for /dev/video0)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Requested webcam frame width (default: 1280)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Requested webcam frame height (default: 720)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=20.0,
        help="Target processing / recording FPS (default: 20.0)",
    )
    parser.add_argument(
        "--gcs-host",
        type=str,
        default=GCS_HOST,
        help=f"GCS computer Wi-Fi IP address (default: {GCS_HOST})",
    )
    parser.add_argument(
        "--video-port",
        type=int,
        default=VIDEO_PORT,
        help=f"GCS Video TCP port (default: {VIDEO_PORT})",
    )
    parser.add_argument(
        "--ai-port",
        type=int,
        default=AI_PORT,
        help=f"GCS AI TCP port (default: {AI_PORT})",
    )
    parser.add_argument(
        "--drone-id",
        type=str,
        default=DRONE_ID,
        help=f"Drone identifier (default: {DRONE_ID})",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable TCP streaming to GCS (run in offline mode)",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable GUI preview window (cv2.imshow) for headless/SSH execution",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    camera_id = args.camera_id
    output_path = PROJECT_ROOT / "recordings" / "test_webcam_output.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("ELIOS-SAR WEBCAM FULL PIPELINE & GCS STREAMER")
    print("=" * 70)
    print(f"[CAMERA] Device: /dev/video{camera_id}")
    print(f"[VIDEO]  Output: {output_path}")
    print(f"[GCS]    Target: {args.gcs_host} (Video: {args.video_port} TCP | AI: {args.ai_port} TCP)")
    print(f"[DRONE]  ID    : {args.drone_id}")
    print("=" * 70)

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"[ERROR] Could not open webcam /dev/video{camera_id}")
        return 1

    if args.width or args.height:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        if args.width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        if args.height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_fps = args.fps

    print(f"[CAMERA] Resolution: {width}x{height}")
    print(f"[CAMERA] Output FPS: {source_fps:.1f}")

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        source_fps,
        (width, height),
    )

    if not writer.isOpened():
        print("[ERROR] Could not create output video writer")
        cap.release()
        return 1

    pipeline = build_pipeline()

    risk_manager = PersistentRiskState(
        promote_hits=3,
        demote_hits=5,
        smoothing_alpha=0.35,
    )

    def event_logger(event):
        print(
            f"[EVENT] {event.get('event_type')} "
            f"{event.get('payload', {})}"
        )

    telemetry_queue = TelemetryQueue(
        sender=event_logger,
        max_size=100,
    )
    telemetry_queue.start()

    emitter = SafeEventEmitter(
        sender=lambda event: telemetry_queue.put(event),
        cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS,
    )

    # Initialize GCS TCP Streamer
    streamer: Optional[GCSTCPStreamer] = None
    if not args.no_stream:
        print(f"\n[STREAM] Initializing TCP connection to GCS at {args.gcs_host}...")
        streamer = GCSTCPStreamer(
            gcs_host=args.gcs_host,
            video_port=args.video_port,
            ai_port=args.ai_port,
            drone_id=args.drone_id,
            jpeg_quality=70,
        )
        streamer.connect(wait=False)

    metrics_writer = MetricsWriter(path=str(PROJECT_ROOT / "logs" / "webcam_metrics.jsonl"))
    replay_writer = ReplayWriter(path=str(PROJECT_ROOT / "recordings" / "webcam_replay.jsonl"))

    frame_count = 0
    start_time = time.perf_counter()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[WARNING] Failed to grab frame from webcam")
                break

            frame_count += 1
            frame_start = time.perf_counter()

            # 1. Run perception pipeline (Person, Pose, Hazards)
            result = pipeline.process(frame)

            # 2. Risk evaluation
            raw_risk = result.get("risk")
            if raw_risk:
                level = getattr(raw_risk, "level", None) or (
                    raw_risk.get("level") if isinstance(raw_risk, dict) else "LOW"
                )
                score = getattr(raw_risk, "score", None) if getattr(raw_risk, "score", None) is not None else (
                    raw_risk.get("score", 0.0) if isinstance(raw_risk, dict) else 0.0
                )
                persistent_risk = risk_manager.update(level or "LOW", score or 0.0)
            else:
                persistent_risk = risk_manager.update("LOW", 0.0)

            result["persistent_risk"] = risk_manager.snapshot()
            confirmed_persons = result.get("confirmed_persons", [])

            # 3. Emit confirmed person events
            for person in confirmed_persons:
                conf = float(
                    person.get("confidence", 0.0)
                    if isinstance(person, dict)
                    else getattr(person, "confidence", 0.0)
                )
                bbox = (
                    person.get("bbox", [])
                    if isinstance(person, dict)
                    else getattr(person, "bbox", [])
                )
                emitter.emit(
                    event_type="person_detected",
                    source="person_model",
                    drone_id=args.drone_id,
                    confidence=conf,
                    bbox=bbox,
                )

            # 4. Emit hazard events
            hazards = result.get("hazards", {})
            if isinstance(hazards, dict):
                for hazard_type, detections in hazards.items():
                    for detection in detections:
                        if isinstance(detection, dict):
                            payload = detection.copy()
                            payload.pop("mask", None)
                        else:
                            payload = {
                                k: v
                                for k, v in vars(detection).items()
                                if k != "mask"
                            }

                        if hazard_type == "boulder":
                            event_type = "obstruction_detected"
                            source = "boulder_segmentation"
                        elif hazard_type == "flood":
                            event_type = "flood_detected"
                            source = "flood_segmentation"
                        elif hazard_type == "fire":
                            event_type = "fire_detected"
                            source = "fire_model"
                        else:
                            event_type = f"{hazard_type}_detected"
                            source = f"{hazard_type}_model"

                        emitter.emit(
                            event_type=event_type,
                            source=source,
                            drone_id=args.drone_id,
                            **payload,
                        )

            frame_id = result.get("frame_id", frame_count)
            replay_writer.write(frame_id, result)

            # 5. Annotate frame
            annotated = draw_results(frame, result, persistent_risk)
            writer.write(annotated)

            inf_ms = (time.perf_counter() - frame_start) * 1000.0
            elapsed = time.perf_counter() - start_time
            current_fps = frame_count / elapsed if elapsed > 0 else 0.0

            # 6. Stream to GCS over Raw TCP (Video + AI readings)
            if streamer is not None:
                # Send Video frame as JPEG over TCP port 8765
                streamer.send_video_frame(annotated)

                # Format and send AI metadata over TCP port 8766
                gcs_detections = extract_detections_for_gcs(result)
                ai_packet = {
                    "source": args.drone_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "frame_id": frame_id,
                    "inference_time_ms": round(inf_ms, 1),
                    "inference_fps": round(current_fps, 1),
                    "detections": gcs_detections,
                    "risk": {
                        "level": getattr(persistent_risk, "level", "LOW"),
                        "score": round(float(getattr(persistent_risk, "score", 0.0)), 2),
                    },
                }
                streamer.send_ai_data(ai_packet)

            # 7. Periodic logging
            if frame_count % 15 == 0:
                metrics_writer.write({
                    "frame_id": frame_id,
                    "fps": current_fps,
                    "inference_ms": inf_ms,
                    "risk_level": persistent_risk.level,
                    "risk_score": persistent_risk.score,
                    "person_count": len(result.get("persons", [])),
                    "confirmed_person_count": len(confirmed_persons),
                    "queue_size": telemetry_queue.queue.qsize(),
                })

            if not args.no_display:
                cv2.imshow("ELIOS-SAR Webcam Full Pipeline Test", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    print("[INFO] Stopped by user")
                    break

            if frame_count % 30 == 0:
                print(
                    f"[PROGRESS] Frames={frame_count} "
                    f"FPS={current_fps:.2f} "
                    f"Persons={len(result.get('persons', []))} "
                    f"Confirmed={len(confirmed_persons)} "
                    f"Risk={persistent_risk.level}"
                )

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user")

    finally:
        if streamer is not None:
            streamer.close()

        cap.release()
        writer.release()
        if not args.no_display:
            cv2.destroyAllWindows()

        try:
            telemetry_queue.stop()
        except Exception:
            pass

        elapsed = time.perf_counter() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0.0

        print()
        print("=" * 70)
        print("WEBCAM FULL PIPELINE TEST COMPLETE")
        print("=" * 70)
        print(f"Frames processed: {frame_count}")
        print(f"Elapsed time: {elapsed:.2f}s")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Output: {output_path}")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
