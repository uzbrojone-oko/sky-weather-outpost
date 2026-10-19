import json
import threading
from datetime import UTC, datetime
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
            Path("tests/fixtures/rtl433-sample.jsonl"),
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
