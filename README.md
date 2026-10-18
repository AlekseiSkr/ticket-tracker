# Ticket Tracker

A support ticket tracker built on the Django admin. It's live at
**https://aleksei-ticket-tracker.fly.dev/**; reviewer logins are sent privately.

Detail lives in [docs/](docs/README.md):
- one doc per feature and external service: [docs/features/](docs/features/);
- the build plan: [docs/plan.md](docs/plan.md);
- operations: [docs/runbook.md](docs/runbook.md);
- product context and the admin's design system: [docs/PRODUCT.md](docs/PRODUCT.md),
  [docs/DESIGN.md](docs/DESIGN.md);
- a `README.md` in every code directory.

`CLAUDE.md` (working rules for coding agents) stays at the root, where Claude Code loads it.

## Introduction

**Actors**
- **Customer:** raises tickets and replies. Customers don't log in; agents record what they
  send by email, chat, phone or web.
- **Agent:** works the queue. Sees only their own tickets and the unassigned queue.
- **Support Lead:** sees everything; assigns, reprioritises, closes and reopens, and manages
  agents, tags and users.

**Views** (all inside `/admin/`)
| View | What it does | Who |
|---|---|---|
| Dashboard | Greeting and the sections this user may open | Both |
| Tickets list | Filters: queue (mine / unassigned), status, priority, SLA breached, channel, tags. Search: `#id`, subject, customer. Bulk actions: claim and resolve; Leads also get assign, set priority and close. Columns sort by SLA, age and comment count. | Both; an Agent's list is limited |
| Ticket page | Fields plus the workflow buttons (claim, waiting on customer, resolve, close, reopen). Comments inline: public replies, internal notes, or a message logged from the customer, with attachments. Assignee and status are read-only here; they change only through the buttons and bulk actions, which apply the rules. SLA deadline and history. | Both |
| Customers | Contact details with their tickets inline | Both; only Leads delete |
| Agents | Team, work-in-progress cap and open-ticket count | Leads |
| Tags, Users, Groups | Lookups and accounts | Leads manage tags and users; Agents only view tags |
| Form assistant | An "Ask about this form" panel on every add and change page. It explains the fields from the form itself, never from ticket data. | Both |

Outside the admin: `/attachments/<id>/` redirects to a 60-second presigned download, for
tickets the user may see. `/healthz` and `/readyz` are for the platform's health checks.

**Particulars**
- **Business rules live on the models,** and the admin only calls them.
  - Status changes only through the workflow: new → open needs an assignee; resolving needs
    a public agent reply; only a Lead closes, and reopens a closed ticket within 14 days.
  - First-response SLAs: urgent 1 h, high 4 h, normal 24 h, low 72 h.
  - Each agent has a cap on open tickets. Claims lock the rows, so two agents can't claim
    the same ticket.
- **Roles are checked by permission, never by group name.** A field hidden from a role is
  removed everywhere: forms, columns, filters, search, autocomplete and the AI's context.
- **Attachments:** PNG, JPG, PDF or TXT, checked by content, up to 10 MB. They're stored
  under random names in a private bucket.
- **Security:** ten failed logins from one IP block it for 15 minutes. A Content Security
  Policy allows only the app's own scripts. Errors go to Sentry without personal data.

## Stack

**Why Django:** its built-in admin generates exactly what this brief is about: list filters,
search, true inline formsets, permission-aware actions and per-request hooks that hide
fields by role. That left the time for the rules, roles and tests instead of UI plumbing.
Python is also one of the backend languages the role lists.

| Layer | Choice |
|---|---|
| App | Django 5.2 LTS, Python 3.13, uv |
| Admin UI | Django admin + Unfold, custom dark theme ([docs/DESIGN.md](docs/DESIGN.md)) |
| Database | Postgres 17: Docker locally, Neon (Frankfurt) in production |
| Files | Private S3 bucket: SeaweedFS locally, Cloudflare R2 (EU) in production |
| Hosting | Fly.io, Frankfurt, one always-on 512 MB machine |
| AI | Groq `openai/gpt-oss-20b`, called with the standard library |
| Monitoring | Sentry: errors (no personal data) and an uptime monitor on `/healthz`; Fly health checks |
| CI/CD | GitHub Actions: ruff, mypy, pytest (93% coverage gate), gitleaks, Docker build; deploys on green `main` |

## Setup

