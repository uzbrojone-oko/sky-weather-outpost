# Sky Weather Outpost

Sky Weather Outpost is a configurable local outpost hub for collecting, normalizing, storing and exposing telemetry, environmental sensor data, node health and future sky/media observations.

The first target is a small City Lab MVP: read temperature and humidity from one known `rtl_433` sensor, store normalized measurements in SQLite, expose a simple API, and render a one-page dashboard.

The long-term direction is wider: weather stations, all-sky media, node health, astro telemetry, garden sensors, lightning detection, NAS archiving, energy/PV and EV telemetry, Home Assistant/smart-home integration, optional observability integrations and future distributed agents.

## Sky / Weather / Outpost

The project name is also its scope model:

- **Sky** — sky and astronomy observations: all-sky imaging, astro telemetry, cloud information, observation readiness, Astro Score and related media.
- **Weather** — local environment: temperature, humidity, wind, rain, dew conditions, lightning, garden/environment sensors and historical weather data.
- **Outpost** — the installation itself: nodes and computers, service health, storage, backup, network and web availability, TLS status, NAS, energy/PV, EV charging and selected smart-home/site infrastructure.

`Outpost` is not a miscellaneous bucket. It represents the physical site as an autonomous technical installation. The hub should be able to answer both "what is happening outside?" and "is the outpost itself healthy?" while keeping automation/control responsibilities separate from the generic telemetry core.

## Core principles

- Build small, design wide.
- The core is a generic local hub, not a weather-only app.
- Every installation is autonomous and configured by site/node/device definitions.
- Raw input is preserved separately from normalized measurements.
- Public and internal APIs are separated.
- Logging, health checks, and system status are first-class features.
- Media files are stored as files and indexed in the database.
- NAS is for backup and selected archive, not the active database.
- Native/systemd is the first deployment target; Docker/Kubernetes readiness should not be blocked by design.
- Future integrations should extend the generic model rather than add vendor-specific concepts to the core.

## MVP v0.1

City Lab only:

- `inFactory-TH` sensor via `rtl_433` JSON/JSONL.
- Temperature and humidity.
- SQLite storage.
- `raw_events`, `measurements`, `devices`, `nodes`, `system_events`.
- `/api/v1/public/current`.
- `/api/v1/internal/health`.
- One-page dashboard.
- Structured logging.

## Planned command shape

```bash
outpost server --config config/examples/city-lab.yaml
outpost replay data/raw_data/rtl433-live.jsonl --config config/examples/city-lab.yaml
outpost health --config config/examples/city-lab.yaml
outpost migrate --config config/examples/city-lab.yaml
outpost backup --config config/examples/city-lab.yaml
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [MVP](docs/MVP.md)
- [Tech stack](docs/TECH_STACK.md)
- [Configuration](docs/CONFIG.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Runbook](docs/RUNBOOK.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Handbook](docs/HANDBOOK.md)
- [Copilot instructions](copilot-instructions.md)
