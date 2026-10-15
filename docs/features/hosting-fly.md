# Hosting (Fly.io)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live since 2026-10-15 at https://aleksei-ticket-tracker.fly.dev/ |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Fly.io personal org (slug `personal`, dashboard name `aleksei-613`), app **`aleksei-ticket-tracker`**, region `fra`, 1 × shared-cpu-1x 512 MB (machine `286557e7c04708`), shared IPv4 + dedicated IPv6 |
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
What was done on 2026-10-15:
1. Installed flyctl v0.4.118 (`iwr https://fly.io/install.ps1 -useb | iex`, which goes to
   `%USERPROFILE%\.fly\bin`), then `fly auth login`.
2. `fly apps create aleksei-ticket-tracker --org personal`. `ticket-tracker` was taken, since
   app names are global. `--org aleksei-613` is rejected by `apps create`, although
   `orgs show aleksei-613` resolves to the personal org.
3. Secrets staged with `fly secrets import --stage` (values from stdin, never in shell
   history), then `fly deploy --remote-only --ha=false`. The image is 87 MB, and
   `release_command` migrated Neon.

To rebuild from nothing, the steps are:
4. Set the secrets (see [configuration-and-secrets.md](configuration-and-secrets.md)):
   `fly secrets set DJANGO_SECRET_KEY=… DJANGO_ALLOWED_HOSTS=<name>.fly.dev DJANGO_CSRF_TRUSTED_ORIGINS=https://<name>.fly.dev DATABASE_URL=… S3_ENDPOINT_URL=… S3_BUCKET=… S3_ACCESS_KEY_ID=… S3_SECRET_ACCESS_KEY=…`
5. `fly deploy --ha=false`. Later deploys go through CI ([ci-cd.md](ci-cd.md)).
6. Create the first admin: `fly ssh console -C "python manage.py createsuperuser"`.
7. Check: `curl https://<name>.fly.dev/healthz` and `/readyz`.

**Verified live on 2026-10-15:**
- `/healthz` ok, `/readyz` with the database up
- `/admin/login/` returns 200, TTFB about 0.25 s (from Estonia)
- HTTP redirects to HTTPS (301)
- hashed static CSS returns 200
- headers present: HSTS 1 year, X-Frame-Options DENY, nosniff
- Fly check: 1 of 1 passing

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
- **App names are global across Fly.** `ticket-tracker` was taken.
- **Use `--ha=false` on deploy.** By default Fly creates 2 machines for availability, which
  would double the cost.
- **`S3_REGION` and `S3_ADDRESSING_STYLE` are set both as secrets and in `fly.toml [env]`.**
  Secrets win when both exist.
- **flyctl lives in `%USERPROFILE%\.fly\bin`.** Shells opened before the install don't have it
  on PATH.

## Open items
- [x] Create the Fly account and app (done 2026-10-15).
- [x] Create the first admin user (done 2026-10-15 by Aleksei; password in the password
  manager). The command needs `--pty`:
  `fly ssh console -a aleksei-ticket-tracker --pty -C "python manage.py createsuperuser"`.
  Without `--pty`, Django skips the prompts with "not running in a TTY".
- [ ] Spike S1: warm changelist p50 ≤ 400 ms from the EU, first request after Neon idle ≤ 2 s.
- [ ] Spike S9: gunicorn RSS < 400 MB under a 20-user load test.
