import cv2

# Use Linux V4L2 directly to prevent GStreamer stalling
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

if not camera.isOpened():
    print("ERROR: Could not open camera")
    exit(1)

# Configure MJPG and resolution
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = camera.get(cv2.CAP_PROP_FPS)

print(f"Camera opened successfully: {width}x{height} @ {fps:.1f} FPS (V4L2)")
print("Press 'q' in the video window to quit.")

while True:
    ret, frame = camera.read()

    if not ret or frame is None:
        print("ERROR: Could not read frame")
        break

    cv2.imshow("ELIOS-SAR Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
