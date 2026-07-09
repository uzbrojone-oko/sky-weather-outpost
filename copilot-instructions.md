# Copilot instructions

## Project identity

This project is `sky-weather-outpost`.

It is a configurable local outpost hub for collecting, normalizing, storing and exposing telemetry, environmental sensor data, node health and future sky/media observations.

It is not a weather-only app.

## High-level rule

Build small, design wide.

The MVP is Kraków Lab temperature/humidity only, but the architecture must not block future all-sky, astro, garden, lightning, media, agents, Docker, Kubernetes or observability modules.

## Architecture rules

- Keep the core generic.
- Use the model: `site`, `node`, `device`, `measurement`, `event`, `media_asset`, `status`.
- Weather, all-sky, astro, garden, lightning and system metrics are modules/domains.
- Do not hardcode Kraków, Głębokie or any device ID in core logic.
- Site/node/device definitions must come from configuration.
- Prefer small modules over large files.
- Do not create a single giant `app.py`.
- Do not introduce microservices unless explicitly requested.
- Prefer modular monolith structure.

## MVP scope rules

For v0.1, implement only:

- config loading
- JSONL replay input
- `rtl_433` normalization for `inFactory-TH` id `166`
- SQLite storage
- raw events
- normalized measurements
- devices/nodes
- basic logging
- health endpoint
- public current endpoint
- simple dashboard

Do not implement all-sky, MQTT, NAS archive, Grafana, Kubernetes, agents, rules/actions or astro/garden modules unless explicitly requested for a later milestone.

## Data rules

- Preserve raw input separately from normalized data.
- Store raw JSON in `raw_events`.
- Store numeric values as normalized `measurements` with `metric`, `value`, `unit`.
- Do not create weather-specific tables like `weather_readings` unless explicitly asked.
- Do not store images/videos in SQLite.
- Media files should be files on disk/NAS and indexed later in `media_assets`.
- Use UTC or timezone-aware timestamps.
- Track `received_at`; keep source time as `measured_at` when available.

## Config rules

- Use YAML for application config.
- Use JSON for ingest/data payloads.
- Keep secrets outside config examples.
- Config examples must not contain real tokens/passwords.
- Paths must be configurable.
- The same codebase must work with different site configs.

## API rules

- Use API versioning: `/api/v1/...`.
- Separate public and internal APIs.
- Public API must be read-only and safe to share.
- Internal API requires token once auth is implemented.
- Ingest API requires token once implemented.
- Do not expose raw/debug/system internals through public API.

## Logging and observability rules

- Add structured logging to service/module boundaries.
- Log important lifecycle events: startup, config loaded, DB initialized, input started, event received, measurement stored, unknown device, errors.
- Important operational events should be storable as `system_events`.
- Add health/status endpoints early.
- System metrics and heartbeat are core concepts, even if minimally implemented first.

## Security rules

- No secrets in git.
- Config and secrets must be separated.
- Public endpoints are read-only.
- Internal/admin endpoints should require bearer token when implemented.
- TLS/SSL should be handled by reverse proxy/tunnel, not directly by FastAPI in normal deployment.

## Testing rules

Prioritize unit tests for:

- config loading
- rtl433 normalizer
- Fahrenheit to Celsius conversion
- known/unknown device matching
- duplicate frame handling
- public API not exposing private/debug data

## Style rules

- Prefer clear, boring code.
- Use type hints.
- Keep functions small.
- Use explicit names.
- Avoid premature abstraction, but do not hardcode core assumptions.
- Favor readable Python over cleverness.
