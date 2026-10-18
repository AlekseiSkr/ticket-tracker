# Authentication and roles

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (roles, 2026-10-18); GitHub OAuth planned (Phase 4) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | Django auth + admin; django-allauth (Phase 4); GitHub OAuth App |
| **Cost**     | $0 |
| **Depends on** | [admin-ui.md](admin-ui.md), [configuration-and-secrets.md](configuration-and-secrets.md) |

## What
Login goes through Django's own auth. Passwords are hashed with **Argon2** (PBKDF2 kept as a
fallback), sessions are DB-backed, cookies are Secure, HttpOnly and SameSite=Lax, and
sessions last 8 h.

**Roles:**
- **Support Lead:** full access.
- **Agent:**
  - sees only their own tickets plus the unassigned queue
  - priority and assignee are read-only, and "close" isn't available
  - no Agents, Users or Groups pages
  - no delete buttons
- **Viewer:** only if self-signup is enabled. Read-only, with customer email masked.

Checks use custom **permissions**, not group names. Optional login with **GitHub OAuth**:
new users get no access until a Lead approves them.

## Why
The brief wants roles that visibly change what a user sees, not a flag that only blocks
requests. Django's per-request admin hooks make the restriction visible. OAuth users with
no role by default answer "does a new OAuth user get a role automatically, and is that
safe?"

**Rejected:**
- **A boolean `is_lead` flag:** doesn't gate anything by itself.
- **django-axes for brute-force protection:** allauth's `secure_admin_login` routes the
  admin login through allauth's rate limits instead, so it isn't needed.
- **Google OAuth:** needs a consent-screen setup; GitHub is simpler for reviewers.

## How it's set up
**Phase 1 (live since 2026-10-18):**
- `tickets/migrations/0002_roles.py` creates the groups and their permissions.
  - **Support Lead:** `view_all_tickets`, `assign_ticket`, `close_ticket`, `change_priority`,
    and the model permissions, with no ticket or comment delete.
  - **Agent:** view, add and change tickets; view and add comments; view, add and change
    customers; view tags. Nothing on agents, users or groups, so those pages and the WIP caps
    stay hidden.
- **Code checks permissions, never group names:**
  - `Ticket.objects.visible_to()` limits Agents to their own tickets plus the queue. Another
    agent's ticket is not found.
  - `TicketAdmin.get_readonly_fields` makes priority and assignee read-only for Agents.
  - `get_actions` removes assign, close and priority actions.
  - The model methods re-check permissions, so the rules hold outside the admin too.
- A demo user per role comes from `seed_users`, with passwords from env vars that are never
  committed.

**Phase 4 (OAuth):**
1. https://github.com/settings/applications/new: create an OAuth App.
   - Homepage: `https://<app>.fly.dev`
   - Callback: `https://<app>.fly.dev/accounts/github/login/callback/`
   - Create a second app for local use with `http://localhost:8000/...`.
2. `fly secrets set GITHUB_OAUTH_CLIENT_ID=… GITHUB_OAUTH_CLIENT_SECRET=…`
3. `ALLAUTH_TRUSTED_CLIENT_IP_HEADER = "Fly-Client-IP"`, so rate limits key on the real
   client IP.
4. Rate limits are stored in `DatabaseCache`, which is shared across gunicorn workers.

## Who owns what
- **GitHub OAuth App:** Aleksei's GitHub account.
- **Client secret:** Fly secrets + password manager.
- **Demo-user passwords:** password manager. They're sent to reviewers privately, never put
  in the README.

## Gotchas
- **Hiding a field isn't enough.** It must also be removed from `search_fields`, list
  filters, autocomplete results, error messages and the AI context. A leak-sweep test logs
  in as an Agent and checks every admin URL.
- **Rate limits behind Fly's proxy** must use `Fly-Client-IP`, or every user shares one
  limit.

## Open items
- [ ] **Waiting on Benrey (asked 2026-10-15):** pre-made accounts only, or self-signup as
  well? This decides whether the Viewer role is built.
- [ ] How many reviewers will log in (one account each)?
