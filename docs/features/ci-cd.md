# CI/CD (GitHub Actions → Fly.io)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | In progress (workflows written; run once the repo is on GitHub) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`, `.github/dependabot.yml` |
| **Cost**     | $0 (GitHub Actions is free on public repos) |
| **Depends on** | [hosting-fly.md](hosting-fly.md), [configuration-and-secrets.md](configuration-and-secrets.md) |

## What
**CI** runs on every push and PR:
- `quality` job: ruff lint and format check, mypy, a check that migrations are committed,
  pytest with coverage against a real Postgres service, and `check --deploy` with
  production settings
- `secrets` job: gitleaks over the full history
- `docker` job: production image build

**Deploy** runs `flyctl deploy --remote-only` after CI passes on `main`.

**Dependabot** opens weekly grouped PRs for uv packages, Actions and the Docker base image.

## Why
Every check maps to something a reviewer will look at: committed migrations, no secrets,
working deploy settings, tested business logic. Deploying only after green CI means `main`
is what's live.

**Rejected:**
- **Fly's GitHub integration / auto-deploy on push:** it would deploy even when tests fail.
- **pre-commit hooks only:** they don't run for reviewers or Dependabot.

## How it's set up
1. Create a public repo at https://github.com/new (e.g. `ticket-tracker`) and push.
2. Repo **Settings → Code security**: enable *Secret scanning* and *Push protection*.
3. Once the Fly app exists (see [hosting-fly.md](hosting-fly.md)):
   - `fly tokens create deploy -x 999999h`, then add it as the Actions secret `FLY_API_TOKEN`
     (Settings → Secrets and variables → Actions).
   - Add the Actions **variable** `FLY_DEPLOY_ENABLED=true`.
   - Create a `production` environment (Settings → Environments).

## Who owns what
- **GitHub repo:** Aleksei.
- **`FLY_API_TOKEN`:** GitHub Actions secrets only. It's a deploy-scoped token, not a
  personal one.

## Gotchas
- **The deploy workflow is a no-op until `FLY_DEPLOY_ENABLED` is `true`**, which is
  deliberate so the first pushes don't fail.
- **`workflow_run` deploys use the workflow file from `main`**, not from the PR.
- **gitleaks-action is free for personal repos.** Organisation repos need a license key.
- **Action versions are pinned to major tags.** Dependabot keeps them current.

## Open items
- [ ] Push the repo and confirm CI is green (2026-10-15).
- [ ] Wire up `FLY_API_TOKEN` and `FLY_DEPLOY_ENABLED` after the Fly app exists.
