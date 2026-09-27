from __future__ import annotations

from copy import deepcopy
from typing import Any


class GCSMapService:
    """
    Stores the latest occupancy map received from a real mapping source.

    The GCS does not create or synthesise any map data.
    If no map has been received, get_snapshot() returns None.
    """

    def __init__(self) -> None:
        self._map: dict[str, Any] | None = None

    def update(
        self,
        map_payload: dict[str, Any],
    ) -> None:
        if not isinstance(map_payload, dict):
            raise ValueError("map_payload must be a dict")

        self._map = deepcopy(map_payload)

    def clear(self) -> None:
        self._map = None

    def get_snapshot(self) -> dict[str, Any] | None:
        return deepcopy(self._map)
