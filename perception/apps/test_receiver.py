from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(
            self.headers.get(
                "Content-Length",
                "0",
            )
        )

        body = self.rfile.read(
            length
        )

        try:
            payload = json.loads(
                body.decode("utf-8")
            )

            print(
                json.dumps(
                    payload,
                    indent=2,
                )
            )

        except Exception as error:
            print(
                "Invalid payload:",
                error,
            )

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.end_headers()

        self.wfile.write(
            b'{"success":true}'
        )


server = HTTPServer(
    ("127.0.0.1", 8000),
    Handler,
)

print("Test receiver listening on port 8000")
server.serve_forever()
