from pathlib import Path

from app.cli import main


def test_config_validate_prints_site_and_node(capsys):
    exit_code = main(["config", "validate", "config/examples/city-lab.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Configuration valid\nsite: city-lab\nnode: city-lab-core\n"
    assert captured.err == ""


def test_config_validate_reports_invalid_config(tmp_path: Path, capsys):
    path = tmp_path / "invalid.yaml"
    path.write_text("site: {}\n", encoding="utf-8")

    exit_code = main(["config", "validate", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Configuration validation failed" in captured.err


def test_rtl433_replay_prints_reading_and_metric_counts(capsys):
    exit_code = main([
        "rtl433", "replay",
        "--config", "config/examples/city-lab.yaml",
        "--input", "tests/fixtures/rtl433-sample.jsonl",
    ])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Replay complete\nreadings: 3\nmetrics: 9\n"
    assert captured.err == ""


def test_rtl433_replay_persists_to_configured_database(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    import sqlite3

    from app.config.loader import load_config

    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "outpost.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )
    monkeypatch.setattr("app.cli.load_config", lambda _path: config)

    exit_code = main(
        [
            "rtl433",
            "replay",
            "--config",
            "config/examples/city-lab.yaml",
            "--input",
            "tests/fixtures/rtl433-sample.jsonl",
        ]
    )

    captured = capsys.readouterr()
    with sqlite3.connect(database_path) as connection:
        raw_event_count = connection.execute(
            "SELECT COUNT(*) FROM raw_events"
        ).fetchone()[0]
        measurement_count = connection.execute(
            "SELECT COUNT(*) FROM measurements"
        ).fetchone()[0]

    assert exit_code == 0
    assert captured.out == "Replay complete\nreadings: 3\nmetrics: 9\n"
    assert captured.err == ""
    assert raw_event_count == 3
    assert measurement_count == 9


def test_rtl433_ingest_persists_jsonl_from_stdin(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    import io
    import sqlite3

    from app.config.loader import load_config

    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "outpost.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )
    monkeypatch.setattr("app.cli.load_config", lambda _path: config)

    fixture_line = (
        Path("tests/fixtures/rtl433-sample.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[1]
    )
    monkeypatch.setattr(
        "app.cli.sys.stdin",
        io.StringIO(f"{fixture_line}\n{fixture_line}\n"),
    )

    exit_code = main(
        [
            "rtl433",
            "ingest",
            "--config",
            "config/examples/city-lab.yaml",
        ]
    )

    captured = capsys.readouterr()
    with sqlite3.connect(database_path) as connection:
        raw_event_count = connection.execute(
            "SELECT COUNT(*) FROM raw_events"
        ).fetchone()[0]
        measurement_count = connection.execute(
            "SELECT COUNT(*) FROM measurements"
        ).fetchone()[0]

    assert exit_code == 0
    assert captured.out == "Ingest complete\nreadings: 1\nmetrics: 3\n"
    assert "stored reading: device=rtl433:inFactory-TH:1:166 metrics=3" in captured.err
    assert raw_event_count == 1
    assert measurement_count == 3


def test_api_serve_starts_server(monkeypatch, capsys):
    from app import cli
    from app.config.loader import load_config

    config = load_config(Path("config/examples/city-lab.yaml"))

    class FakeServer:
        server_address = ("127.0.0.1", 8000)
        started = False

        def serve_forever(self):
            self.started = True

        def server_close(self):
            pass

    server = FakeServer()
    monkeypatch.setattr(cli, "load_config", lambda _path: config)
    monkeypatch.setattr(
        cli,
        "create_api_server",
        lambda _config, **_kwargs: server,
        raising=False,
    )

    exit_code = cli.main(
        ["api", "serve", "--config", "config/examples/city-lab.yaml"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "API listening at http://127.0.0.1:8000\n"
    assert captured.err == ""
    assert server.started


def test_api_serve_passes_host_override_to_server(monkeypatch, capsys):
    from app import cli
    from app.config.loader import load_config

    config = load_config(Path("config/examples/city-lab.yaml"))
    server_options = {}

    class FakeServer:
        server_address = ("192.168.1.249", 8000)

        def serve_forever(self):
            pass

        def server_close(self):
            pass

    server = FakeServer()

    def create_server(_config, *, host=None):
        server_options["host"] = host
        return server

    monkeypatch.setattr(cli, "load_config", lambda _path: config)
    monkeypatch.setattr(cli, "create_api_server", create_server)

    exit_code = cli.main(
        [
            "api",
            "serve",
            "--config",
            "config/examples/city-lab.yaml",
            "--host",
            "192.168.1.249",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert server_options["host"] == "192.168.1.249"
    assert captured.out == "API listening at http://192.168.1.249:8000\n"
    assert captured.err == ""


def test_weather_current_prints_latest_reading(monkeypatch, capsys):
    from app import cli
    from app.config.loader import load_config

    config = load_config(Path("config/examples/city-lab.yaml"))
    reading = {
        "device_key": "rtl433:inFactory-TH:1:166",
        "measured_at": "2026-10-19T14:48:31+00:00",
        "received_at": "2026-10-19T14:48:32+00:00",
        "measurements": {
            "temperature": {"value": 10.444, "unit": "C"},
            "humidity": {"value": 79.0, "unit": "%"},
            "battery_ok": {"value": 1.0, "unit": "bool"},
        },
    }

    monkeypatch.setattr(cli, "load_config", lambda _path: config)
    monkeypatch.setattr(
        cli,
        "get_latest_reading",
        lambda _database_path, _device_key: reading,
        raising=False,
    )

    exit_code = cli.main(
        ["weather", "current", "--config", "config/examples/city-lab.yaml"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert config.site.name in captured.out
    assert "Pomiar: 19.10.2026, 16:48" in captured.out
    assert "Temperatura: 10,4 °C" in captured.out
    assert "Wilgotność: 79%" in captured.out
    assert "Bateria: OK" in captured.out
    assert captured.err == ""


def test_weather_current_reports_when_no_reading_exists(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    from app import cli
    from app.config.loader import load_config

    config = load_config(Path("config/examples/city-lab.yaml"))
    database_path = tmp_path / "outpost.sqlite"
    config = config.model_copy(
        update={
            "storage": config.storage.model_copy(
                update={"sqlite_path": str(database_path)}
            )
        }
    )

    monkeypatch.setattr(cli, "load_config", lambda _path: config)
    monkeypatch.setattr(
        cli,
        "get_latest_reading",
        lambda _database_path, _device_key: None,
    )

    exit_code = cli.main(
        ["weather", "current", "--config", "config/examples/city-lab.yaml"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Brak zapisanych pomiarów.\n"
    assert captured.err == ""


def test_weather_current_fetches_and_formats_api_response(
    monkeypatch,
    capsys,
):
    import json
    from io import BytesIO

    from app import cli

    payload = {
        "site": {
            "id": "city-lab",
            "name": "City Lab",
            "timezone": "Europe/Warsaw",
        },
        "devices": [
            {
                "key": "rtl433:inFactory-TH:1:166",
                "name": "City Lab weather sensor",
                "type": "weather_sensor",
                "measured_at": "2026-10-19T14:48:31+00:00",
                "received_at": "2026-10-19T14:48:32+00:00",
                "measurements": {
                    "temperature": {"value": 10.444, "unit": "C"},
                    "humidity": {"value": 79.0, "unit": "%"},
                    "battery_ok": {"value": 1.0, "unit": "bool"},
                },
            }
        ],
    }
    requested = {}

    def fake_urlopen(url, *, timeout):
        requested["url"] = url
        requested["timeout"] = timeout
        return BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(cli, "urlopen", fake_urlopen, raising=False)

    exit_code = cli.main(
        [
            "weather",
            "current",
            "--url",
            "http://192.168.1.249:8000/api/v1/public/current",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert requested == {
        "url": "http://192.168.1.249:8000/api/v1/public/current",
        "timeout": 2,
    }
    assert "City Lab" in captured.out
    assert "Pomiar: 19.10.2026, 16:48" in captured.out
    assert "Temperatura: 10,4 °C" in captured.out
    assert "Wilgotność: 79%" in captured.out
    assert "Bateria: OK" in captured.out
    assert captured.err == ""


def test_weather_current_uses_environment_config_without_flag(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    from app import cli
    from app.config.loader import load_config

    config = load_config(Path("config/examples/city-lab.yaml"))
    environment_path = tmp_path / "city-lab.yaml"
    loaded_paths = []

    monkeypatch.setenv("OUTPOST_CONFIG", str(environment_path))
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda path: loaded_paths.append(path) or config,
    )
    monkeypatch.setattr(cli, "initialize_database", lambda _path: None)
    monkeypatch.setattr(cli, "get_latest_reading", lambda *_args: None)

    exit_code = cli.main(["weather", "current"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert loaded_paths == [environment_path]
    assert captured.out == "Brak zapisanych pomiarów.\n"
    assert captured.err == ""
