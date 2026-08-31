# Roadmap

## v0.1 — City Lab MVP

Goal: first living outpost.

- Config loader with `city-lab.yaml`.
- JSONL replay input.
- Real sanitized `rtl_433` fixtures captured from the City Lab sensor.
- `rtl_433` raw JSON mapping for `inFactory-TH` id `166`, channel `1`.
- SQLite schema and migrations.
- Tables: `nodes`, `devices`, `raw_events`, `measurements`, `system_events`, `schema_migrations`.
- Store raw events separately from normalized measurements.
- Basic deduplication strategy placeholder.
- Structured logging.
- `GET /api/v1/public/current`.
- `GET /api/v1/internal/health`.
- Simple one-page dashboard with temperature, humidity, last seen, battery and system status.
- Document runtime requirements in `REQUIREMENTS.md`.
- Validate the MVP on desktop replay mode and on a Debian terminal.

## v0.2 — Live collector

- Live `rtl_433 -F json -C si` stdout input.
- Known devices filtering from config.
- Unknown devices tracked internally but not exposed publicly.
- Dedupe repeated frames.
- Last seen/stale status.
- Better operational logs.
- Terminal system metrics collector.
- Capture helper for full and filtered `rtl_433` JSONL feeds.

## v0.3 — Operability

- `install.sh` with dependency checks based on `REQUIREMENTS.md`.
- `update.sh`.
- `backup.sh`.
- `restore.sh`.
- systemd unit.
- Config/secrets split.
- Internal API token.
- Shared internal status model and `GET /api/v1/internal/status` endpoint as the common runtime source for CLI and authenticated web status views.
- `outpost status` for a concise current-state view with readable status indicators.
- `outpost health` / healthcheck CLI for application and API health.
- `outpost doctor` for deeper active diagnostics with pass/warn/fail checks and actionable failure details.
- Initial diagnostic checks for service/process state, database access and migrations, sensor freshness, disk space and configuration validity.
- Operational checks for web/API reachability and reverse-proxy state when configured.
- HTTPS/TLS status including certificate validity and remaining lifetime; certificate issuance and renewal remain the responsibility of Caddy/ACME or the configured reverse proxy rather than Outpost itself.
- Backup-on-demand through the CLI and backup freshness/status exposed through the shared status model.
- Authenticated web `System / Outpost Status` view reusing the same status endpoint as the CLI rather than implementing separate health logic.
- Safe database migration workflow.
- Native installation validation on a clean Debian/Ubuntu host.

## v0.4 — History, charts and derived weather data

- `GET /api/v1/history`.
- 24h temperature/humidity preview.
- Min/max values.
- Dashboard cards.
- Basic retention config.
- Dew point calculation.
- Simple dew-risk indicator.
- Data quality flags for stale, suspect and invalid readings.

## v0.5 — Core Bunker field config

- `core-bunker.yaml` example.
- Bresser 5-in-1 mapping based on a real captured payload.
- Wind/rain metrics.
- NAS archive/backup config placeholders.
- Field/outpost dashboard layout.
- Multiple node status within one site.

## v0.6 — Media foundation

- `media_assets` table.
- Media directory layout.
- Latest image placeholder.
- All-sky latest image support.
- Top-night metadata structure.
- Archive status: `local_only`, `pending_archive`, `archived`, `failed`.
- Configurable temporary retention for full-night frame dumps.
- Manual `keep/archive/delete` workflow before automated scoring.

## v0.7 — Observability integrations

- `/metrics` endpoint.
- Prometheus-compatible metrics.
- Docker Compose with optional Prometheus/Grafana.
- Technical dashboard examples.
- Node heartbeat visualization.
- Alerts for stale sensors, low disk space and failed backups.

## v0.8 — Agents and distributed nodes

- HTTP ingest endpoint.
- Per-node tokens.
- Heartbeat payload.
- Agent mode design.
- System metrics from remote nodes.
- Buffered/retried delivery when the hub is temporarily unavailable.
- Astro, garden and all-sky agents later.

## v0.9 — Observation readiness and Astro Score

- Derived observation-readiness service.
- Configurable Astro Score from available local data.
- Explainable score components rather than a single opaque number.
- Initial inputs: humidity, dew point/dew risk, wind, rain, sensor freshness and optional cloud score.
- Future inputs: all-sky cloud detection, lightning distance, Moon conditions and astro-node status.
- `GET /api/v1/public/astro-score` or equivalent dashboard payload.
- One-page dashboard card with score, recommendation and contributing warnings.
- Keep scoring optional and site-configurable.

