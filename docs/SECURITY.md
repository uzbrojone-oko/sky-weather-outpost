# Security

## Principles

- Public API is read-only and limited.
- Internal/admin API requires token.
- Ingest API requires token.
- Per-node ingest tokens should be supported later.
- Config and secrets are separated.
- No secrets in git.
- HTTPS is handled by reverse proxy or tunnel.
- App should not be exposed directly to the internet.
- Public dashboard must not expose raw/debug/system internals.

## API separation

Public/share endpoints:

```text
/api/v1/public/current
/api/v1/public/dashboard
/api/v1/public/media/top-night
```

Internal/admin endpoints:

```text
/api/v1/internal/health
/api/v1/internal/system
/api/v1/internal/nodes
/api/v1/internal/devices
/api/v1/internal/raw-events
```

Ingest endpoints:

```text
/api/v1/ingest
```

## Tokens

Use Bearer tokens:

```http
Authorization: Bearer <token>
```

Future tokens:

- admin token
- read-only internal token
- ingest token per node
- optional share token

## Secrets

Do not commit:

- `.env`
- API tokens
- Cloudflare/Tailscale tokens
- NAS passwords
- private certs/keys
- real production config with secrets

## TLS

Preferred approaches:

- Cloudflare Tunnel
- Tailscale/VPN for internal use
- Caddy reverse proxy
- Nginx + certbot

FastAPI should normally run behind a reverse proxy on `127.0.0.1:8000`.
