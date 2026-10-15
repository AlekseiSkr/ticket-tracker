# Hosting (Fly.io)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Planned |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Fly.io, region `fra` (Frankfurt), app `ticket-tracker` (rename if taken), 1 × shared-cpu-1x 512 MB |
| **Cost**     | About $4.26/mo (calculated from Fly's regional pricing; `iad` list price is $3.69; confirm in the dashboard). No free tier for new orgs. |
| **Depends on** | [database.md](database.md), [file-storage.md](file-storage.md), [ci-cd.md](ci-cd.md) |

## What
The production `prod` Docker stage (gunicorn, non-root, WhiteNoise static files) runs on
one always-on Fly Machine in Frankfurt. HTTPS is terminated by Fly. Migrations run as
Fly's `release_command` before each release goes live.

## Why
- **Always on:** no cold starts.
- **Same image as CI:** what's tested is what runs.
- **Frankfurt:** colocated with Neon's Frankfurt region (see [database.md](database.md)).

**Rejected:**
- **Vercel Hobby ($0):** a non-commercial clause covering anyone "involved in any part of
  the production", a 4.5 MB request body cap, cold starts, and 1 h log retention.
- **Render Free:** about 1 min wake from sleep.
- **Render Starter ($7):** twice the price for the same thing.
- **Koyeb Free:** sleeps after 1 h, 0.1 vCPU.
- **Fly `arn` (Stockholm, closest to Estonia):** Neon has no Stockholm region, so it would
  cost about 0.3–0.45 s of extra DB latency per page.

## How it's set up
1. https://fly.io/app/sign-up: create an account and add a card (needed beyond the trial).
2. Install flyctl: https://fly.io/docs/flyctl/install/ (Windows:
   `pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"`), then `fly auth login`.
3. `fly apps create <name>`, then set `app = "<name>"` in `fly.toml`.
4. Set the secrets (see [configuration-and-secrets.md](configuration-and-secrets.md)):
   `fly secrets set DJANGO_SECRET_KEY=… DJANGO_ALLOWED_HOSTS=<name>.fly.dev DJANGO_CSRF_TRUSTED_ORIGINS=https://<name>.fly.dev DATABASE_URL=… S3_ENDPOINT_URL=… S3_BUCKET=… S3_ACCESS_KEY_ID=… S3_SECRET_ACCESS_KEY=…`
5. `fly deploy`. Later deploys go through CI ([ci-cd.md](ci-cd.md)).
6. Create the first admin: `fly ssh console -C "python manage.py createsuperuser"`.
7. Check: `curl https://<name>.fly.dev/healthz` and `/readyz`.

## Who owns what
- **Fly account and billing card:** Aleksei.
- **Deploy token:** GitHub Actions secret `FLY_API_TOKEN`.

## Gotchas
- **Fly health checks don't follow redirects** and need a 200. `/healthz` is answered before
  the HTTPS redirect for that reason (see [health-checks.md](health-checks.md)).
- **`auto_stop_machines` takes strings** (`"off"`/`"stop"`/`"suspend"`). `"off"` keeps the
  machine running. `min_machines_running` only matters when stopping is enabled.
- **`release_command` runs in a separate temporary machine.** It has the same secrets but no
  shared disk.
- **512 MB RAM:** gunicorn runs 2 workers × 4 threads. If memory runs short (spike S9), go to
  1 GB (about $7.7/mo in `fra`).
- **App names are global across Fly.** `ticket-tracker` may already be taken.

## Open items
- [ ] Create the Fly account and app (2026-10-15).
- [ ] Spike S1: warm changelist p50 ≤ 400 ms from the EU, first request after Neon idle ≤ 2 s.
- [ ] Spike S9: gunicorn RSS < 400 MB under a 20-user load test.
