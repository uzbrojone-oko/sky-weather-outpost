# Technology stack

This document records the intended technology choices for Sky Weather Outpost. It is a planning baseline, not a requirement to introduce every technology immediately.

The guiding rule is: use the smallest stack that satisfies the current version while keeping clean extension points for later modules and deployment modes.

## v0.1 application stack

### Language and runtime

- Python 3.11+.
- Dedicated Python virtual environment for native installations.
- `pyproject.toml` as the project/dependency metadata source.

### Backend and API

- FastAPI for the HTTP API and web application boundary.
- ASGI server such as Uvicorn for native development/runtime.
- Pydantic-based validation for configuration and API/domain payload boundaries where appropriate.

### Configuration and data contracts

- YAML for site/application configuration.
- JSON/JSONL for ingest payloads, replay fixtures and API responses.
- Environment variables or external local secret files for secrets.

### Storage

- SQLite as the active local database for the initial outpost.
- Explicit schema migrations from the beginning.
- Local filesystem for runtime/media files; media metadata is indexed in SQLite rather than stored as database BLOBs.
- NAS only for backup/archive and selected media, never as the active SQLite location.

### Radio / sensor ingest

- `rtl_433` for supported RF weather/environment sensors.
- RTL-SDR hardware where live radio collection is enabled.
- JSONL replay as the first development/test ingest mode.
- Live `rtl_433` stdout collection after replay mode is stable.

### Web UI

- Server-served, lightweight one-page dashboard for the initial versions.
- Card-based dashboard model.
- Avoid introducing a separate SPA/frontend framework until the UI complexity clearly requires it.

### Testing and code quality

- pytest for automated tests.
- Ruff for linting/format-related checks.
- Small sanitized JSONL fixtures for ingest and normalization tests.

## Native deployment stack

Primary production-style deployment for early versions:

- Debian or Ubuntu Linux.
- Python virtual environment.
- systemd service management.
- Local SSD/storage for database and runtime state.
- Caddy as the preferred reverse proxy when HTTPS/public exposure is introduced.
- Nginx as an alternative reverse proxy.

## Planned integration technologies

These are introduced only when their roadmap stage requires them:

- MQTT, likely via Mosquitto, for selected local messaging/integration scenarios.
- HTTP/JSON ingest for remote Outpost agents.
- INDI/Ekos integration through a dedicated astro agent rather than coupling the core directly to telescope hardware.
- Home Assistant APIs, WebSocket events and/or MQTT through a dedicated adapter/agent.
- Vendor-specific PV inverter, smart-meter, battery and EV charger protocols behind adapters/agents.

## Observability

Planned optional observability stack:

- Structured application logs.
- Health and readiness endpoints.
- Prometheus-compatible `/metrics` endpoint.
- Prometheus for metrics collection when needed.
- Grafana for optional technical dashboards.
- Loki or another log backend only if operational needs justify it.

The Outpost's own user dashboard remains separate from Grafana. Grafana is an optional operational/technical tool, not the primary product UI.

## Containers and orchestration

Deployment evolution should be incremental:

1. Native Python + systemd.
2. Docker/Compose when useful.
3. k3s/Kubernetes only when the project has a real reason to use orchestration.

The application should remain container-friendly from the beginning through external configuration, mountable data paths, stdout logging, health/readiness endpoints and graceful shutdown, without making containers a v0.1 requirement.

## Architecture boundaries

Technology choices must preserve these boundaries:

- Core domain model remains generic and vendor-neutral.
- Hardware and vendor protocols belong in adapters/agents.
- Raw ingest data is preserved separately from normalized data.
- Public, internal and ingest API surfaces remain distinct.
- Telemetry and observation are separate from active control/automation.
- Site installations remain capable of autonomous local operation.

## Deliberately undecided

The following choices should remain open until implementation pressure provides a reason to decide them:

- A dedicated frontend framework.
- A database server replacing SQLite.
- A specific Python ORM/database abstraction beyond the migration/storage needs discovered during v0.1.
- A permanent MQTT topology.
- A specific container orchestration platform for production use.
- Exact vendor libraries/protocols for PV, EV charging and smart-home hardware.

Avoid selecting technology only because it may be useful someday. Add it when a concrete roadmap requirement needs it.
