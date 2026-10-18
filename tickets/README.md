# tickets/: the support-ticket domain

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (Phase 1, v0.1) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | `tickets/` (Django app `tickets`, admin section "Support") |
| **Cost**     | $0 |
| **Depends on** | [../docs/plan.md](../docs/plan.md), [../docs/features/admin-ui.md](../docs/features/admin-ui.md), [../docs/features/authentication-and-roles.md](../docs/features/authentication-and-roles.md) |

## What
The domain: `Customer`, `Agent`, `Ticket`, `Comment` and `Tag`. It holds:
- the business rules: the status workflow, a concurrency-safe claim with a work-in-progress cap, first-response stamping and SLA;
- the Django admin for them;
- the permission-checked attachment download.

## Why
- **Business rules live on the models,** so admin actions, buttons and tests all go through the same code.
- **Admin actions call model methods,** never `queryset.update()`, which would skip the rules.
- **One visibility rule** (`Ticket.objects.visible_to(user)`) feeds the ticket list, the customer page's ticket inline and the attachment view, so an Agent can't see another agent's tickets anywhere.

**Rejected:**
- A separate `services.py` layer: the brief expects logic on the models.
- Rules in admin views.
- `Count("comments")` in the list queryset: it grouped all 25k tickets (about 850 ms). A correlated subquery takes about 180 ms.
- A plain OFFSET for deep pages: Postgres ran the comment subquery for every skipped row (the last page took 521 ms in SQL, over 1.5 s in the admin). `IdsFirstPaginator` picks the page's 50 ids first, then annotates only those (43 ms).

## How it's set up
| File | Role |
|---|---|
| `models.py` | Models and constraints. `TicketQuerySet.visible_to()` and `.with_sla()` (`sla_due_at`, `is_sla_breached`, `age`, all sortable). `Ticket.transition_to()`, `.claim()`, `.assign()`, `.set_priority()`. `Comment.save()` stamps `first_response_at`. |
| `validators.py` | Attachment rules: allow-listed extensions checked by magic bytes, UTF-8 text check, 10 MB cap, random UUID keys. `CappedUploadHandler` refuses requests over 11 MB instead of dropping the file silently. |
| `admin.py` | Ticket, Customer, Agent and Tag admins: badges, filters (queue, status, priority, SLA, channel, assignee, tags), search (`#id`, subject, customer), comment inline, bulk actions, workflow buttons, role-aware fields and actions. |
| `views.py` | `/attachments/<comment_id>/`: a 60 s presigned download for visible tickets only, and 404 otherwise. |
| `migrations/` | Schema plus the role groups (see [migrations/README.md](migrations/README.md)). |
| `management/commands/` | `seed_users`, `seed_demo` (see [management/commands/README.md](management/commands/README.md)). |

**Workflow:**
- new → open needs an assignee.
- open ↔ pending customer.
- → resolved needs a public agent reply.
- resolved → closed is Lead only.
- A resolved ticket can be reopened. A closed one only by a Lead, within 14 days.
- Claiming a new ticket opens it.

**SLA (first response):** urgent 1 h, high 4 h, normal 24 h, low 72 h.

Tests: `tests/test_tickets.py`.

## Who owns what
No credentials.

## Gotchas
- **Hiding a field from Agents means removing it everywhere:** fields, list display, filters, search, autocomplete, error messages and the AI context. The leak-sweep test enforces this for tickets.
- **Comments are an append-only log.** The inline allows adding but never editing or deleting. The current user's Agent profile is set as the author before validation, so internal notes pass the "needs an agent" constraint.
- **Unfold badge maps must list every value.** A missing key shows the raw value (`pending_customer`) instead of the label.
- **Locks are always taken ticket first, then agent,** so concurrent claims can't deadlock.

## Open items
- [x] Phase 2: leak sweep extended to history, delete, workflow buttons and the assignee autocomplete (2026-10-18).
- [ ] Phase 3: the AI form assistant reads role-filtered form metadata from these admins.
