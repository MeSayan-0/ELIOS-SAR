import os
import cv2

OUTPUT_DIR = os.path.expanduser("~/Desktop/elios-apriltag/calibration/calibration_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHECKERBOARD = (9, 6)

def draw_hud_text(img, text, pos, scale=0.7, text_color=(0, 0, 0), outline_color=(255, 255, 255)):
    x, y = pos
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, outline_color, 4, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, text_color, 2, cv2.LINE_AA)

def main():
    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not camera.isOpened():
        print("ERROR: Could not open camera with V4L2 backend")
        exit(1)

    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    count = 0
    print()
    print("=" * 55)
    print("Camera Calibration Image Capture")
    print("=" * 55)
    print("Point camera at the 9x6 checkerboard from various angles.")
    print("SPACE = Capture image | Q = Quit")
    print(f"Saving to: {OUTPUT_DIR}")
    print()

    while True:
        ret, frame = camera.read()

        if not ret or frame is None:
            print("ERROR: Could not read frame")
            break

        display = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Quick corner detection preview
        found, corners = cv2.findChessboardCorners(
            gray,
            CHECKERBOARD,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if found:
            cv2.drawChessboardCorners(display, CHECKERBOARD, corners, found)
            status_text = "Status: Checkerboard DETECTED (Press SPACE)"
            status_color = (0, 150, 0)
        else:
            status_text = "Status: Searching for 9x6 checkerboard..."
            status_color = (0, 0, 180)

        # High-contrast HUD
        draw_hud_text(display, f"Captured Images: {count} / 25 target", (20, 40), scale=0.8, text_color=(0, 0, 0))
        draw_hud_text(display, "SPACE = Capture  |  Q = Quit", (20, 75), scale=0.7, text_color=(0, 0, 0))
        draw_hud_text(display, status_text, (20, 110), scale=0.65, text_color=status_color)

        cv2.imshow("ELIOS-SAR Calibration Capture", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == 32:  # SPACE
            filename = os.path.join(OUTPUT_DIR, f"image_{count:02d}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename} {'(Board Detected)' if found else '(Board not found in preview)'}")
            count += 1
            # Visual capture confirmation flash
            display[:] = display // 2 + 100
            draw_hud_text(display, f"SAVED: image_{count-1:02d}.jpg", (w // 2 - 200 if 'w' in locals() else 350, 360), scale=1.1, text_color=(0, 200, 0))
            cv2.imshow("ELIOS-SAR Calibration Capture", display)
            cv2.waitKey(200)

    camera.release()
    cv2.destroyAllWindows()
    print(f"\nFinished. Total captured: {count} images in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
