from pathlib import Path

import pytest

from app.config.loader import ConfigError, load_config


def test_load_city_lab_example():
    config = load_config(Path("config/examples/city-lab.yaml"))

    assert config.site.id == "city-lab"
    assert config.site.name == "City Lab"
    assert config.node.id == "city-lab-core"
    assert config.modules.rtl433.enabled is True
    assert config.devices[0].match.model == "inFactory-TH"


def test_missing_required_site_id_is_rejected(tmp_path: Path):
    path = tmp_path / "invalid.yaml"
    path.write_text(
        "site:\n  name: Broken Lab\n  type: lab\n  timezone: Europe/Warsaw\n"
        "node:\n  id: broken-core\n  role: hub\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="site.id"):
        load_config(path)


def test_missing_config_file_has_clear_error(tmp_path: Path):
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config(tmp_path / "missing.yaml")
