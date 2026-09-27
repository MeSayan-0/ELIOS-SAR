"""Print the actual metadata embedded in an ELIOS-SAR RGB YOLO checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.perception.rgb_detector import RGBDetector


DEFAULT_MODEL_PATH = Path("models/rgb/rgb_disaster.pt")


def describe_model(model_path: str | Path) -> RGBDetector:
    """Load an RGB model, print its metadata, and return its adapter."""
    detector = RGBDetector(model_path)
    class_names = detector.get_class_names()

    print(f"Model: {detector.model_path}")
    print("Model loaded: YES")
    print(f"Model task: {getattr(detector.model, 'task', 'unknown')}")
    print(f"Number of classes: {len(class_names)}")
    print("Classes:")
    for class_id, class_name in class_names.items():
        print(f"{class_id}: {class_name}")

    return detector


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", nargs="?", default=DEFAULT_MODEL_PATH)
    args = parser.parse_args()
    describe_model(args.model_path)


if __name__ == "__main__":
    main()
