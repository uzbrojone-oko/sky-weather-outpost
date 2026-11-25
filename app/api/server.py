import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from app.config.models import OutpostConfig
from app.history import HISTORY_PERIODS, history_window
from app.storage.database import initialize_database
from app.storage.repository import get_latest_reading, get_reading_history

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
            request = urlsplit(self.path)
            if request.path not in {
                "/api/v1/public/current",
                "/api/v1/public/history",
            }:
                self._send_json(404, {"error": "not_found"})
                return

            if not config.api.public_enabled:
                self._send_json(404, {"error": "not_found"})
                return

            if request.path == "/api/v1/public/history":
                query = parse_qs(request.query)
                period_values = query.get("period", ["day"])
                period = period_values[0]
                if period not in HISTORY_PERIODS:
                    self._send_json(
                        400,
                        {
                            "error": "invalid_period",
                            "allowed": list(HISTORY_PERIODS),
                        },
                    )
                    return

                start_at, end_at, bucket_seconds = history_window(period)
                devices = []
                for device in config.devices:
                    if not device.public:
                        continue
                    devices.append(
                        {
                            "key": device.key,
                            "name": device.name,
                            "type": device.type,
                            "points": get_reading_history(
                                database_path,
                                device.key,
                                start_at=start_at,
                                end_at=end_at,
                                bucket_seconds=bucket_seconds,
                            ),
                        }
                    )

                self._send_json(
                    200,
                    {
                        "site": {
                            "id": config.site.id,
                            "name": config.site.name,
                            "timezone": config.site.timezone,
                        },
                        "period": period,
                        "from": start_at.isoformat(),
                        "to": end_at.isoformat(),
                        "bucket_seconds": bucket_seconds,
                        "devices": devices,
                    },
                )
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
                    "timezone": config.site.timezone,
                },
                "devices": devices,
            })

        def log_message(self, _format: str, *_args: object) -> None:
            pass

    bind_host = config.api.host if host is None else host
    bind_port = config.api.port if port is None else port
    return ThreadingHTTPServer((bind_host, bind_port), ApiHandler)
