# Requirements

This document describes the runtime, system and optional integration requirements for Sky Weather Outpost.

The project is designed as a configurable local-first hub. A minimal installation must remain small, while optional modules may add SDR reception, reverse proxying, NAS archiving, observability and container deployment.

## 1. Supported operating environment

Primary native target:

- Debian or Ubuntu Linux.
- systemd-based installation.
- x86_64 hardware such as HP thin clients or small PCs.
- Local SSD or other reliable local storage for the active database.

Development may be performed on Windows, Linux or macOS, but native integration and hardware tests must be validated on Debian/Ubuntu.

## 2. Minimum hardware

For the v0.1 City Lab MVP:

- 64-bit CPU.
- 2 GB RAM minimum; 4 GB or more recommended.
- 2 GB free disk space for the application, virtual environment, logs and initial database.
- Network access for installation and optional API exposure.

For live `rtl_433` collection:

- Compatible RTL-SDR receiver.
- USB port accessible to the host or container.
- Suitable antenna for the configured frequency.

For future all-sky/media workloads:

- Larger local SSD recommended.
- Storage size depends on image cadence and retention policy.
- NAS is optional and must not be required for normal hub operation.

## 3. Required system packages for v0.1

The native installation requires:

- `git`
- `curl`
- `ca-certificates`
- `python3`
- `python3-venv`
- `python3-pip`
- `sqlite3`

Recommended utility packages:

- `jq`
- `unzip`
- `wget`

Example installation:

```bash
sudo apt update
sudo apt install -y \
  git curl ca-certificates unzip wget \
  python3 python3-venv python3-pip \
  sqlite3 jq
```

The application installer should verify required commands before continuing and print actionable errors when a dependency is missing.

## 4. Additional packages for live RTL-SDR input

Required when the hub directly receives radio data:

- `rtl-433`
- `rtl-sdr`
- `jq` for shell-level diagnostics and capture scripts

Example installation:

```bash
sudo apt install -y rtl-433 rtl-sdr jq
```

Basic validation commands:

```bash
rtl_test
rtl_433 -F json -C si
```

The installer or runbook must account for the Linux DVB kernel driver claiming the SDR device. Any automatic remediation must be explicit and reversible; the installer must not silently blacklist kernel modules.

## 5. Python runtime and application dependencies

The native installation should use a dedicated virtual environment rather than installing project packages globally.

Expected native layout:

```text
/opt/sky-weather-outpost/          application code and virtual environment
/etc/sky-weather-outpost/          configuration and local secrets
/var/lib/sky-weather-outpost/      active database, runtime state and cache
/var/log/sky-weather-outpost/      native file logs when enabled
```

Initial Python dependency categories:

- FastAPI-compatible web framework and ASGI server.
- YAML configuration loading.
- Data validation and serialization.
- SQLite access and schema migration support.
- Structured logging.
- Test runner and HTTP test client for development.

Exact package versions must be declared in `pyproject.toml` and installed by the project installer.

## 6. Input requirements

### JSONL replay mode

The first development input is newline-delimited JSON produced by `rtl_433`.

Example capture command:

```bash
rtl_433 -F json -C si \
  | jq -c 'select(.model=="inFactory-TH" and .id==166 and .channel==1)' \
  >> data/raw_data/rtl433-live.jsonl
```

Repository tests should use small sanitized fixtures under:

```text
tests/fixtures/
```

Large live captures must remain outside Git.

### Live stdout mode

The live collector must support line-by-line JSON input from:

```bash
rtl_433 -F json -C si
```

### Future inputs

Planned but not required for v0.1:

- MQTT.
- HTTP ingest from remote agents.
- All-sky media workers.
- INDI/Ekos telemetry agents.
- Garden and lightning sensor nodes.

## 7. Database and storage requirements

For the first implementation:

- SQLite is the active local database.
- The database file must live on local storage, not on an SMB/NFS mount.
- Schema changes must be applied through migrations.
- Raw events and normalized measurements must be stored separately.
- Backup must use a SQLite-safe method rather than copying a busy database file blindly.

NAS usage is optional and limited to:

- database backups,
- configuration backups excluding secrets,
- selected all-sky images,
- timelapse source material retained for a configured period,
- final timelapses and manually or automatically selected media.

