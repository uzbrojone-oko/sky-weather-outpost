# Roadmap

## v0.1 — Kraków Lab MVP

Goal: first living outpost.

- Config loader with `krakow.yaml`.
- JSONL replay input.
- `rtl_433` raw JSON mapping for `inFactory-TH` id `166`, channel `1`.
- SQLite schema and migrations.
- Tables: `nodes`, `devices`, `raw_events`, `measurements`, `system_events`, `schema_migrations`.
- Store raw events separately from normalized measurements.
- Basic deduplication strategy placeholder.
- Structured logging.
- `GET /api/v1/public/current`.
- `GET /api/v1/internal/health`.
- Simple one-page dashboard with temperature, humidity, last seen, battery and system status.

## v0.2 — Live collector

- Live `rtl_433 -F json -C si` stdout input.
- Known devices filtering from config.
- Unknown devices tracked internally but not exposed publicly.
- Dedupe repeated frames.
- Last seen/stale status.
- Better operational logs.

## v0.3 — Operability

- `install.sh`.
- `update.sh`.
- `backup.sh`.
- `restore.sh`.
- systemd unit.
- Config/secrets split.
- Internal API token.
- Healthcheck CLI/script.

## v0.4 — History and charts

- `GET /api/v1/history`.
- 24h temperature/humidity preview.
- Min/max values.
- Dashboard cards.
- Basic retention config.

## v0.5 — Głębokie field config

- `glebokie.yaml` example.
- Bresser 5-in-1 mapping.
- Wind/rain metrics.
- NAS archive/backup config placeholders.
- Field/outpost dashboard layout.

## v0.6 — Media foundation

- `media_assets` table.
- Media directory layout.
- Latest image placeholder.
- All-sky latest image support.
- Top-night metadata structure.
- Archive status: `local_only`, `pending_archive`, `archived`, `failed`.

## v0.7 — Observability integrations

- `/metrics` endpoint.
- Prometheus-compatible metrics.
- Docker Compose with optional Prometheus/Grafana.
- Technical dashboard examples.

## v0.8 — Agents and distributed nodes

- HTTP ingest endpoint.
- Per-node tokens.
- Heartbeat payload.
- Agent mode design.
- System metrics from remote nodes.
- Astro/garden/allsky agents later.

## v1.0 — Stable local outpost

- Reliable install/update/backup/restore.
- Public/internal API split.
- One-page dashboard.
- Local-first storage.
- Operational documentation.
- Ready to run on Kraków Lab and Głębokie Field Outpost.
