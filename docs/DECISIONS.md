# Decisions

Short records of decisions that changed or clarified the plan. Newest first.

## 2026-09 — Ingest and normalization

- **Declared vs incidental devices.** Devices listed in the site config are
  *declared*. Any other device heard on the radio is *incidental*: not an error,
  just outside the plan.
- **Measurements only from declared devices.** Every frame, including incidental
  ones, is stored in `raw_events`. A `measurement` is created only for declared
  devices. Promoting an incidental device means adding it to the config.
- **Metric naming.** Metric names carry no unit (`temperature`, `humidity`);
  the unit is a separate field (`C`, `%`).
- **Device key.** Four segments: `source:model:channel:id`. A missing channel is
  an empty segment, e.g. `rtl433:Toyota::<id>`.
- **Timestamps.** Source time without a timezone is interpreted in
  `site.timezone`. Stored timestamps are UTC. `received_at` is always UTC.
- **Deduplication.** rtl_433 repeats one reading 2-6 times within ~1-2 seconds.
  All frames stay in `raw_events`; identical frames within a short window
  produce one `measurement`. Basic dedupe moves into v0.1.
- **Optional fields.** `measurements` get nullable `quality` and `metadata`
  columns from the start.
- **Fixtures.** Real captures stay out of Git. Only small sanitized samples live
  in `tests/fixtures/`.
- **Reference environment.** HP t620 (Debian) is the bare-metal integration lab:
  rtl_433, RTL-SDR, systemd, install.sh, soak tests. Windows is for development
  and JSONL replay only.
- **Battery status.** `battery_ok` is stored as a regular measurement (`0`/`1`,
  unit `bool`), so it has history and reaches the dashboard like any other
  metric. The normalizer stays a pure function: it does not log or raise
  alerts. Detecting a transition (battery OK -> low), logging it as a
  `system_event` and alerting belong to a layer above the normalizer.
- **Normalizer scope.** The rtl_433 normalizer emits only known metrics
  (`temperature`, `humidity`, `battery_ok`). Other fields stay in the raw event.
  Judging plausibility (e.g. -35 C from a noise-decoded frame) is not its job;
  that is the `quality` flag in a later layer.
