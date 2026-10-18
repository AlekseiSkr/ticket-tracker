# Demo data (seed)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (commands); the live reset workflow comes in Phase 5 |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | `manage.py seed_demo`, `manage.py seed_users`; GitHub Actions "Reset demo data" workflow |
| **Cost**     | $0 |
| **Depends on** | [database.md](database.md), [file-storage.md](file-storage.md) |

## What
`seed_demo --reset --seed=42` generates realistic, deterministic data:
- 25 agents, about 4k customers and 40 tags
- **about 25k tickets** in states consistent with the workflow, with realistic timestamps
  and some SLA breaches
- **about 61k comments** (about 2.4 per ticket), 5% with attachments that reuse three sample files

`seed_users` creates a Lead and an Agent login for each of the two reviewers, each with its own
password from an env var. The seed never
touches user accounts.

## Why
The brief asks for "more rather than less" data, so that list views, filters, search and
inlines behave as they would at real scale.

The live reset is a **manual GitHub Actions job**. There's no admin button, because a
destructive button in production is a smell.

**Rejected:**
- **Fixtures (JSON):** huge, and static.
- **Seeding on every deploy:** would wipe reviewers' changes mid-review.

## How it's set up
- **Local:** copy the four `DEMO_*_PASSWORD` placeholders from `.env.example` into `.env`, then run
  `docker compose exec web python manage.py seed_users` and
  `docker compose exec web python manage.py seed_demo --reset`. About 30 s for 25k tickets.
- **Production (first time):** `fly ssh console -C "python manage.py seed_users"` (passwords
  from Fly secrets), then `fly ssh console -C "python manage.py seed_demo --reset"`.
- **Live:** GitHub → Actions → *Reset demo data* → Run workflow. It runs
  `fly ssh console -C "python manage.py seed_demo --reset"`.

## Who owns what
- **Demo-user passwords:** password manager, sent to reviewers privately.

## Gotchas
- **`bulk_create` skips model `clean()` and `save()`.** The generator must produce
  already-valid states, and a test asserts the seeded data satisfies every rule.
- **Customer emails use the reserved `.example` domain**, so no real address ever appears.
- **`--reset` deletes only `seed-*` agent users.** Real and demo accounts stay; their old
  tickets go with the rest of the demo data.

## Open items
- [x] Built in Phase 1 (2026-10-18). About 30 s locally for 25k tickets.
- [ ] Measure against Neon (target < 3 min, spike S7) on the first production seed.
- [ ] Phase 5: the GitHub Actions *Reset demo data* workflow.
