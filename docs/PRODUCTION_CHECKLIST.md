# SquiidWiki — Production Hardening Checklist

Mark items ✅ when complete. Items marked ⚠️ are required before exposing to external users.

---

## Security

- [x] ⚠️ **Passwords hashed with argon2** (not bcrypt or MD5)
- [x] ⚠️ **JWT access tokens expire in 15 min**, refresh tokens rotate
- [x] ⚠️ **httpOnly refresh token cookie** (XSS-resistant)
- [x] ⚠️ **CORS restricted** to configured origins (`settings.cors_origins`)
- [ ] ⚠️ **`SECRET_KEY` is a random 32-byte hex value** — not the default `change-me-in-production`
- [ ] ⚠️ **`.env` is NOT committed to git** (verify `.gitignore` covers it)
- [ ] **Rate limiting** on auth + write endpoints via `slowapi` — confirm limits are reasonable for expected traffic
- [ ] **SQL injection** — all queries use parameterized statements (no raw f-string SQL). Verify with a code grep for `text(f"` patterns.
- [ ] **Audit log writes** confirmed working — create a record and check `audit_log` table

## Database

- [x] ⚠️ **Migrations applied** (`alembic upgrade head`) before starting backend
- [x] **Bilateral relationship trigger** enforces `set_a_id < set_b_id` at DB level
- [x] **Trigram indexes** on `name`/`nickname` columns for fuzzy search
- [ ] **`pg_dump` backup** scheduled — see backup procedure below
- [ ] **Restore tested** — verify a backup can be restored to a clean DB
- [ ] **`audit_log` retention** — confirm audit table is excluded from any data-pruning scripts

### Backup Procedure

```bash
# Manual backup
docker exec squiidwiki-db-1 pg_dump -U postgres squiidwiki_db \
  | gzip > backups/squiidwiki_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore
gunzip -c backups/squiidwiki_TIMESTAMP.sql.gz \
  | docker exec -i squiidwiki-db-1 psql -U postgres squiidwiki_db
```

Store backups outside the Docker volume (e.g., a mounted host directory or S3).

## Monitoring

- [x] **`/metrics` Prometheus endpoint** exposed at `http://localhost:8000/metrics`
- [x] **Prometheus scraping** configured in `infra/prometheus.yml`
- [x] **Grafana** provisioned with Prometheus datasource at `http://localhost:3000` (admin/admin)
- [ ] **Alert rules** — set up alerts for: p95 latency > 500ms, error rate > 1%, DB connection pool exhaustion
- [ ] **Uptime check** — external ping on `/health` endpoint

## Performance

- [x] **Materialized views** `member_stats` + `set_stats` refreshed every 5 min via APScheduler
- [x] **Cursor pagination** on high-volume endpoints (members, incidents)
- [ ] **EXPLAIN ANALYZE** run on: member search, set detail (friend/enemy lookup), incident participant join
- [ ] **p95 latency < 200ms** verified under seed data load (use `wrk` or `hey`)
- [ ] **Redis connection** confirmed active (`redis-cli ping` from backend container)

## Observability

- [x] **Request-ID header** (`X-Request-ID`) on all responses — correlate frontend errors with backend logs
- [x] **Structured JSON logging** via `structlog` — log lines include `request_id`, `level`, `event`
- [ ] **Log aggregation** — if deploying externally, pipe logs to Loki or a log shipper

## Accessibility (Frontend)

- [x] **Keyboard navigation** — sidebar links, forms, and modals are reachable by Tab
- [x] **Focus visible** — Tailwind's `focus-visible:ring` classes applied on interactive elements
- [ ] **ARIA labels** — verify screen-reader labels on: icon-only buttons, dialog close buttons, status badges
- [ ] **Color contrast** — verify WCAG AA contrast ratios on zinc-400 text over zinc-900 backgrounds
- [ ] **Reduced motion** — confirm modals/transitions respect `prefers-reduced-motion`

## Documentation

- [x] `docs/PRIVACY.md` — data handling policy
- [x] `docs/ARCHITECTURE.md` — system diagram and data flow
- [x] `docs/SCHEMA.md` — entity relationships and FuzzyDate spec
- [x] `docs/API.md` — endpoint reference and curl examples
- [x] `docs/CONTRIBUTING.md` — dev setup, migrations, testing
- [x] `.env.example` — all required env vars documented with comments

## Before First External User

- [ ] Change `GF_SECURITY_ADMIN_PASSWORD` in docker-compose from `admin`
- [ ] Set a strong `SECRET_KEY` in `.env`
- [ ] Enable HTTPS (nginx reverse proxy with Let's Encrypt, or Cloudflare Tunnel)
- [ ] Review `CORS_ORIGINS` — remove `localhost` origins
- [ ] Run `$PY -m pytest --cov` — all green, ≥80% coverage
- [ ] Run `npx tsc --noEmit` in frontend — no type errors
