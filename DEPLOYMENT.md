# Deployment

## Supported deployment modes

Planned modes:

1. Local development.
2. Native edge install with Python venv and systemd.
3. Docker Compose.
4. Kubernetes later.

The first real target is Debian/Ubuntu terminal with Python venv and systemd.

## Native layout

```text
/opt/sky-weather-outpost/          application code
/etc/sky-weather-outpost/          config and local secrets
/var/lib/sky-weather-outpost/      database, runtime, cache
/var/log/sky-weather-outpost/      logs
/mnt/nas/outpost/                  optional archive/backup
```

## Native install concept

```bash
git clone https://github.com/uzbrojone-oko/sky-weather-outpost.git
cd sky-weather-outpost
sudo ./scripts/install.sh --config config/examples/krakow.yaml
```

## systemd

Service name:

```text
sky-weather-outpost.service
```

Common commands:

```bash
sudo systemctl status sky-weather-outpost
sudo systemctl restart sky-weather-outpost
journalctl -u sky-weather-outpost -f
```

## Docker-ready design

The app should be configurable through mounted config/env and volumes:

```text
/app        code
/config     config
/data       DB/runtime/cache
/archive    optional NAS/archive mount
```

Docker Compose may later include:

- outpost
- mosquitto
- caddy/nginx
- prometheus
- grafana

## Kubernetes-ready design

Do not implement Kubernetes first, but keep the app compatible with:

- ConfigMap
- Secret
- PersistentVolumeClaim
- Service
- Ingress
- `/healthz`
- `/readyz`
- `/metrics`
- stdout JSON logs
- graceful shutdown

## Reverse proxy

Preferred default: Caddy.

Alternative: Nginx.

The app should listen locally, for example:

```text
127.0.0.1:8000
```

Reverse proxy handles:

- HTTPS/TLS
- public exposure
- optional rate limiting
- routing/blocking internal endpoints
