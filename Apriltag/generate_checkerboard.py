import os
import cv2
import numpy as np

OUTPUT_DIR = os.path.expanduser("~/Desktop/elios-apriltag/calibration")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_checkerboard(cols=9, rows=6, square_size_px=140, border_px=120):
    """
    Generates a calibration chessboard with (cols, rows) inner corners.
    Inner corners: cols x rows = 9 x 6.
    Number of squares: (cols + 1) x (rows + 1) = 10 x 7 squares.
    """
    num_squares_x = cols + 1
    num_squares_y = rows + 1

    board_w = num_squares_x * square_size_px
    board_h = num_squares_y * square_size_px

    # Create white canvas with border (quiet zone)
    total_w = board_w + 2 * border_px
    total_h = board_h + 2 * border_px + 80  # extra room for label
    img = np.ones((total_h, total_w), dtype=np.uint8) * 255

    for y in range(num_squares_y):
        for x in range(num_squares_x):
            if (x + y) % 2 == 1:
                x1 = border_px + x * square_size_px
                y1 = border_px + y * square_size_px
                x2 = x1 + square_size_px
                y2 = y1 + square_size_px
                img[y1:y2, x1:x2] = 0

    # Add label text at the bottom
    label = f"OpenCV Calibration Target | 9x6 Inner Corners (10x7 Squares) | ELIOS-SAR"
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(label, font, 0.7, 2)
    text_x = (total_w - tw) // 2
    text_y = total_h - 35
    cv2.putText(img, label, (text_x, text_y), font, 0.7, 0, 2, cv2.LINE_AA)

    out_path = os.path.join(OUTPUT_DIR, "checkerboard_9x6_printable.png")
    cv2.imwrite(out_path, img)
    print(f"Checkerboard generated: {out_path} ({total_w}x{total_h} px)")
    return out_path

if __name__ == "__main__":
    generate_checkerboard()