## v1.0 — Stable local outpost

- Reliable install/update/backup/restore.
- Public/internal API split.
- One-page dashboard.
- Local-first storage.
- Operational documentation.
- Ready to run on City Lab and Core Bunker example deployments.

## Future modules

The modules below are possible post-v1.0 directions, not requirements for the current MVP or for reaching v1.0. They should build on the generic device, measurement, event and agent architecture and keep vendor-specific protocols outside the core.

Initial integrations should prefer read-only telemetry. Active control and automation should be introduced later through an explicitly designed control layer with authentication and appropriate safety boundaries.

### External telemetry publishing

Sky Weather Outpost may optionally publish a selected subset of locally collected measurements to one or more public weather, environmental or citizen-science services while keeping the local Outpost database as the source of truth.

- Pluggable outbound publisher adapters for third-party services.
- Start with a single well-supported public service before adding additional targets.
- Explicit per-site and per-metric allowlists so only intentionally selected data leaves the Outpost.
- Publish normalized measurements rather than raw radio frames or internal device metadata.
- Support service-specific authentication, station identifiers and payload mapping outside the generic core.
- Queue/retry transient delivery failures without blocking local collection or storage.
- Track publisher health, last successful upload and rejected/failed submissions through the Outpost status model.
- Respect provider rate limits and required reporting intervals.
- Keep credentials in the secrets/config layer and never in the public repository.
- Make external publishing opt-in and independently disableable per target.
- Evaluate suitable services later, for example public personal-weather-station or environmental-data networks, based on available measurements and their API requirements.

### Energy, PV and EV charging

#### Photovoltaics and site energy

- Pluggable inverter integrations through adapters or agents.
- Live photovoltaic power monitoring.
- Daily and total energy production.
- Inverter status and temperature where available.
- Optional grid import/export power and energy telemetry.
- Optional battery state-of-charge, charge/discharge power and energy telemetry.
- Support future smart-meter and energy-meter integrations.
- Historical PV and site-energy charts.
- Energy/PV card on the main dashboard.
- Correlate photovoltaic production with local weather and all-sky conditions.
- Allow multiple inverters, meters, batteries and other energy-related devices per site.
- Keep vendor-specific inverter and meter protocols outside the generic core.

#### EV charger / wallbox

- Pluggable EV charger integrations through adapters or agents.
- Charger availability, connection and charging-session status.
- Live charging power, current and energy delivered.
- Charging-session history with start/end time, duration and energy consumed.
- Optional vehicle state-of-charge when exposed by the charger or a separate vehicle integration.
- EV charging card on the main dashboard.
- Correlate charging consumption with photovoltaic production and grid import/export.
- Future PV-surplus charging mode when supported by the installation and charger.
- Future configurable charging limits and schedules through the control/automation layer.
- Keep charger/vendor protocols outside the generic telemetry core.

### Home Assistant and smart-home integration

Home Assistant should remain the home-automation and device-control layer, while Sky Weather Outpost can consume, correlate and present selected smart-home state alongside environmental, energy and infrastructure telemetry.

- Pluggable Home Assistant integration through an adapter or agent.
- Consume selected Home Assistant entities through supported APIs, WebSocket events or MQTT where appropriate.
- Map selected entities onto generic Outpost devices, measurements, statuses and events rather than introducing Home Assistant-specific concepts into the core.
- Support read-only state telemetry for devices such as shutters/blinds, switches, relays, lights, technical sensors and other selected home infrastructure.
- Allow Outpost telemetry and derived values to be exposed back to Home Assistant where useful, including weather sensors, node health, Astro Score, all-sky status and energy data.
- Add an authenticated internal `Home / Site Status` dashboard separate from the public weather/sky view.
- Example status cards: PV production and energy flow, EV charging, shutter/blind position, selected circuits/devices, technical temperatures and integration health.
- Allow site configuration to explicitly select which Home Assistant entities are imported and displayed.
- Track Home Assistant connection/heartbeat state and stale entity data.
- Keep Zigbee, Z-Wave, ESPHome, Shelly and other device-specific protocols behind Home Assistant when HA already provides the integration.
- Route future active smart-home actions through the dedicated control/automation layer rather than the generic telemetry core.
