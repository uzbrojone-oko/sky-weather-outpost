# Architecture

## Purpose

Sky Weather Outpost is a configurable local hub for telemetry, environment data, media observations and node health.

It must not be designed as a weather-only application. Weather, all-sky, astro, garden, lightning and system metrics are modules/domains. The core stays generic.

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

Initial endpoints:

- `GET /api/v1/public/current`
- `GET /api/v1/public/dashboard`
- `GET /api/v1/internal/health`
- `GET /api/v1/internal/system`

Future endpoints:

- `GET /api/v1/history`
- `POST /api/v1/ingest`
- `GET /api/v1/internal/nodes`
- `GET /api/v1/internal/devices`
- `GET /metrics`

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

Kraków Lab may show only a few cards. Głębokie Field Outpost may show many.

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

## Deployment readiness

Primary v0.1 path: native Python + systemd.

Design should remain compatible with:

- local development
- native systemd install
- Docker Compose
- Kubernetes later

Use config/env for paths, node identity, storage and module settings.
