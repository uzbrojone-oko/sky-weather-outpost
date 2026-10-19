import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from app.config.models import OutpostConfig
from app.storage.database import initialize_database
from app.storage.repository import get_latest_reading


def create_api_server(
    config: OutpostConfig,
    *,
    host: str | None = None,
    port: int | None = None,
) -> ThreadingHTTPServer:
    database_path = Path(config.storage.sqlite_path)
    initialize_database(database_path)

    class ApiHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if urlsplit(self.path).path != "/api/v1/public/current":
                self._send_json(404, {"error": "not_found"})
                return

            if not config.api.public_enabled:
                self._send_json(404, {"error": "not_found"})
                return

            devices = []
            for device in config.devices:
                if not device.public:
                    continue

                reading = get_latest_reading(database_path, device.key)
                if reading is None:
                    continue

                devices.append({
                    "key": device.key,
                    "name": device.name,
                    "type": device.type,
                    "measured_at": reading["measured_at"],
                    "received_at": reading["received_at"],
                    "measurements": reading["measurements"],
                })

            self._send_json(200, {
                "site": {
                    "id": config.site.id,
                    "name": config.site.name,
                },
                "devices": devices,
            })

        def log_message(self, _format: str, *_args: object) -> None:
            pass

    bind_host = config.api.host if host is None else host
    bind_port = config.api.port if port is None else port
    return ThreadingHTTPServer((bind_host, bind_port), ApiHandler)
