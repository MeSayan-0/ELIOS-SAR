from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.safe_emitter import SafeEventEmitter


sent = []


def sender(event):
    sent.append(event)
    print("SENT:", event["event_type"])


emitter = SafeEventEmitter(
    sender=sender,
    cooldown_seconds=2,
)

for _ in range(10):
    emitter.emit(
        event_type="person_detected",
        identity="person_1",
        payload={
            "confidence": 0.91,
        },
        severity="warning",
    )

    time.sleep(0.1)

print()
print("Total emitted:", len(sent))
