from pathlib import Path

from app.config import loader


def test_explicit_config_path_takes_priority_over_environment(
    monkeypatch,
    tmp_path: Path,
):
    explicit_path = tmp_path / "explicit.yaml"
    monkeypatch.setenv("OUTPOST_CONFIG", str(tmp_path / "environment.yaml"))

    resolver = getattr(loader, "resolve_config_path", None)
    assert callable(resolver), "config path resolver is not implemented yet"
    assert resolver(explicit_path) == explicit_path


def test_environment_config_is_used_when_no_explicit_path(
    monkeypatch,
    tmp_path: Path,
):
    environment_path = tmp_path / "environment.yaml"
    monkeypatch.setenv("OUTPOST_CONFIG", str(environment_path))

    resolver = getattr(loader, "resolve_config_path", None)
    assert callable(resolver), "config path resolver is not implemented yet"
    assert resolver() == environment_path


def test_default_config_path_uses_user_config_directory(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.delenv("OUTPOST_CONFIG", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    resolver = getattr(loader, "resolve_config_path", None)
    assert callable(resolver), "config path resolver is not implemented yet"
    assert resolver() == (
        tmp_path / ".config" / "sky-weather-outpost" / "config.yaml"
    )
