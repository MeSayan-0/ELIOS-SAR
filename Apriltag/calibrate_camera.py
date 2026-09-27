import os
import glob
import cv2
import numpy as np

# -----------------------------------------
# Configuration
# -----------------------------------------
CHECKERBOARD = (9, 6)
SQUARE_SIZE_METERS = 0.025  # 25 mm per square (for metric scale reference)

BASE_DIR = os.path.expanduser("~/Desktop/elios-apriltag")
IMAGE_DIR = os.path.join(BASE_DIR, "calibration/calibration_images")
OUTPUT_FILE = os.path.join(BASE_DIR, "calibration/camera_calibration.npz")

def main():
    print("=" * 60)
    print("ELIOS-SAR Camera Calibration")
    print("=" * 60)

    # Prepare checkerboard 3D world coordinates
    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
    objp = objp * SQUARE_SIZE_METERS

    object_points = []
    image_points = []

    images = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.jpg")))

    if len(images) == 0:
        print(f"ERROR: No calibration images found in {IMAGE_DIR}")
        print("Run 'python calibration/capture_calibration.py' to capture 20-30 images first.")
        return False

    print(f"Found {len(images)} images in {IMAGE_DIR}. Detecting corners...")

    image_size = None
    success_count = 0

    for i, filename in enumerate(images):
        image = cv2.imread(filename)
        if image is None:
            print(f"[{i+1}/{len(images)}] Failed to load: {os.path.basename(filename)}")
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image_size = gray.shape[::-1]

        found, corners = cv2.findChessboardCorners(
            gray,
            CHECKERBOARD,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if found:
            object_points.append(objp)
            refined = cv2.cornerSubPix(
                gray,
                corners,
                (11, 11),
                (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )
            image_points.append(refined)
            success_count += 1
            print(f"[{i+1}/{len(images)}] OK: {os.path.basename(filename)}")
        else:
            print(f"[{i+1}/{len(images)}] FAILED (corners not clear): {os.path.basename(filename)}")

    print("-" * 60)
    print(f"Successfully processed {success_count} / {len(images)} images.")

    if success_count < 10:
        print("ERROR: Fewer than 10 valid images. Capture more images with varied angles and distances.")
        return False

    print("Computing camera calibration matrices...")
    ret, camera_matrix, distortion, rvecs, tvecs = cv2.calibrateCamera(
        object_points,
        image_points,
        image_size,
        None,
        None
    )

    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]

    print()
    print("=" * 60)
    print("CALIBRATION RESULTS")
    print("=" * 60)
    print(f"Reprojection Error (RMS): {ret:.4f} pixels  (Ideal: < 0.5 px)")
    print()
    print("Camera Intrinsics Matrix K:")
    print(camera_matrix)
    print()
    print(f"fx = {fx:.3f}")
    print(f"fy = {fy:.3f}")
    print(f"cx = {cx:.3f}")
    print(f"cy = {cy:.3f}")
    print()
    print("Distortion Coefficients [k1, k2, p1, p2, k3]:")
    print(distortion.ravel())
    print()

    # Save calibration file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    np.savez(
        OUTPUT_FILE,
        camera_matrix=camera_matrix,
        distortion=distortion,
        image_width=image_size[0],
        image_height=image_size[1],
        reprojection_error=ret
    )
    print(f"Calibration successfully saved to:\n  {OUTPUT_FILE}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    main()
