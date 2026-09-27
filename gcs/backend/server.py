from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.communication.protocol import (
    MESSAGE_DRONE_STATE,
    MESSAGE_HAZARD,
    MESSAGE_MAP_UPDATE,
    MESSAGE_MISSION_EVENT,
    MESSAGE_MISSION_STATE,
    MESSAGE_PERSON_DETECTION,
    MESSAGE_RISK_EVENT,
    MESSAGE_SENSOR_STATE,
    MESSAGE_VEHICLE_STATE,
)

from src.telemetry import TelemetryManager

from gcs.backend.map_service import GCSMapService
from gcs.backend.state import GCSState


gcs_state = GCSState()
map_service = GCSMapService()
telemetry_manager = TelemetryManager()

websocket_clients: set[WebSocket] = set()

STALE_VEHICLE_CHECK_INTERVAL_SECONDS = 1.0


def process_message(message: dict[str, Any]) -> None:
    """
    Process one inbound message.

    Only data supplied by the sender is stored.
    No operational/default telemetry is generated.
    """

    if not isinstance(message, dict):
        raise TypeError("message must be a dictionary")

    message_type = message.get("message_type")
    payload = message.get("payload")

    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")

    if message_type in (
        MESSAGE_VEHICLE_STATE,
        MESSAGE_DRONE_STATE,
    ):
        vehicle_id = payload.get("vehicle_id")

        if not vehicle_id:
            return

        gcs_state.update_vehicle(payload)
        return

    if message_type == MESSAGE_SENSOR_STATE:
        gcs_state.update_sensor(payload)
        return

    if message_type == MESSAGE_PERSON_DETECTION:
        gcs_state.add_person_detection(payload)
        return

    if message_type == MESSAGE_HAZARD:
        gcs_state.add_hazard(payload)
        return

    if message_type == MESSAGE_RISK_EVENT:
        gcs_state.add_risk_event(payload)
        return

    if message_type == MESSAGE_MISSION_EVENT:
        gcs_state.add_mission_event(payload)
        return

    if message_type == MESSAGE_MISSION_STATE:
        mission_id = payload.get("mission_id")

        if not mission_id:
            return

        gcs_state.update_mission(
            str(mission_id),
            payload,
        )
        return

    if message_type == MESSAGE_MAP_UPDATE:
        gcs_state.set_map(payload)
        return

    # Telemetry is intentionally handled separately from
    # vehicle registration/state.
    if message_type == "TELEMETRY":
        telemetry_manager.update_from_payload(
            payload
        )
        return

    # Unknown message types are intentionally ignored.
    return


def get_authoritative_state() -> dict[str, Any]:
    """
    Build the state exposed to the GCS.

    Telemetry is included only when it has actually been received.
    """

    state = gcs_state.get_snapshot()

    received_telemetry = telemetry_manager.get_all()

    state["telemetry"] = received_telemetry

    return state


async def broadcast_state() -> None:
    """
    Broadcast the current authoritative state
    to all connected GCS clients.
    """

    if not websocket_clients:
        return

    state = get_authoritative_state()

    disconnected_clients: list[WebSocket] = []

    for websocket in list(websocket_clients):
        try:
            await websocket.send_json(state)

        except Exception:
            disconnected_clients.append(websocket)

    for websocket in disconnected_clients:
        websocket_clients.discard(websocket)


async def stale_vehicle_loop() -> None:
    """
    Periodically mark stale vehicles disconnected.

    This loop does not create vehicles or telemetry.
    """

    while True:
        await asyncio.sleep(
            STALE_VEHICLE_CHECK_INTERVAL_SECONDS
        )

        before = gcs_state.get_snapshot()

        gcs_state.mark_stale_vehicles_disconnected()

        after = gcs_state.get_snapshot()

        if before["vehicles"] != after["vehicles"]:
            await broadcast_state()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle.

    Only backend maintenance tasks are started.
    """

    stale_task = asyncio.create_task(
        stale_vehicle_loop()
    )

    try:
        yield

    finally:
        stale_task.cancel()

        try:
            await stale_task

        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="ELIOS-SAR GCS Backend",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/state")
async def get_state() -> dict[str, Any]:
    """
    Return authoritative current GCS state.
    """

    return get_authoritative_state()


@app.post("/api/message")
async def receive_message(
    message: dict[str, Any],
) -> dict[str, Any]:
    """
    Receive an inbound vehicle/system message.

    Only supplied data is stored.
    """

    try:
        process_message(message)

    except (
        ValueError,
        KeyError,
        TypeError,
    ) as exc:

        return {
            "accepted": False,
            "error": str(exc),
        }

    await broadcast_state()

    return {
        "accepted": True,
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
) -> None:
    """
    WebSocket endpoint for the React GCS.
    """

    await websocket.accept()

    websocket_clients.add(websocket)

    try:
        await websocket.send_json(
            get_authoritative_state()
        )

        while True:
            message = await websocket.receive_json()

            try:
                process_message(message)

            except (
                ValueError,
                KeyError,
                TypeError,
            ):
                continue

            await broadcast_state()

    except WebSocketDisconnect:
        websocket_clients.discard(websocket)

    except Exception:
        websocket_clients.discard(websocket)
