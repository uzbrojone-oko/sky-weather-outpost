# Runbook

Operational notes for running and debugging Sky Weather Outpost.

## Run as systemd services

Install and start both services:

```bash
sudo install -m 644 deploy/systemd/sky-weather-outpost-ingest.service /etc/systemd/system/
sudo install -m 644 deploy/systemd/sky-weather-outpost-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sky-weather-outpost-ingest.service sky-weather-outpost-api.service
```

Check status:

```bash
sudo systemctl status sky-weather-outpost-ingest.service
sudo systemctl status sky-weather-outpost-api.service
```

Read recent logs or follow them live:

```bash
sudo journalctl -u sky-weather-outpost-ingest.service -n 50 --no-pager
sudo journalctl -u sky-weather-outpost-api.service -n 50 --no-pager
sudo journalctl -u sky-weather-outpost-ingest.service -f
sudo journalctl -u sky-weather-outpost-api.service -f
```

After updating code or service files, restart the app:

```bash
sudo systemctl restart sky-weather-outpost-ingest.service sky-weather-outpost-api.service
```

## Check API

The current public readings endpoint is available locally and to clients on the LAN:

```bash
curl http://127.0.0.1:8000/api/v1/public/current
```

## Check rtl_433 manually

```bash
rtl_433 -F json -C si
```

For the City Lab sensor:

```bash
rtl_433 -F json -C si | jq -c 'select(.model=="inFactory-TH" and .id==166 and .channel==1)'
```

## Replay data

```bash
outpost replay data/raw_data/rtl433-live.jsonl --config config/examples/city-lab.yaml
```

## Backup

```bash
./scripts/backup.sh
```

Backup should include:

- SQLite database
- config without secrets
- application version

## Restore

```bash
./scripts/restore.sh <backup-file>
```

Restore should:

- restore config
- restore database
- run migrations
- restart service
- run healthcheck

## Add new rtl_433 device

1. Capture raw JSON.
2. Identify `model`, `id`/native id, `channel`.
3. Build `device_key` as `rtl433:<model>:<channel>:<native_id>`.
4. Add device to config.
5. Add/adjust normalizer mapping if needed.
6. Restart/reload app.
7. Check internal devices/status.
8. Confirm public API only exposes intended devices.

## Common failures

### No sensor data

- Check `rtl_433` manually.
- Check SDR USB device.
- Check known devices config.
- Check logs for unknown device events.
- Check last measurement age.

### NAS unavailable

- Hub should continue working.
- Archive jobs should become pending/failed.
- Check mount and credentials.

### Disk filling up

- Check media dump retention.
- Check log rotation.
- Check DB size.
- Stop media capture if necessary.
