# Changelog

## Unreleased

### Added
- Query weather history over a custom ISO-8601 time range with selectable aggregation buckets.
- Reduce dashboard chart marker clutter while keeping full-resolution lines and adding hover details for each bucket.
- Export weather history as CSV with UTC bucket times and temperature and humidity aggregates.
- Save weather history command output directly to a path with `--output`.
- Add a dashboard selector for multiple configured weather sensors; keep it hidden for a single sensor.
- Show the configured weather sensor battery status in the dashboard footer.
- Format daily chart time labels in 24-hour `HH.MM` notation.
- Show hourly time labels on the daily weather charts, with spacing adapted to the available width.
- Improved dashboard chart axes with adaptive time labels, denser value ticks and a centered 0 °C reference line.
- Separated site, node and sensor labels in the example config, API payloads and dashboard.
- Added a local web dashboard with current readings and selectable temperature and humidity history charts.
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
- Made RTL-433 ingestion skip malformed frames without stopping the stream.
- Updated the City Lab example sensor and replay fixture to Bresser-3CH (ID 241).
- Added a public weather history API with temperature and humidity aggregates for day, week, month and year ranges.
- Added a terminal history command with local-time bucket summaries for day, week, month and year.

### Fixed
- Show the bucket duration beside the dashboard count of empty history intervals.
- Show the latest measurement age and count missing history buckets in the dashboard footer.
- Align daily chart labels with full clock hours and show the sensor name with a "Czujnik:" label.
- Mark midnight on daily weather charts to separate calendar days.
- Restored readable time labels on daily weather charts.
- Corrected the JSONL replay command examples in the README and Runbook to match the current CLI.
- Space chart time labels evenly across the requested period, including when measurements are sparse.
- Mark Mondays, month starts and year starts on weather charts; show monthly labels in the year view.
- Break chart lines and min–max ranges where one or more history buckets are missing.
