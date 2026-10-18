# tickets/management/commands/: seed commands

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-18 |
| **Updated**  | 2026-10-18 |
| **Where**    | `python manage.py seed_users`, `python manage.py seed_demo` |
| **Cost**     | $0 |
| **Depends on** | [../../../docs/features/demo-data.md](../../../docs/features/demo-data.md) |

## What
- `seed_users` creates or updates the two demo logins, `lead` (Support Lead) and `agent` (Agent), with Agent profiles. Passwords come from `DEMO_LEAD_PASSWORD` and `DEMO_AGENT_PASSWORD` and must pass Django's password validators.
- `seed_demo [--reset] [--seed 42] [--tickets 25000]` bulk-creates demo data:
  - 25 agents, about 4k customers and 40 tags;
  - tickets in workflow-consistent states, with about 10% SLA breaches;
  - about 2.4 comments per ticket;
  - attachments on 5% of comments, reusing three uploaded sample files.

## Why
- **Passwords from the environment:** they're never in git, and production uses Fly secrets.
- **Bulk inserts:** 25k tickets in about 30 s locally. Calling `transition_to()` per ticket would take many minutes on Neon.

**Rejected:**
- JSON fixtures: huge, and static.
- Seeding on deploy: it would wipe reviewers' changes.

## How it's set up
| File | Role |
|---|---|
| `seed_users.py` | The two demo accounts. |
| `seed_demo.py` | Demo data. `--reset` deletes tickets, comments, customers, tags and the `seed-*` agent users; real accounts stay. |

Order: run `seed_users` first, so the demo `agent` also gets open tickets.

## Who owns what
- **Demo passwords:** password manager and Fly secrets.

## Gotchas
- **`bulk_create` skips `save()` and `clean()`.** `seed_demo` writes states that already satisfy the rules, and `tests/test_tickets.py::test_seed_demo_obeys_the_workflow_rules` proves it.
- **Each agent keeps at least three free slots under their cap,** so the demo agent can still claim tickets.
- **Customer emails use the reserved `.example` domain,** so no real address ever appears.

## Open items
- [ ] Phase 5: a GitHub Actions "Reset demo data" workflow that runs `seed_demo --reset` on Fly.
