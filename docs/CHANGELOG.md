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
