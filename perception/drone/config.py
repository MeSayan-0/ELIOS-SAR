from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


GCS_HOST = os.getenv("GCS_HOST", "127.0.0.1")
VIDEO_PORT = env_int("VIDEO_PORT", env_int("VIDEO_WS_PORT", 8765))
AI_PORT = env_int("AI_PORT", env_int("AI_WS_PORT", 8766))
VIDEO_WS_PORT = VIDEO_PORT
AI_WS_PORT = AI_PORT

VIDEO_WS_URL = f"ws://{GCS_HOST}:{VIDEO_WS_PORT}"
AI_WS_URL = f"ws://{GCS_HOST}:{AI_WS_PORT}"

DRONE_ID = os.getenv("DRONE_ID", "DRONE-01")

CAMERA_DEVICE = os.getenv("CAMERA_DEVICE", "0")
try:
    CAMERA_DEVICE = int(CAMERA_DEVICE)
except ValueError:
    pass

CAMERA_WIDTH = env_int("CAMERA_WIDTH", 640)
CAMERA_HEIGHT = env_int("CAMERA_HEIGHT", 480)
CAMERA_FPS = env_int("CAMERA_FPS", 15)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "models/rgb/rgb_disaster.pt"
)

YOLO_CONFIDENCE = env_float("YOLO_CONFIDENCE", 0.45)

POSE_MODEL_PATH = os.getenv(
    "POSE_MODEL_PATH",
    "models/pose/yolo11n-pose.pt"
)
POSE_CONFIDENCE = env_float("POSE_CONFIDENCE", 0.35)
POSE_IMAGE_SIZE = env_int("POSE_IMAGE_SIZE", 320)
POSE_INTERVAL_FRAMES = env_int("POSE_INTERVAL_FRAMES", 3)

FIRE_MODEL_PATH = os.getenv(
    "FIRE_MODEL_PATH",
    "models/hazards/fire.pt"
)
FLOOD_MODEL_PATH = os.getenv(
    "FLOOD_MODEL_PATH",
    "models/hazards/flood.pt"
)
BOULDER_MODEL_PATH = os.getenv(
    "BOULDER_MODEL_PATH",
    "models/hazards/boulder.pt"
)

FIRE_CONFIDENCE = env_float("FIRE_CONFIDENCE", 0.45)
FLOOD_CONFIDENCE = env_float("FLOOD_CONFIDENCE", 0.45)
BOULDER_CONFIDENCE = env_float("BOULDER_CONFIDENCE", 0.35)

HAZARD_IMAGE_SIZE = env_int("HAZARD_IMAGE_SIZE", 320)
BOULDER_IMAGE_SIZE = env_int("BOULDER_IMAGE_SIZE", 320)

HAZARD_INTERVAL_FRAMES = env_int("HAZARD_INTERVAL_FRAMES", 3)

FIRE_INTERVAL_FRAMES = env_int("FIRE_INTERVAL_FRAMES", 1)
FLOOD_INTERVAL_FRAMES = env_int("FLOOD_INTERVAL_FRAMES", 0)
BOULDER_INTERVAL_FRAMES = env_int("BOULDER_INTERVAL_FRAMES", 2)

FIRE_RATE = env_float("FIRE_RATE", 0.75)
FLOOD_RATE = env_float("FLOOD_RATE", 0.0)
BOULDER_RATE = env_float("BOULDER_RATE", 0.50)

ENABLE_FIRE = env_bool("ENABLE_FIRE", True)
ENABLE_FLOOD = env_bool("ENABLE_FLOOD", False)
ENABLE_BOULDER = env_bool("ENABLE_BOULDER", True)
ENABLE_POSE = env_bool("ENABLE_POSE", True)

PERSON_RISK_SCORE = env_int("PERSON_RISK_SCORE", 10)

RISK_EVENT_COOLDOWN_SECONDS = env_float(
    "RISK_EVENT_COOLDOWN_SECONDS",
    2.0
)
