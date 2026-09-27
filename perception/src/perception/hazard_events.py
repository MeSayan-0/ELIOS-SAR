from datetime import datetime, timezone


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def build_detection_events(
    drone_id: str,
    result: dict
) -> list[dict]:
    events = []

    for person in result.get("persons", []):
        events.append({
            "event_type": "person_detected",
            "source": "person_model",
            "drone_id": drone_id,
            "confidence": round(
                float(person.get("confidence", 0.0)),
                4
            ),
            "bbox": person.get("bbox", []),
            "timestamp": utc_timestamp()
        })

    for pose in result.get("poses", []):
        events.append({
            "event_type": "person_posture",
            "source": "pose_model",
            "drone_id": drone_id,
            "posture": pose.get("posture", "unknown"),
            "confidence": pose.get("confidence", 0.0),
            "bbox": pose.get("bbox", []),
            "timestamp": utc_timestamp()
        })

    hazards = result.get("hazards", {})

    for hazard_type, detections in hazards.items():
        for detection in detections:
            if hazard_type == "boulder":
                events.append({
                    "event_type": "obstruction_detected",
                    "source": "boulder_segmentation",
                    "drone_id": drone_id,
                    **detection,
                    "timestamp": utc_timestamp()
                })
            else:
                events.append({
                    "event_type": f"{hazard_type}_detected",
                    "source": f"{hazard_type}_model",
                    "drone_id": drone_id,
                    **detection,
                    "timestamp": utc_timestamp()
                })

    risk = result.get("risk")

    if risk:
        events.append({
            "event_type": "risk_update",
            "source": "risk_engine",
            "drone_id": drone_id,
            **risk,
            "timestamp": utc_timestamp()
        })

    return events
