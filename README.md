# Sky Weather Outpost

Sky Weather Outpost is a configurable local outpost hub for collecting, normalizing, storing and exposing telemetry, environmental sensor data, node health and future sky/media observations.

The first target is a small Kraków Lab MVP: read temperature and humidity from one known `rtl_433` sensor, store normalized measurements in SQLite, expose a simple API, and render a one-page dashboard.

The long-term direction is wider: weather stations, all-sky media, node health, astro telemetry, garden sensors, lightning detection, NAS archiving, Docker/Compose, optional observability integrations and future agents.

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

## MVP v0.1

Kraków Lab only:

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
outpost server --config config/examples/krakow.yaml
outpost replay data/raw_data/rtl433-live.jsonl --config config/examples/krakow.yaml
outpost health --config config/examples/krakow.yaml
outpost migrate --config config/examples/krakow.yaml
outpost backup --config config/examples/krakow.yaml
```

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [MVP](MVP.md)
- [Configuration](CONFIG.md)
- [Runbook](RUNBOOK.md)
- [Security](SECURITY.md)
- [Deployment](DEPLOYMENT.md)
- [Copilot instructions](copilot-instructions.md)
