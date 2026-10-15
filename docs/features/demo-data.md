# Demo data (seed)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Planned (Phase 1) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `manage.py seed_demo`, `manage.py seed_users`; GitHub Actions "Reset demo data" workflow |
| **Cost**     | $0 |
| **Depends on** | [database.md](database.md), [file-storage.md](file-storage.md) |

## What
`seed_demo --reset --seed=42` generates realistic, deterministic data:
- 25 agents, about 4k customers and 40 tags
- **about 25k tickets** in states consistent with the workflow, with realistic timestamps
  and some SLA breaches
- **about 75k comments**, 5% with attachments that reuse about 10 sample files

`seed_users` creates one login per role, with passwords from env vars. The seed never
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
- **Local:** `docker compose exec web python manage.py seed_demo --reset`
- **Live:** GitHub → Actions → *Reset demo data* → Run workflow. It runs
  `fly ssh console -C "python manage.py seed_demo --reset"`.

## Who owns what
- **Demo-user passwords:** password manager, sent to reviewers privately.

## Gotchas
- **`bulk_create` skips model `clean()` and `save()`.** The generator must produce
  already-valid states, and a test asserts the seeded data satisfies every rule.
- **Use `example.com` emails only**, so no real addresses ever appear in the data.

## Open items
- [ ] Build in Phase 1. Measure seed time against Neon (target < 3 min, spike S7).
