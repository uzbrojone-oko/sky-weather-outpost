from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SiteConfig(ConfigModel):
    id: str
    name: str
    type: str
    timezone: str


class NodeConfig(ConfigModel):
    id: str
    role: str


class Rtl433Config(ConfigModel):
    enabled: bool
    mode: str
    replay_path: str | None = None


class SystemMetricsConfig(ConfigModel):
    enabled: bool
    interval_seconds: int = Field(gt=0)


class ModulesConfig(ConfigModel):
    rtl433: Rtl433Config
    system_metrics: SystemMetricsConfig


class StorageConfig(ConfigModel):
    sqlite_path: str


class LoggingConfig(ConfigModel):
    level: str
    mode: str


class ApiConfig(ConfigModel):
    host: str
    port: int = Field(ge=1, le=65535)
    public_enabled: bool
    internal_enabled: bool


class DeviceMatchConfig(ConfigModel):
    source: str
    model: str
    id: int | str
    channel: int | None = None


class DeviceConfig(ConfigModel):
    key: str
    name: str
    type: str
    public: bool
    match: DeviceMatchConfig
    metrics: list[str]


class DashboardConfig(ConfigModel):
    cards: list[str]


class OutpostConfig(ConfigModel):
    site: SiteConfig
    node: NodeConfig
    modules: ModulesConfig
    storage: StorageConfig
    logging: LoggingConfig
    api: ApiConfig
    devices: list[DeviceConfig]
    dashboard: DashboardConfig
