# Changelog

## Unreleased

### Added
- Configuration-based device registry keyed by normalized device keys.
- Five-second deduplication of normalized sensor readings.
- Collection of `battery_ok` for the City Lab weather sensor.
- Added an RTL-433 JSONL processor that filters configured devices and removes duplicate normalized readings.
- Added file-based JSONL replay for RTL-433 frames.
