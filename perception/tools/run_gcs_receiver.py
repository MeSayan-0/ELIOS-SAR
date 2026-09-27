import asyncio
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gcs.receiver import GCSReceiver


if __name__ == "__main__":
    asyncio.run(
        GCSReceiver(
            host="0.0.0.0",
            port=8766,
        ).run()
    )
