from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import logging

from src.core.serialization import serialize

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    health_provider = None

    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        try:
            provider = HealthHandler.health_provider
            raw_payload = (
                provider()
                if provider is not None
                else {
                    "status": "unknown"
                }
            )

            payload = serialize(raw_payload)

            body = json.dumps(
                payload,
                default=str,
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.wfile.write(body)

        except Exception as exc:
            import traceback
            traceback.print_exc()
            body = json.dumps(
                {
                    "status": "error",
                    "error": str(exc),
                }
            ).encode("utf-8")

            self.send_response(500)
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        return


def start_health_server(
    health_provider,
    host: str = "127.0.0.1",
    port: int = 8767,
):
    HealthHandler.health_provider = health_provider
    ports_to_try = [port, 8767, 8768, 8888, 5000, 0]

    for p in ports_to_try:
        try:
            server = HTTPServer((host, p), HealthHandler)
            actual_port = server.server_address[1]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            logger.info("Health server started on http://%s:%s/health", host, actual_port)
            return server
        except (PermissionError, OSError) as exc:
            logger.warning("Port %s unavailable: %s. Trying next port...", p, exc)

    return None
