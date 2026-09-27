from pathlib import Path
import time


def cleanup(
    directory="logs",
    max_age_days=7,
):
    root = Path(directory)

    if not root.exists():
        return

    cutoff = time.time() - (
        max_age_days * 86400
    )

    for path in root.iterdir():
        if not path.is_file():
            continue

        if path.stat().st_mtime < cutoff:
            print("Deleting:", path)
            path.unlink()


if __name__ == "__main__":
    cleanup()
