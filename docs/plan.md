# Build plan

Decided on 2026-10-15. Feature-level detail lives in [features/](features/).

## Domain: Support Ticket Tracker

| Model | Key fields |
|---|---|
| `Customer` | name, unique email, company, country |
| `Agent` | OneToOne → User, team, `max_open_tickets` (default 15) |
| `Ticket` | FK customer, FK assignee (Agent, nullable), subject, description, status, priority, channel, timestamps (created / first response / resolved / closed), M2M `tags` |
| `Comment` | FK ticket, FK author (Agent; null = the customer wrote it), body, `is_internal`, `attachment` (file) |
| `Tag` | lookup; case-insensitive unique name |

**Constraints:**
- `resolved_at` is set only when the status is resolved or closed
- `closed_at ≥ resolved_at`
- `first_response_at ≥ created_at`
- internal comments need an agent author
- `max_open_tickets > 0`

Indexes on `(status, priority)` and `(assignee, status)`.

**Business rules (on the models):**
- `Ticket.transition_to(status, by)`:
  - new→open needs an assignee
  - open↔pending_customer
  - → resolved needs at least one public agent reply
  - resolved→closed is Lead only
  - reopening from resolved is allowed; reopening a closed ticket is Lead only, within 14 days
- `Ticket.claim(agent)`: row locks on the ticket and the agent, and a cap on each agent's
  open tickets, so two concurrent claims give exactly one winner.
- SLA deadlines by priority (urgent 1 h / high 4 h / normal 24 h / low 72 h), annotated so
  they stay sortable.
- Status is read-only on forms and changes only through the rules above.

## Stack

| Layer | Choice | Doc |
|---|---|---|
| App | Django 5.2 LTS, Python 3.13, uv | — |
| Admin | Django admin + Unfold 0.110.0 | [admin-ui.md](features/admin-ui.md) |
| DB | Postgres 17: Docker locally, Neon Frankfurt in production | [database.md](features/database.md) |
| Files | Private S3 bucket: SeaweedFS locally, Cloudflare R2 (EU) in production | [file-storage.md](features/file-storage.md) |
| Hosting | Fly.io `fra`, always on, 512 MB | [hosting-fly.md](features/hosting-fly.md) |
| AI | Groq `openai/gpt-oss-20b`, falls back to showing help_text | [ai-form-assistant.md](features/ai-form-assistant.md) |
| Auth | Django auth (Argon2); pre-made reviewer accounts (OAuth dropped 2026-10-18) | [authentication-and-roles.md](features/authentication-and-roles.md) |
| Ops | GitHub Actions CI/CD, Sentry, health checks | [ci-cd.md](features/ci-cd.md), [error-monitoring.md](features/error-monitoring.md), [health-checks.md](features/health-checks.md) |

## Phases

| Phase | Output | Status |
|---|---|---|
| 0. Skeleton | Docker stack, settings, health checks, storage, CI, Fly config, docs | **Done 2026-10-15**, live at https://aleksei-ticket-tracker.fly.dev/ |
| 1. Core | Models, constraints, rules, admin (lists, filters, search, inlines, actions), roles, uploads, seed. **Tag v0.1, deployed** | **Done 2026-10-18** (v0.1) |
| 2. Tests + CI/CD | Rule matrix, concurrency, role leak sweep, seed invariants; deploy on green | **Done 2026-10-18** (v0.2: 76 tests, 95% coverage, CI gate at 93%) |
| 3. AI assistant | Grounded chat with a fallback | **Done 2026-10-18** (live once `GROQ_API_KEY` is set on Fly; help-text fallback until then) |
| 4. OAuth | GitHub login, approval-gated | **Dropped 2026-10-18:** Benrey wants pre-made accounts for two reviewers |
| 5. Hardening | CSP, Sentry, runbook, final README. **v1.0** | — |
| 6. Polish (optional) | Role-aware dashboard | — |

## Day-1 spikes (pass/fail)

| # | Spike | Pass |
|---|---|---|
| S1 | Latency from the EU | Warm changelist p50 ≤ 400 ms; first request after Neon idle ≤ 2 s |
| S2 | `release_command` migrate | A broken migration aborts the deploy; the old release keeps serving |
| S3 | django-storages + R2 (EU) | Private upload; presigned 200 then 403 after expiry; nothing on disk |
| S4 | Unfold + chat widget + CSP | Widget on every change form, no CSP violations |
| S5 | Groq | ≥ 1K requests/day; p95 < 3 s; fallback within 9 s |
| S6 | ~~allauth behind Fly~~ (dropped with OAuth) | The Phase 5 login rate limit keys on `Fly-Client-IP` |
| S7 | Seed into Neon | < 3 min; changelist ≤ 15 queries per page |
| S8 | Agent isolation sweep | No other agents' tickets or hidden fields anywhere |
| S9 | 512 MB memory | RSS < 400 MB under 20 users |
| S10 | Upload limits | 9.9 MB works; 10.1 MB gives a form error |
