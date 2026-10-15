# Database (Postgres; Neon in production)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | In progress (local: Live; Neon: not yet created) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Local: `db` service (postgres:17-alpine). Prod: Neon, region **AWS Europe (Frankfurt) `aws-eu-central-1`**, project `ticket-tracker` |
| **Cost**     | $0 (Neon Free) |
| **Depends on** | [configuration-and-secrets.md](configuration-and-secrets.md), [hosting-fly.md](hosting-fly.md) |

## What
PostgreSQL 17. It runs in Docker locally and on Neon's managed serverless Postgres in
production. Django connects through `DATABASE_URL`.

## Why
- **Neon Free:** 100 CU-hours a month, 1 GB storage, 10 branches, no card, and data is never
  deleted when limits are hit (verified 2026-10-15 on neon.com/docs/introduction/plans).
- **Frankfurt:** Neon has no Stockholm region. The Fly app runs in `fra`, so the app and DB
  share a city. An admin page makes 10–15 queries, so a cross-region hop would add about
  0.3–0.45 s per page for reviewers in Estonia.

**Rejected:**
- **Supabase Free:** pauses projects after 1 week of inactivity.
- **Render Postgres Free:** expires after 30 days.
- **Fly Managed Postgres:** paid.
- **Neon London:** farther from Estonia than Frankfurt.

## How it's set up
1. https://console.neon.tech/signup: sign up (GitHub login is fine).
2. Create project `ticket-tracker`: Postgres **17**, region **AWS Europe (Frankfurt)**.
3. Dashboard → **Connect**: copy the **direct** connection string (host *without*
   `-pooler`), `sslmode=require`.
4. `fly secrets set DATABASE_URL='<direct string>'`, and store a copy in the password manager.
5. Migrations run automatically on every deploy (`release_command` in `fly.toml`).

## Who owns what
- **Neon account:** Aleksei.
- **Connection string:** Fly secrets + password manager.

## Gotchas
- **Use the direct URL, not `-pooler`.** The app is a long-lived server
  (`CONN_MAX_AGE=60`). The pooler is PgBouncer in transaction mode, which would require
  `DISABLE_SERVER_SIDE_CURSORS=True`.
- **Neon closes idle connections after 5 minutes.** `CONN_MAX_AGE=60` stays under that, and
  `CONN_HEALTH_CHECKS=True` drops dead ones before use.
- **Scale-to-zero can't be disabled on Free.** The first query after 5 min idle waits a few
  hundred ms. Never keep it warm with pings, because that burns the 100 CU-hours.
- **Running out of CU-hours suspends compute until next month.** Check usage in the Neon
  console before the review window.

## Open items
- [ ] Create the Neon project (2026-10-15: waiting on account setup).
- [ ] Check CU-hour usage before submitting and again during the review window.
