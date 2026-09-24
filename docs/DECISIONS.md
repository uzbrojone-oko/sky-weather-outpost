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
