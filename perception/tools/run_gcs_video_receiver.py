import asyncio
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gcs.video_receiver import GCSVideoReceiver


if __name__ == "__main__":
    receiver = GCSVideoReceiver()
    asyncio.run(receiver.run())
