import importlib
from pathlib import Path

import pytest

from app.config.loader import load_config
from app.normalizers.rtl433 import build_device_key


def make_registry(devices):
    try:
        module = importlib.import_module("app.core.devices")
    except ModuleNotFoundError as exc:
        if exc.name != "app.core.devices":
            raise
        pytest.fail("DeviceRegistry is not implemented yet")

    return module.DeviceRegistry(devices)


def test_registry_returns_declared_device_by_normalized_key():
    config = load_config(Path("config/examples/city-lab.yaml"))
    registry = make_registry(config.devices)

    device = registry.get("rtl433:inFactory-TH:1:166")

    assert device is not None
    assert device.name == "City Lab weather sensor"


def test_registry_returns_none_for_unknown_device():
    config = load_config(Path("config/examples/city-lab.yaml"))
    registry = make_registry(config.devices)

    assert registry.get("rtl433:unknown:1:999") is None


def test_city_lab_collects_battery_status():
    config = load_config(Path("config/examples/city-lab.yaml"))
    registry = make_registry(config.devices)

    device = registry.get("rtl433:inFactory-TH:1:166")

    assert device is not None
    assert "battery_ok" in device.metrics


def test_city_lab_device_key_matches_rtl433_match_fields():
    config = load_config(Path("config/examples/city-lab.yaml"))
    device = make_registry(config.devices).get("rtl433:inFactory-TH:1:166")

    assert device is not None
    assert device.key == build_device_key(device.match.model_dump())