Locally, with Docker Desktop:

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py seed_users
docker compose exec web python manage.py seed_demo --reset
```

Then open http://localhost:8000/admin/ and log in with a `lead-1` or `agent-1` password from
`.env`.

| Task | Command |
|---|---|
| Tests | `docker compose exec web pytest` |
| Lint, format, types | `docker compose exec web ruff check . && docker compose exec web ruff format --check . && docker compose exec web mypy .` |
| Load report (25k tickets, timings) | `docker compose exec -e STRESS_TICKETS=25000 web pytest -m stress -s` |
| Stop / wipe data | `docker compose down` / `docker compose down -v` |

**Production:**
- Every setting comes from an environment variable, and a missing one stops the app at
  startup. The secrets live in Fly ([configuration-and-secrets.md](docs/features/configuration-and-secrets.md)).
- A green push to `main` deploys, and migrations run before the release goes live.
- Recovery steps are in the [runbook](docs/runbook.md).

## Implementation stages
| Stage | What shipped | Done |
|---|---|---|
| 0. Skeleton | Docker stack, settings, health checks, storage, CI, Fly deploy, docs | 2026-10-15 |
| Design | Admin theme, login, dashboard greeting, branded error pages | 2026-10-15 |
| 1. Core | Models and constraints, workflow rules, roles, admin, attachments, demo data | v0.1, 2026-10-18 |
| 2. Tests | All 25 status transitions, concurrent claims, a sweep of every URL an Agent could use to reach another agent's data, seed invariants | v0.2, 2026-10-18 |
| 3. AI assistant | Form-grounded answers, role-aware fields, question scrubbing, rate limit, help-text fallback | v0.3, 2026-10-18 |
| 4. OAuth | Dropped: the hiring team asked for pre-made reviewer accounts | 2026-10-18 |
| Review | Field picker for read-only fields, upload cap, faster deep pages and search, on-demand stress test | 2026-10-18 |
| 5. Hardening | Login rate limit, Content Security Policy, Sentry, runbook, this README | 2026-10-18 |

At 25,000 tickets, most admin pages answer in 0.1–0.3 s (median), each in 11 queries or fewer.

## Trade-offs
| Decision | Why | Rejected |
|---|---|---|
| Django admin, no custom frontend | A small domain done well beats more features done thinly. The time went into rules, roles and tests. | A separate SPA |
| Unfold | Maintained, dark mode, badges and action buttons | Jazzmin (many open bugs), Grappelli (no dark mode) |
| Neon | Free, EU, never expires | Supabase Free (pauses), Render Postgres (expires after 30 days) |
| Fly.io | Always-on container, no cold starts | Vercel Hobby (non-commercial clause, 4.5 MB bodies), Render Free (1 min wake) |
| Groq without an SDK | Free, OpenAI-compatible, no data retention. Any failure falls back to the help text. | Gemini free tier (paid-only for EEA users), LLM SDKs, streaming |
| Pre-made accounts | What the hiring team asked for | GitHub OAuth |
| Bulk-inserted seed | 25,000 tickets in about 30 s; a test checks the data obeys the rules | Running each ticket through the workflow (many minutes) |
| PBKDF2 passwords | Argon2 needs 100 MB per login attempt, too much for 512 MB | Argon2 |
| Hand-written CSP header | Eight lines on Django 5.2, which has no built-in CSP | django-csp (a dependency for one header) |
| Login limit per IP, in memory | No dependency; checked before the password is hashed | django-axes (lockout tables, more to configure) |

**Known limits:**
- The login and assistant limits are counted per gunicorn process, so with two workers the
  real limits are up to twice the set values. A deploy restarts the process and resets them.
- The CSP still allows `'unsafe-eval'`, because Unfold's Alpine.js needs it.

## Deliberately skipped
| Skipped | Why |
|---|---|
| GitHub OAuth | The hiring team asked for pre-made reviewer accounts, so nobody signs up. |
| A customer portal or public API | The brief asks for an API only beyond the admin. Customers' messages are logged by agents ("From the customer" on a comment). |
| Email ingestion | Real mailbox plumbing for a demo; agents log what customers send instead. |
| Streaming AI answers | Under WSGI a stream ties up a gunicorn worker for its whole length. Answers are short. |
| A shared cache (Redis) | One machine; the per-process limits are documented above. |
| Per-PR preview apps | Each one is a paid Fly machine. |
| A one-click "Reset demo data" workflow | One documented command does it ([runbook](docs/runbook.md)). |

## With more time
- A shared cache for the login and assistant limits, so they hold across workers and deploys.
- Assigning from the ticket page itself, through a dialog that applies the same rules as the
  bulk action. Today a Lead assigns from the list.
- A customer reply on a ticket waiting on the customer reopens it automatically.
- Resolution-time SLAs and breach alerts, not just first response.
- Browser tests (Playwright) of each role's screens, on top of the HTML assertions.
- Drop `'unsafe-eval'` from the CSP once Unfold ships a CSP-safe Alpine build.
- A small set of graded questions for the AI assistant, to catch answers that drift from
  the form.
