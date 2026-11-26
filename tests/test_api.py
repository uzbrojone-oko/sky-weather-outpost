import json
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

from app.api.server import create_api_server
from app.config.loader import load_config
from app.ingest.replay import replay_jsonl
from app.ingest.rtl433 import Rtl433FrameProcessor
from app.storage.database import initialize_database
from app.storage.repository import store_frame


def test_public_current_returns_latest_configured_reading(tmp_path: Path):
    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "outpost.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )
    initialize_database(database_path)

    processor = Rtl433FrameProcessor(config.devices, config.site.timezone)
    received_at = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
    frames = list(
        replay_jsonl(
            Path("tests/fixtures/rtl433-bresser-sample.jsonl"),
            processor,
            received_at,
        )
    )

    for frame in frames:
        device = next(item for item in config.devices if item.key == frame.device_key)
        store_frame(
            database_path,
            frame,
            site_id=config.site.id,
            node=config.node,
            device=device,
        )

    server = create_api_server(config, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        assert server.server_port != config.api.port
        url = f"http://127.0.0.1:{server.server_port}/api/v1/public/current"
        with urlopen(url, timeout=2) as response:
            payload = json.load(response)
            assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert payload["site"] == {
        "id": config.site.id,
        "name": config.site.name,
        "timezone": config.site.timezone,
    }
    assert payload["node"] == {
        "id": config.node.id,
        "name": config.node.name or config.site.name,
    }
    assert len(payload["devices"]) == 1

    latest_device = payload["devices"][0]
    assert latest_device["key"] == frames[-1].device_key
    assert latest_device["measured_at"] == frames[-1].measured_at.isoformat()
    assert latest_device["measurements"]["temperature"]["unit"] == "C"
    assert latest_device["measurements"]["humidity"]["unit"] == "%"


def test_public_current_returns_empty_devices_before_first_ingest(
    tmp_path: Path,
):
    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "new-outpost.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )

    server = create_api_server(config, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        url = f"http://127.0.0.1:{server.server_port}/api/v1/public/current"
        with urlopen(url, timeout=2) as response:
            payload = json.load(response)
            assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert payload["devices"] == []


def test_public_history_returns_aggregated_weather_buckets(tmp_path: Path):
    from app.normalizers.rtl433 import MeasurementDraft, NormalizedFrame

    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "history.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )
    initialize_database(database_path)
    device = config.devices[0]

    now = datetime.now(UTC)
    bucket_start = datetime.fromtimestamp(
        (int(now.timestamp()) // (15 * 60)) * (15 * 60) - (15 * 60),
        UTC,
    )
    for minute, temperature, humidity in ((1, 1.0, 70.0), (3, 3.0, 80.0)):
        measured_at = bucket_start + timedelta(minutes=minute)
        frame = NormalizedFrame(
            device_key=device.key,
            measured_at=measured_at,
            received_at=measured_at,
            measurements=(
                MeasurementDraft("temperature", temperature, "C"),
                MeasurementDraft("humidity", humidity, "%"),
                MeasurementDraft("battery_ok", 1.0, "bool"),
            ),
            raw={},
        )
        store_frame(
            database_path,
            frame,
            site_id=config.site.id,
            node=config.node,
            device=device,
        )

    server = create_api_server(config, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        url = f"http://127.0.0.1:{server.server_port}/api/v1/public/history?period=day"
        with urlopen(url, timeout=2) as response:
            payload = json.load(response)
            assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert payload["period"] == "day"
    assert payload["node"] == {
        "id": config.node.id,
        "name": config.node.name or config.site.name,
    }
    assert payload["bucket_seconds"] == 15 * 60
    assert len(payload["devices"]) == 1
    points = payload["devices"][0]["points"]
    assert len(points) == 1
    assert points[0]["measurements"]["temperature"] == {
        "average": 2.0,
        "min": 1.0,
        "max": 3.0,
        "unit": "C",
        "samples": 2,
    }
    assert points[0]["measurements"]["humidity"] == {
        "average": 75.0,
        "min": 70.0,
        "max": 80.0,
        "unit": "%",
        "samples": 2,
    }


def test_public_history_rejects_unknown_period(tmp_path: Path):
    from urllib.error import HTTPError

    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "history.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )

    server = create_api_server(config, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        url = (
            f"http://127.0.0.1:{server.server_port}"
            "/api/v1/public/history?period=decade"
        )
        try:
            urlopen(url, timeout=2)
        except HTTPError as error:
            assert error.code == 400
            assert json.load(error) == {
                "error": "invalid_period",
                "allowed": ["day", "week", "month", "year"],
            }
        else:
            raise AssertionError("Unknown period should return HTTP 400")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_public_history_periods_return_documented_rolling_windows(
    tmp_path: Path,
):
    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "history-periods.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )

    server = create_api_server(config, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    expected = {
        "day": (1, 15 * 60),
        "week": (7, 60 * 60),
        "month": (30, 6 * 60 * 60),
        "year": (365, 24 * 60 * 60),
    }
    try:
        for period, (days, bucket_seconds) in expected.items():
            url = (
                f"http://127.0.0.1:{server.server_port}"
                f"/api/v1/public/history?period={period}"
            )
            with urlopen(url, timeout=2) as response:
                payload = json.load(response)
                assert response.status == 200

            start_at = datetime.fromisoformat(payload["from"])
            end_at = datetime.fromisoformat(payload["to"])
            assert end_at - start_at == timedelta(days=days)
            assert payload["period"] == period
            assert payload["bucket_seconds"] == bucket_seconds
            assert len(payload["devices"]) == 1
            assert payload["devices"][0]["points"] == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)



def test_dashboard_is_served_from_api_root(tmp_path: Path):
    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "dashboard.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )

    server = create_api_server(config, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=2) as response:
            html = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers.get_content_type() == "text/html"
            assert "Historia pogody" in html
            assert 'data-period="year"' in html
            assert "/api/v1/public/history?period=" in html
            assert '"Czujnik: " + device.name' in html
            assert "midnight-line" in html
            assert "historyRange.from" in html
            assert "historyRange.to" in html
            assert "maxGapMilliseconds" in html
            assert "range-bar" in html
            assert "item.timestamp-previous.timestamp>maxGapMilliseconds" in html
            assert "history.bucket_seconds" in html
            assert 'parts.weekday==="Mon"' in html
            assert "monthBoundaries" in html
            assert 'parts.month==="01"' in html
            assert "function updateDataStatus" in html
            assert "Brakujące przedziały" in html
            assert "bucketGap>1.5" in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
