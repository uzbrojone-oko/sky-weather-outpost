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
