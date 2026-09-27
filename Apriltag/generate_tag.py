import os
import urllib.request
import cv2
import numpy as np

OUTPUT_DIR = os.path.expanduser("~/elios-apriltag/tags")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_printable_tag(tag_id=0, family="tagStandard41h12", target_size=1200, border_px=150):
    """
    Downloads official tag image from AprilRobotics repository and prepares
    a high-resolution printable PNG with border and label.
    """
    id_str = f"{tag_id:05d}"
    url = f"https://raw.githubusercontent.com/AprilRobotics/apriltag-imgs/master/{family}/tag41_12_{id_str}.png"
    raw_path = os.path.join(OUTPUT_DIR, f"{family}_id{tag_id}_raw.png")
    printable_path = os.path.join(OUTPUT_DIR, f"{family}_id{tag_id}_printable.png")

    print(f"Fetching official tag {family} ID {tag_id} from {url}...")
    urllib.request.urlretrieve(url, raw_path)

    raw_img = cv2.imread(raw_path, cv2.IMREAD_GRAYSCALE)
    if raw_img is None:
        raise RuntimeError(f"Could not load downloaded image from {raw_path}")

    # Upscale using nearest neighbor to keep razor-sharp square edges
    scaled = cv2.resize(raw_img, (target_size, target_size), interpolation=cv2.INTER_NEAREST)

    # Add quiet zone white border
    bordered = cv2.copyMakeBorder(
        scaled,
        border_px, border_px + 80, border_px, border_px,
        cv2.BORDER_CONSTANT,
        value=255
    )

    # Add label text at the bottom
    label = f"AprilTag: {family}  |  ID: {tag_id}  |  ELIOS-SAR Docking Target"
    cv2.putText(
        bordered,
        label,
        (border_px, target_size + border_px + 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (0, 0, 0),
        2
    )

    cv2.imwrite(printable_path, bordered)
    print(f"Printable tag created: {printable_path}")
    return printable_path

if __name__ == "__main__":
    generate_printable_tag(0)
