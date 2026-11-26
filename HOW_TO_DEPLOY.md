# How to Deploy Track (Server Deployment)

This guide covers deploying the full stack on a server. The app is three
containers — PostgreSQL, the FastAPI backend, and the Next.js frontend — defined
in [`docker-compose.yml`](docker-compose.yml). Locally, `docker compose up` is
all you need; for a real server you add a reverse proxy with TLS and change a few
settings. For local development, see [HOW_TO_RUN.md](HOW_TO_RUN.md).

---

## 1. Prerequisites

- A Linux host (VM, droplet, EC2, etc.) with **Docker Engine** and the **Docker
  Compose plugin** installed.
- A domain name pointing at the host (for TLS), if you want HTTPS.
- Ports **80/443** open to the internet. Do **not** expose Postgres (5432) or the
  app ports (3000/8000) publicly — put everything behind the proxy.

---

## 2. One critical setting: the public API URL

`NEXT_PUBLIC_API_URL` is **baked into the frontend at build time** and is used by
the browser, so it must be the **publicly reachable** API URL — never
`localhost` in production.

The recommended layout is a **single domain**: the proxy routes `/api/*` to the
backend and everything else to the frontend. Then set, in `docker-compose.yml`
under `frontend.build.args`:

```yaml
NEXT_PUBLIC_API_URL: https://track.example.com/api/v1
```

Because the browser calls the API on the same origin, CORS is a non-issue. (If
you instead host the API on a separate subdomain, set
`NEXT_PUBLIC_API_URL: https://api.example.com/api/v1` and add that frontend
origin to the backend's `BACKEND_CORS_ORIGINS`.)

Also change the backend env for production in `docker-compose.yml`:

- Set a strong `POSTGRES_PASSWORD` on `db` and the matching `DATABASE_URL` on
  `backend`.
- `APP_NOW` is a **simulated clock** for this assessment. For a real deployment
  you would remove it so the app uses real time — note this changes which week is
  "current" and what counts as overdue.

---

## 3. Deploy

```bash
git clone <repo-url> track && cd track

# 1) Edit docker-compose.yml:
#    - frontend build arg NEXT_PUBLIC_API_URL -> your public API URL
#    - db POSTGRES_PASSWORD + backend DATABASE_URL -> a strong password
#    - remove the "ports:" host mappings for db/backend/frontend if the proxy
#      reaches them over the compose network (recommended)

# 2) Build and start in the background
docker compose up -d --build
```

The backend container applies migrations and the idempotent seed on start, so the
database comes up ready. Check health:

```bash
docker compose ps
docker compose logs -f backend          # watch migrate + seed + uvicorn
curl -s http://localhost:8000/api/v1/health
```

---

## 4. Reverse proxy + TLS

Run a proxy on the same host (as a container on the compose network, or on the
host). **Caddy** is simplest — it obtains and renews TLS automatically and
streams SSE correctly out of the box.

`Caddyfile`:

```
track.example.com {
    @api path /api/*
    handle @api {
        reverse_proxy backend:8000
    }
    handle {
        reverse_proxy frontend:3000
    }
}
```

Add Caddy as a service in compose (sharing the network), mapping host 80/443 to
it, and drop the public `ports:` on backend/frontend.

### SSE and nginx

The meeting uses **Server-Sent Events** (`GET /api/v1/meetings/{id}/events`).
Caddy handles these with no extra config. If you use **nginx**, you must disable
buffering for the API location or the live timer/updates will stall:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;          # required for SSE
    chunked_transfer_encoding off;
    proxy_read_timeout 1h;        # long-lived stream
}
```

(The backend already sends `X-Accel-Buffering: no`, which nginx also respects.)

---

## 5. Database options

- **Bundled Postgres (default):** data persists in the named volume
  `track_pgdata`. Back it up regularly, e.g.:
  ```bash
  docker compose exec -T db pg_dump -U postgres track_db > backup-$(date +%F).sql
  ```
- **Managed Postgres (RDS/Cloud SQL):** remove the `db` service and the
  `depends_on`, and point `DATABASE_URL` at the managed instance. Migrations and
  the seed still run from the backend entrypoint on first start.

---

## 6. Updates

```bash
git pull
docker compose up -d --build        # rebuilds changed images; migrations re-run
```

Migrations are idempotent (Alembic `upgrade head`) and the seed will not
duplicate data.

---

## 7. Security checklist

- [ ] Strong `POSTGRES_PASSWORD`; `DATABASE_URL` updated to match.
- [ ] No public `ports:` for db/backend/frontend — only the proxy is exposed.
- [ ] TLS on 443 (Caddy/Let's Encrypt).
- [ ] `NEXT_PUBLIC_API_URL` is the public HTTPS URL.
- [ ] Decide on `APP_NOW` (simulated vs real time).
- [ ] Regular database backups.

---

## 8. Scaling note

The real-time layer uses an **in-process** SSE broadcaster, so run the backend as
a **single worker** (the default here). To scale horizontally, replace the
broadcaster's publish step with a shared bus — **Postgres `LISTEN/NOTIFY`** is the
natural fit since Postgres is already a dependency (see
[ADR0009](adr/ADR0009.md)). Everything else (stateless REST, DB as source of
truth) scales normally.
