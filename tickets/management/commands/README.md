# tickets/management/commands/: seed commands

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-18 |
| **Updated**  | 2026-10-19 |
| **Where**    | `python manage.py seed_users`, `python manage.py seed_demo` |
| **Cost**     | $0 |
| **Depends on** | [../../../docs/features/demo-data.md](../../../docs/features/demo-data.md) |

## What
- `seed_users` creates or updates the reviewer logins: `lead-1`, `agent-1`, `lead-2` and `agent-2`, each with an Agent profile. Each has its own password from `DEMO_<ROLE>_<N>_PASSWORD`, which must pass Django's password validators.
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
| `seed_users.py` | A Lead and an Agent account for each of the two reviewers. |
| `seed_demo.py` | Demo data, in named steps: upload samples, agents, customers, tags, one planned ticket at a time (`_plan_ticket`), then comments and tags. `--reset` deletes tickets, comments, customers, tags and the `seed-*` agent users; real accounts stay. |

Order: run `seed_users` first, so the reviewer Agent accounts also get open tickets.

## Who owns what
- **Demo passwords:** password manager and Fly secrets.

## Gotchas
- **`bulk_create` skips `save()` and `clean()`.** `seed_demo` writes states that already satisfy the rules, and `tests/test_tickets.py::test_seed_demo_obeys_the_workflow_rules` proves it.
- **Each agent keeps at least three free slots under their cap,** so the demo agent can still claim tickets.
- **Customer emails use the reserved `.example` domain,** so no real address ever appears.

## Open items
- [x] A GitHub Actions "Reset demo data" workflow: not built (decided 2026-10-19); `fly ssh console -C "python manage.py seed_demo --reset"` does it.
