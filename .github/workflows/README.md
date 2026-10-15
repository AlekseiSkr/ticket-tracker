# .github/workflows/: CI and deploy pipelines

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (CI and auto-deploy to Fly, enabled 2026-10-15) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | GitHub Actions in https://github.com/AlekseiSkr/ticket-tracker |
| **Cost**     | $0 |
| **Depends on** | [../../docs/features/ci-cd.md](../../docs/features/ci-cd.md), [../../docs/features/hosting-fly.md](../../docs/features/hosting-fly.md) |

## What
Two workflows:
- **CI** checks every push and PR.
- **Deploy** ships `main` to Fly.io after CI succeeds.

## Why
Only code that passed lint, types, tests, the deploy checks and the secret scan reaches
production.

**Rejected:** Fly's own auto-deploy on push, which deploys even when tests fail.

## How it's set up
| File | Trigger | Jobs |
|---|---|---|
| `ci.yml` | push to `main`, every PR | **quality** (uv sync, ruff, mypy, `makemigrations --check`, pytest with coverage against a Postgres 17 service, `check --deploy` with `DJANGO_DEBUG=false`), **secrets** (gitleaks over full history), **docker** (build the `prod` image). |
| `deploy.yml` | CI completed on `main`, or manual | `flyctl deploy --remote-only` in the `production` environment. Runs only when repo variable `FLY_DEPLOY_ENABLED=true`. |

Placeholder env values for settings are at the top of `ci.yml`. They're not secrets.

## Who owns what
- **`FLY_API_TOKEN`** (deploy-scoped): repo Actions secrets, once created.
- **`FLY_DEPLOY_ENABLED`:** repo Actions variable.

## Gotchas
- **`workflow_run` uses the workflow file from `main`**, not the PR's version.
- **Adding a required setting?** Add a placeholder to `ci.yml`'s `env:`, or CI fails at
  settings import.
- **Actions are pinned to major tags** (`checkout@v7`, `setup-uv@v7`, `gitleaks@v3` as of
  2026-10-15). Dependabot bumps them.

## Open items
- [x] Enable deploy (done 2026-10-15). Token rotation is tracked in
  [../../docs/features/ci-cd.md](../../docs/features/ci-cd.md).
