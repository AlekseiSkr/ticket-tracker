# tests/: automated tests

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (88 tests passing, 95% coverage, on 2026-10-18), plus one on-demand stress test |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | `tests/`; run with `docker compose exec web pytest`; CI job `quality` |
| **Cost**     | $0 |
| **Depends on** | [../config/README.md](../config/README.md), [../docs/features/ci-cd.md](../docs/features/ci-cd.md) |

## What
The pytest-django suite, run against real Postgres (Docker locally, a service container in
CI). It covers config fail-fast behaviour, health endpoints, presigned storage URLs and the
bucket command. Phase 1+ adds the business rules, concurrency, role isolation and seed
invariants.

## Why
- **Real Postgres, not SQLite:** constraints and `select_for_update` only behave correctly on
  Postgres.
- **Storage tests sign URLs locally**, with no network call.

**Rejected:**
- Django's `TestCase` runner: pytest fixtures are simpler.
- Mocking the database.

## How it's set up
| File | Covers |
|---|---|
| `conftest.py` | Autouse fixture: plain static storage, because tests run with `DEBUG=False` and no `collectstatic`. Shared fixtures: `lead`, `agent`, `other_agent`, `customer`, and the `make_user` helper. |
| `test_assistant.py` | The AI form assistant: prompt contents (metadata and rules in, ticket data out); read-only marking for Agents; Lead-only forms and other agents' tickets refused; fallback on timeout, 429 and missing config; question scrubbing and cap; rate limit; staff-only with CSRF; widget present; the field list includes read-only, dropdown and inline fields. |
| `test_env.py` | `require_env` and the other helpers fail loudly on missing or invalid values. |
| `test_health.py` | `/healthz` makes zero queries; `/readyz` up and 503; the admin login page renders. |
| `test_admin_theme.py` | Dark theme, lime primary, self-hosted fonts, favicon and login art; no dead "Return to site"; skip link before the sidebar; dashboard greeting; Unfold auth admins; branded 404; "Local" badge only under `DEBUG`. |
| `test_tickets.py` | The full transition matrix (all 25 status pairs); workflow rules and first-response stamping; WIP cap and a two-thread concurrent claim (exactly one wins); the Agent leak sweep (list, change, history, delete and every workflow-button URL of another agent's ticket, customer inline, attachment, the assignee autocomplete, WIP caps never shown); Lead bulk assign, priority and close; role-hidden actions, pages and fields; internal note via the admin form; bulk-action skip messages; upload validation and the 11 MB request cap; seed invariants; changelist ≤ 15 queries, and the ids-first paginator keeps sorted rows in order. |
| `test_stress.py` | **On demand only** (marker `stress`, excluded by default). Seeds `STRESS_TICKETS` tickets (default 25,000) into the throwaway test DB. Then it prints p50/p95/max, query count and page size for 16 Lead and Agent pages, bulk-claim time, an 8-agent race on one ticket (exactly one winner), assistant overhead with the LLM mocked, table sizes and peak memory. Fails if any page goes over `STRESS_P95_MS` (default 1500) or 20 queries. |
| `test_storage.py` | URLs are presigned (60 s); the public endpoint is used when set. |
| `test_ensure_bucket.py` | Creates the bucket only on a 404 with `--create`; never on 403. |

Run the stress test:

```bash
docker compose exec -e STRESS_TICKETS=25000 web pytest -m stress -s
```

Config is in `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.coverage.run]`, and `[tool.coverage.report]` with the 93% gate).

## Who owns what
No credentials. The test settings use placeholders from `.env` or CI `env:`.

## Gotchas
- **CI has `DJANGO_DEBUG` unset**, so production security settings apply and HTTP requests
  get a 301. Use `client.get(..., secure=True)`.
- **Concurrency tests need `transaction=True`** (`@pytest.mark.django_db(transaction=True)`).
  The default wraps everything in one transaction and hides lock behaviour.

## Open items
- [x] Phase 2: transition matrix, concurrent claim, Agent leak sweep, upload validators, seed
  invariants, AI fallback.
