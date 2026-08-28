# Architecture

## Purpose

Sky Weather Outpost is a configurable local hub for telemetry, environment data, media observations and node health.

It must not be designed as a weather-only application. Weather, all-sky, astro, garden, lightning, energy and external/smart-home integrations are modules/domains. The core stays generic and vendor-neutral.

### Sky / Weather / Outpost domain model

The project name describes three complementary views of one physical installation:

- **Sky** covers sky and astronomy observations: all-sky media, astro telemetry, cloud-related information, observation readiness and derived products such as Astro Score.
- **Weather** covers local environmental telemetry: temperature, humidity, wind, rain, dew conditions, lightning, garden/environment sensors and weather history.
- **Outpost** covers the health and infrastructure of the installation itself: nodes, services, storage, backup, network and web reachability, TLS state, NAS, energy/PV, EV charging and selected smart-home/site state.

`Outpost` is not a catch-all for unrelated features. It represents the physical site as an autonomous technical installation. A complete outpost should be able to describe both its surroundings and its own operational condition.

These domains are presentation and product concepts, not separate core architectures. They all map onto the same generic `site`, `node`, `device`, `measurement`, `event`, `media_asset` and `status` model. Automation and active device control remain outside the generic telemetry core and should use a separately designed control layer or an external automation platform such as Home Assistant.

## Core model

Primary concepts:

- `site` — installation/location, for example `krakow` or `glebokie`.
- `node` — machine/agent/controller that collects or emits data.
- `device` — sensor/camera/telescope/computer/component.
- `measurement` — normalized numeric/time-series value.
- `event` — discrete operational or domain event.
- `media_asset` — indexed file/stream/image/timelapse metadata.
- `status` — current health/heartbeat/component state.

Example hierarchy:

```text
site: glebokie
  node: glebokie-core-t620
    device: rtl433:bresser-5in1:<id>
  node: glebokie-media-t620
    device: allsky:t7c
  node: glebokie-astro-pc
    device: indi:asi533mc-pro
```

Future adapters and agents should map vendor- or protocol-specific data onto these generic concepts rather than expand the core model for each integration.

## Deployment model

Each installation is autonomous. Kraków and Głębokie do not need to communicate with each other.

The same codebase should run in different places with different configuration:

```bash
outpost server --config config/krakow.yaml
outpost server --config config/glebokie.yaml
```

Local hub is the source of truth for local data. NAS is backup/archive. A future central server may aggregate data but is not required.

## Ingest model

Use JSON as the ingest contract.

There are two levels:

1. Raw input JSON — exactly what came from `rtl_433`, MQTT, agent, HTTP, file replay, etc.
2. Normalized internal event JSON — common shape used by the hub.

Example normalized payload:

```json
{
  "schema_version": "1.0",
  "site": "krakow",
  "node": "krakow-lab-t620",
  "source": "rtl433",
  "events": [
    {
      "type": "measurement",
      "device_key": "rtl433:inFactory-TH:1:166",
      "metric": "temperature",
      "value": 20.06,
      "unit": "C"
    },
    {
      "type": "measurement",
      "device_key": "rtl433:inFactory-TH:1:166",
      "metric": "humidity",
      "value": 47,
      "unit": "%"
    }
  ]
}
```

## Storage model

Initial storage is SQLite.

Core tables planned for v0.1:

- `schema_migrations`
- `nodes`
- `devices`
- `raw_events`
- `measurements`
- `system_events`

Future tables:

- `node_heartbeats`
- `component_status`
- `media_assets`
- `archive_jobs`
- `outbox`
- `aggregates`

Do not store media binary data in SQLite. Store files on disk/NAS and index metadata in the database.

## API model

Use API versioning from the beginning:

```text
/api/v1/public/*
/api/v1/internal/*
/api/v1/ingest/*
```

Public API is read-only and safe to share. Internal API requires auth and may expose debug/system data.

Initial v0.1 endpoints:

- `GET /api/v1/public/current`
- `GET /api/v1/internal/health`

Planned later endpoints:

- `GET /api/v1/public/dashboard`
- `GET /api/v1/internal/status`
- `GET /api/v1/internal/system`
- `GET /api/v1/history`
- `POST /api/v1/ingest`
- `GET /api/v1/internal/nodes`
- `GET /api/v1/internal/devices`
- `GET /metrics`

## Status and presentation model

Operational and telemetry state must have one source of truth. The CLI and web UI must not independently calculate whether a sensor, node, database, backup, web endpoint or other component is healthy.

A shared status service should build a normalized status snapshot from the same underlying measurements, device state, component health and operational checks. That model is exposed through the internal API and rendered by different clients.

For normal runtime inspection:

```text
status/health services
        |
        +-- /api/v1/internal/status
        |       |
        |       +-- authenticated web status dashboard
        |       +-- `outpost status`
        |
        +-- /api/v1/internal/health
                |
                +-- health checks / monitoring
                +-- `outpost health`
```

The same information may therefore appear as graphical cards in the authenticated web UI and as tables, sections and status indicators in the CLI. Domain-specific views such as weather, system, astro, energy or home/site status should reuse the same API data rather than duplicate business logic in each presentation layer.

`outpost status` is intended to display the current state. `outpost doctor` may perform deeper active diagnostics and explain failures, for example configuration validation, database writability, migration state, SDR visibility, `rtl_433` availability, stale sensors, disk space, backup freshness, reverse-proxy reachability, HTTPS certificate validity and optional NAS availability.

Administrative or recovery commands such as install, restore or operations required while the daemon is unavailable may use local system facilities directly; the shared-endpoint rule applies to runtime state and telemetry presentation, not to offline recovery actions.

## Dashboard model

The web UI is a single-page dashboard composed of cards.

Examples:

- current weather
- history preview
- system status
- all-sky latest image
- top night media
- node health
- astro status
- garden status
- lightning status
- energy/PV and EV charging status
- authenticated home/site status from selected smart-home integrations

Kraków Lab may show only a few cards. Głębokie Field Outpost may show many. Public and authenticated/internal views may expose different cards and data.

## Logging and observability

Logging, health, heartbeat and system metrics are core features.

Required from early versions:

- structured logs
- log rotation or stdout JSON mode
- system events in the database
- health endpoint
- terminal system metrics
- last measurement age
- component status

Future:

- Prometheus-compatible `/metrics`
- optional Grafana dashboard
- optional Loki/log viewer

## Security model

- Public API: read-only, limited data.
- Internal API: token-protected.
- Ingest API: token-protected, preferably per-node token later.
- Config and secrets must be separated.
- TLS/SSL handled by reverse proxy or tunnel.
- App should not be directly exposed to the internet.
- Smart-home state and other privacy-sensitive site information belongs only in authenticated/internal views.
- Active control/automation is not part of the generic telemetry core and requires a separately designed authenticated control layer.

## Deployment readiness

Primary v0.1 path: native Python + systemd.

Design should remain compatible with:

- local development
- native systemd install
- Docker Compose
- Kubernetes later

Use config/env for paths, node identity, storage and module settings.
