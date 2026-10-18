# Ticket Tracker

A support ticket tracker built on the Django admin: customers, agents, tickets with a status
workflow and SLA, comments with attachments, role-based access, and an AI assistant that
explains the admin forms.

> Status: Phase 1 (core, v0.1) is done: tickets, workflow rules, roles, attachments and demo
> data. The full README (architecture decisions, why this stack, what was skipped) is written
> in Phase 5. The plan is in [docs/plan.md](docs/plan.md).

## Run it locally

Requires Docker Desktop.

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
# Demo data: needs the four DEMO_*_PASSWORD values in .env (see .env.example)
docker compose exec web python manage.py seed_users
docker compose exec web python manage.py seed_demo --reset
```

Open http://localhost:8000/admin/. Health: http://localhost:8000/healthz and `/readyz`.

| Task | Command |
|---|---|
| Tests | `docker compose exec web pytest` |
| Lint and format | `docker compose exec web ruff check . && docker compose exec web ruff format .` |
| Type check | `docker compose exec web mypy .` |
| Stop / wipe data | `docker compose down` / `docker compose down -v` |

## Docs

Every feature has a short doc in [docs/features/](docs/features/). See [docs/README.md](docs/README.md)
for the index and the rules (no secrets in git, absolute dates, record the rejected option).
