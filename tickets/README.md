# tickets/: the support-ticket domain

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Planned (empty app; built in Phase 1) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `tickets/` (Django app `tickets`, admin section "Support") |
| **Cost**     | $0 |
| **Depends on** | [../docs/plan.md](../docs/plan.md), [../docs/features/admin-ui.md](../docs/features/admin-ui.md), [../docs/features/authentication-and-roles.md](../docs/features/authentication-and-roles.md) |

## What
The domain: `Customer`, `Agent`, `Ticket`, `Comment` and `Tag`. It holds the business rules
(status workflow, concurrency-safe claim, SLA) and the customised Django admin for them.

## Why
- **Business rules live on the models**, so admin actions, the seed command and tests all
  go through the same code.
- **Admin actions call model methods**, never `queryset.update()`, which would skip the rules.

**Rejected:**
- A separate `services.py` layer: the brief and the rubric expect logic on models.
- Putting the rules in admin views.

## How it's set up
| File | Role |
|---|---|
| `apps.py` | `TicketsConfig` (verbose name "Support"). |
| `models.py` | Phase 1: models, constraints, `Ticket.transition_to()`, `Ticket.claim()`, SLA annotations. Currently a placeholder. |
| `migrations/` | Generated migrations only (see [migrations/README.md](migrations/README.md)). |
| `admin.py` (Phase 1) | ModelAdmins, inlines, bulk actions, role-aware hooks. |
| `management/commands/seed_demo.py` (Phase 1) | Demo data (see [../docs/features/demo-data.md](../docs/features/demo-data.md)). |

## Who owns what
No credentials.

## Gotchas
- **Hiding a field from Agents means removing it everywhere:** fields, list display,
  filters, search, autocomplete, error messages and the AI context. The leak-sweep test
  enforces this.

## Open items
- [ ] Phase 1: build everything above (see the model and rule spec in [../docs/plan.md](../docs/plan.md)).
