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


def test_alternate_site_and_node_are_accepted(tmp_path: Path):
    source = Path("config/examples/city-lab.yaml").read_text(encoding="utf-8")
    source = source.replace("id: city-lab", "id: field-lab", 1)
    source = source.replace('name: "City Lab"', 'name: "Field Lab"', 1)
    source = source.replace("id: city-lab-core", "id: field-lab-core", 1)

    path = tmp_path / "alternate.yaml"
    path.write_text(source, encoding="utf-8")

    config = load_config(path)

    assert config.site.id == "field-lab"
    assert config.site.name == "Field Lab"
    assert config.node.id == "field-lab-core"


def test_missing_required_site_id_is_rejected(tmp_path: Path):
    path = tmp_path / "invalid.yaml"
    path.write_text(
        "site:\n  name: Broken Lab\n  type: lab\n  timezone: Europe/Warsaw\n"
        "node:\n  id: broken-core\n  role: hub\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="site.id"):
        load_config(path)


def test_unknown_field_is_rejected(tmp_path: Path):
    source = Path("config/examples/city-lab.yaml").read_text(encoding="utf-8")
    path = tmp_path / "unknown-field.yaml"
    path.write_text(source + "\nunexpected_option: true\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="unexpected_option"):
        load_config(path)


def test_missing_config_file_has_clear_error(tmp_path: Path):
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config(tmp_path / "missing.yaml")