The hub must continue collecting data when the NAS is unavailable.

## 8. Configuration requirements

Configuration must be external to the application code.

Required concepts:

- `site`
- local hub `node`
- additional nodes
- devices
- enabled modules
- storage paths
- retention policy
- public/internal API settings
- timezone
- logging mode and level

Secrets must not be stored in committed YAML files.

Supported secret sources should eventually include:

- environment variables,
- local secrets file outside Git,
- Docker secrets,
- Kubernetes Secrets.

## 9. Networking and API requirements

The application must provide:

- versioned JSON API under `/api/v1/`,
- a one-page dashboard,
- public read-only endpoints,
- protected internal endpoints,
- health and readiness endpoints,
- future Prometheus-compatible `/metrics` output.

Default native binding should be local or explicitly configured. The application must not assume direct internet exposure.

## 10. Security requirements

Minimum security rules:

- Public API is read-only.
- Internal/admin endpoints require authentication.
- Future ingest endpoints use per-node credentials.
- Secrets are never committed to Git.
- TLS is terminated by a reverse proxy or trusted tunnel.
- Raw events, logs, paths and detailed system diagnostics are not public.
- API tokens must be revocable and scoped where practical.

Optional reverse proxies:

- Caddy as the preferred simple default.
- Nginx as a supported alternative.

Apache is not a project requirement.

## 11. Logging and observability requirements

Logging and node health are core features.

The application must support:

- structured logs,
- configurable log level,
- stdout logging for containers,
- rotation or journald integration for native installs,
- component-level health status,
- last-seen/stale tracking,
- terminal system metrics,
- future Prometheus/Grafana integration.

Initial terminal metrics should include where available:

- CPU usage,
- RAM usage,
- load average,
- free disk space,
- uptime,
- database size,
- log/media directory size,
- application and collector status,
- age of the latest valid sensor measurement.

## 12. Optional native integrations

### NAS

Depending on protocol:

```bash
sudo apt install -y cifs-utils
```

or:

```bash
sudo apt install -y nfs-common
```

NAS support must remain optional.

### Reverse proxy

Caddy or Nginx may be installed separately. TLS configuration is not part of the Python process itself.

### MQTT

A future deployment may use Mosquitto. It is not required for v0.1.

### Observability stack

Prometheus and Grafana are optional and should preferably be delivered through a separate Docker Compose profile rather than installed by the minimal native installer.

## 13. Container requirements

The application must remain container-ready:

- configuration through files and environment variables,
- persistent data under a mounted `/data` path,
- optional archive mount under `/archive`,
- logs to stdout/stderr,
- graceful shutdown,
- health/readiness endpoints,
- no assumption that the working directory is writable.

Direct SDR access from a container requires explicit USB device mapping. An alternative deployment is to run `rtl_433` on the host or in a dedicated container and deliver events through MQTT.

## 14. Kubernetes compatibility

Kubernetes is not a v0.1 deployment target, but the design should remain compatible with:

- ConfigMap,
- Secret,
- PersistentVolumeClaim,
- Service,
- Ingress,
- liveness and readiness probes,
- stdout JSON logs,
- separate server/collector/worker commands when needed.

## 15. Installer responsibilities

`scripts/install.sh` should eventually:

1. Validate supported OS and privileges.
2. Verify or install required system packages.
3. Create a dedicated service account.
4. Create native application directories with correct permissions.
5. Create and populate a Python virtual environment.
6. Install the application from the checked-out version.
7. Install or validate configuration.
8. Initialize or migrate the database.
9. Install and enable the systemd unit.
10. Run a health check and print useful next steps.

Optional integrations must be enabled explicitly, for example:

```text
--with-rtl433
--with-caddy
--with-nas-smb
--with-nas-nfs
--with-docker
```

The installer should be safe to run repeatedly and must not overwrite an existing configuration or database without confirmation and backup.

## 16. Not required for v0.1

The following are deliberately outside the first milestone:

- MQTT broker.
- Docker Compose production deployment.
- Kubernetes manifests.
- Prometheus and Grafana.
- NAS archive automation.
- All-sky image processing.
- Astro telemetry agent.
- Garden and lightning sensor agents.
- Automation or actuator control.
- Astro Score.

They are future modules and must not complicate the first City Lab implementation.
