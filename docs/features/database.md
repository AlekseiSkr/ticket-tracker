# Database (Postgres; Neon in production)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (local: Docker; production: Neon since 2026-10-15) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Local: `db` service (postgres:17-alpine). Prod: Neon org `org-polished-butterfly-83708031`, project **`ticket-tracker` (`holy-block-87765409`)**, region **`aws-eu-central-1` (Frankfurt)**, Postgres 17.11, database `neondb`, endpoint `ep-long-star-batabne7` (direct, non-pooled) |
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
Done on 2026-10-15 with the Neon CLI (`npm i -g neon`, v8.7.1):
1. `neon login` (browser OAuth).
2. Create the project:
   `neon projects create --name ticket-tracker --region-id aws-eu-central-1 --org-id org-polished-butterfly-83708031 --pg-version 17`
3. Take the project's **direct** connection URI (host without `-pooler`, `sslmode=require`)
   and import it as the Fly secret `DATABASE_URL`, via `fly secrets import` so it never
   appears in shell history.
4. Migrations run automatically on every deploy (`release_command` in `fly.toml`). The first
   one ran on 2026-10-15.

**Verified on 2026-10-15:** connected from local Docker (about 52 ms per query from Estonia),
and the live `/readyz` returns `{"database": "up"}`.

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
- [x] Create the Neon project (done 2026-10-15).
- [ ] **Delete the unused project `benrey` (`fancy-hill-70406886`, `aws-us-east-2`, Postgres 18).**
  It was created first, in the wrong region (Ohio, about 1 s of extra latency per admin
  page from Frankfurt), and its owner password was shared in a chat on 2026-10-15. Delete it
  in the Neon console, or reset the password if it's kept.
- [ ] Check CU-hour usage before submitting and again during the review window.
