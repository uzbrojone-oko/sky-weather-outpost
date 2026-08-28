# Roadmap

## v0.1 — Kraków Lab MVP

Goal: first living outpost.

- Config loader with `krakow.yaml`.
- JSONL replay input.
- Real sanitized `rtl_433` fixtures captured from the Kraków sensor.
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
- Healthcheck CLI/script.
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

## v0.5 — Głębokie field config

- `glebokie.yaml` example.
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
- Ready to run on Kraków Lab and Głębokie Field Outpost.

## Future modules — Energy, PV and EV charging

Energy integrations should build on the generic measurement, device and agent architecture rather than introduce vendor-specific concepts into the core.

### Photovoltaics and site energy

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

### EV charger / wallbox

- Pluggable EV charger integrations through adapters or agents.
- Charger availability, connection and charging-session status.
- Live charging power, current and energy delivered.
- Charging-session history with start/end time, duration and energy consumed.
- Optional vehicle state-of-charge when exposed by the charger or a separate vehicle integration.
- EV charging card on the main dashboard.
- Correlate charging consumption with photovoltaic production and grid import/export.
- Future PV-surplus charging mode when supported by the installation and charger.
- Future configurable charging limits and schedules through a dedicated automation/control layer.
- Keep charger/vendor protocols and control logic outside the generic telemetry core.

> Future scope only. Energy, PV and EV charging integrations must not expand the v0.1 Kraków Lab MVP. Initial implementations should be read-only telemetry; active control and automation belong to a later, explicitly designed control layer.
