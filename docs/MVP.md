# MVP v0.1

## Goal

Build the smallest useful Sky Weather Outpost instance: City Lab temperature and humidity from one known `rtl_433` sensor, stored in SQLite and exposed via API and a simple dashboard.

## Included

- Python + FastAPI.
- YAML config.
- JSONL replay input first.
- SQLite database.
- Basic migrations.
- Tables:
  - `schema_migrations`
  - `nodes`
  - `devices`
  - `raw_events`
  - `measurements`
  - `system_events`
- `inFactory-TH` id `166`, channel `1` mapping.
- Temperature normalized to `C`.
- Humidity normalized to `%`.
- Public current endpoint.
- Internal health endpoint.
- One-page web dashboard.
- Structured logging.

## Not included in v0.1

- All-sky camera.
- Media processing.
- NAS archive.
- MQTT.
- Docker Compose.
- Kubernetes.
- Grafana/Prometheus.
- Astro agent.
- Garden node.
- Lightning sensor.
- Energy/PV, battery or smart-meter integrations.
- EV charger/wallbox integration.
- Home Assistant or other smart-home integrations.
- Rules/actions/automation or active device control.
- Public internet exposure.

Future modules are documented in `ROADMAP.md`; they must not expand the v0.1 scope.

## Success criteria

The app can read sample JSONL or live-compatible payloads, store raw and normalized data, and display:

- temperature
- humidity
- battery status
- last seen time
- basic app/database/sensor health

A user can run:

```bash
outpost replay data/raw_data/rtl433-live.jsonl --config config/examples/city-lab.yaml
outpost server --config config/examples/city-lab.yaml
```

and open the local dashboard.
