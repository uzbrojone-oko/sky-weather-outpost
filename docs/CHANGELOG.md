# Changelog

## Unreleased

### Added
- Configuration-based device registry keyed by normalized device keys.
- Five-second deduplication of normalized sensor readings.
- Collection of `battery_ok` for the City Lab weather sensor.
- Added an RTL-433 JSONL processor that filters configured devices and removes duplicate normalized readings.
- Added file-based JSONL replay for RTL-433 frames.
- Added an RTL-433 JSONL replay command to the CLI with reading and metric counts.
- Added an initial versioned SQLite schema for nodes, devices, raw events, measurements and system events.
- Added SQLite storage for raw RTL-433 frames and normalized measurements.
- Connected CLI JSONL replay to SQLite persistence using the configured database path.
- Added live RTL-433 JSONL ingestion from stdin to SQLite through the CLI.
- Added a public current readings API and CLI command to serve it.
- Added a human-readable CLI command for the latest weather reading, selected by measurement time with a received-time fallback.
- Added a remote CLI mode that fetches and formats current weather from the public API.
- Added shared CLI configuration discovery via `--config`, `OUTPOST_CONFIG` and the default user config path.
- Added systemd units for continuous RTL-433 ingestion and API serving, with live ingest progress in logs.
