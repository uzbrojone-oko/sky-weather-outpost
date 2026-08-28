# Configuration

Configuration is YAML. Ingest/data payloads are JSON.

Each installation should be configured by site, node, enabled modules, devices, storage, API and dashboard settings.

Secrets must not be committed to git. Use environment variables or a local secrets file outside the repository.

## Example: Kraków Lab

```yaml
site:
  id: krakow
  name: "Kraków Lab"
  type: lab
  timezone: Europe/Warsaw

node:
  id: krakow-lab-t620
  role: hub

modules:
  rtl433:
    enabled: true
    mode: jsonl_replay
    replay_path: ./data/raw_data/rtl433-live.jsonl

  system_metrics:
    enabled: true
    interval_seconds: 60

storage:
  sqlite_path: ./data/outpost.sqlite

logging:
  level: INFO
  mode: stdout_json

api:
  host: 127.0.0.1
  port: 8000
  public_enabled: true
  internal_enabled: true

devices:
  - key: rtl433:inFactory-TH:1:166
    name: "Kraków weather shield"
    type: weather_sensor
    public: true
    match:
      source: rtl433
      model: inFactory-TH
      id: 166
      channel: 1
    metrics:
      - temperature
      - humidity

dashboard:
  cards:
    - current_weather
    - system_status
```

## Example: Głębokie Field Outpost

```yaml
site:
  id: glebokie
  name: "Głębokie Outpost"
  type: field
  timezone: Europe/Warsaw

node:
  id: glebokie-core-t620
  role: hub

modules:
  rtl433:
    enabled: true
    mode: mqtt
    mqtt_topic: rtl_433/+/events

  system_metrics:
    enabled: true
    interval_seconds: 60

  allsky:
    enabled: false

storage:
  sqlite_path: /var/lib/sky-weather-outpost/outpost.sqlite

archive:
  nas_enabled: true
  path: /mnt/nas/outpost

api:
  host: 127.0.0.1
  port: 8000
  public_enabled: true
  internal_enabled: true

devices: []

dashboard:
  cards:
    - current_weather
    - wind_rain
    - allsky_latest
    - top_night
    - system_status
```
