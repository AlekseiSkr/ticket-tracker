# Authentication and roles

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (roles and reviewer accounts, 2026-10-18) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | Django auth + admin; `tickets/migrations/0002_roles.py`; `manage.py seed_users` |
| **Cost**     | $0 |
| **Depends on** | [admin-ui.md](admin-ui.md), [configuration-and-secrets.md](configuration-and-secrets.md) |

## What
Login goes through Django's own auth:
- passwords are hashed with Django's default, **PBKDF2**;
- sessions are DB-backed and last 8 h;
- cookies are Secure, HttpOnly and SameSite=Lax.

**Roles:**
- **Support Lead:** full access.
- **Agent:**
  - sees only their own tickets plus the unassigned queue;
  - priority and assignee are read-only, and "close" isn't available;
  - no Agents, Users or Groups pages;
  - no delete buttons.

Checks use custom **permissions**, not group names.

**Accounts:** pre-made only, as Benrey asked on 2026-10-18 (two reviewers). Each reviewer gets their own Lead and Agent login (`lead-1`/`agent-1`, `lead-2`/`agent-2`), each with its own password. There's no self-signup.

## Why
The brief wants roles that visibly change what a user sees, not a flag that only blocks requests. Django's per-request admin hooks make the restriction visible.

Separate accounts per reviewer, rather than one shared login per role, keep each reviewer's actions apart: claims, comments and the history log. Neither reviewer holds the other's password.

**Rejected:**
- **A boolean `is_lead` flag:** doesn't gate anything by itself.
- **GitHub OAuth (planned as Phase 4, dropped 2026-10-18):** Benrey wants pre-made accounts only, so there's nobody to sign up.
- **The Viewer role (dropped 2026-10-18):** it existed only for self-signups.
- **One shared login per role:** both reviewers would act as the same agent.

## How it's set up
- **Groups:** `tickets/migrations/0002_roles.py` creates them with their permissions.
  - **Support Lead:** `view_all_tickets`, `assign_ticket`, `close_ticket`, `change_priority`, and the model permissions, with no ticket or comment delete.
  - **Agent:** view, add and change tickets; view and add comments; view, add and change customers; view tags. Nothing on agents, users or groups, so those pages and the WIP caps stay hidden.
- **Code checks permissions, never group names:**
  - `Ticket.objects.visible_to()` limits Agents to their own tickets plus the queue. Another agent's ticket is not found.
  - `TicketAdmin.get_readonly_fields` makes priority and assignee read-only for Agents.
  - `get_actions` removes the assign, close and priority actions.
  - The model methods re-check permissions, so the rules hold outside the admin too.
- **Reviewer accounts:** `seed_users` creates the four accounts. Passwords come from `DEMO_LEAD_1_PASSWORD`, `DEMO_AGENT_1_PASSWORD`, `DEMO_LEAD_2_PASSWORD` and `DEMO_AGENT_2_PASSWORD`, and must pass Django's password validators.
- **Production:**
  1. Set the four secrets: `fly secrets set DEMO_LEAD_1_PASSWORD=… DEMO_AGENT_1_PASSWORD=… DEMO_LEAD_2_PASSWORD=… DEMO_AGENT_2_PASSWORD=…`
  2. Run `fly ssh console -C "python manage.py seed_users"`.
  3. Send each reviewer their two logins privately.

## Who owns what
- **Reviewer passwords:** Fly secrets and the password manager. They're sent to each reviewer privately, never put in the README or a commit.

## Gotchas
- **Hiding a field isn't enough.** It must also be removed from `search_fields`, list filters, autocomplete results, error messages and the AI context. A leak-sweep test logs in as an Agent and checks every admin URL.
- **The admin login has no rate limit.** OAuth's allauth `secure_admin_login` was going to provide one, and it went with OAuth. Until Phase 5 adds one, the only defence is strong passwords.
- **Not Argon2 (switched 2026-10-18).** Django's Argon2 settings take 100 MB of memory per hash, and Django hashes even for unknown usernames. About six parallel anonymous login attempts would push the 512 MB VM out of memory. PBKDF2 is CPU-bound, with no memory spike. Existing Argon2 hashes still verify (`argon2-cffi` stays installed) and are rehashed to PBKDF2 at the next login. Rerunning `seed_users` rehashes the reviewer accounts at once.
  **Rejected:** keeping Argon2 with a lower `memory_cost` (a custom hasher subclass to maintain).

## Open items
- [x] **Benrey answered (2026-10-18):** pre-made accounts only, for two reviewers.
- [ ] **Phase 5:** rate-limit the admin login (django-axes, or a small cache-backed check keyed on `Fly-Client-IP`).
