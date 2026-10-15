# CI/CD (GitHub Actions → Fly.io)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (CI green since 2026-10-15; auto-deploy to Fly enabled 2026-10-15) |
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
1. Public repo https://github.com/AlekseiSkr/ticket-tracker, created on 2026-10-15 with
   `gh repo create AlekseiSkr/ticket-tracker --public --source . --push`.
2. Secret scanning, push protection and Dependabot alerts were enabled on 2026-10-15 via the
   GitHub API (equivalent to repo **Settings → Code security**).
3. Auto-deploy, enabled on 2026-10-15:
   - Created a **deploy-scoped** token, valid for 1 year, named `github-actions-deploy`, and
     piped it straight into the repo secret without displaying it:
     `fly tokens create deploy -a aleksei-ticket-tracker -x 8760h -n github-actions-deploy | gh secret set FLY_API_TOKEN`
   - Set the Actions variable: `gh variable set FLY_DEPLOY_ENABLED --body true`.
   - The `production` environment is created automatically the first time the deploy job
     runs.
   - **Verified:** a manual dispatch of Deploy (run 38788295485) succeeded, and the release
     migration and machine update went through.

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
- **CI runs with `DJANGO_DEBUG` unset**, which means production security settings, so plain
  HTTP requests in tests get a 301 to HTTPS. Use `client.get(..., secure=True)`. This was
  the first CI failure, on 2026-10-15.
- **Dependabot is told to ignore** Django and django-stubs minor/major bumps, and Python
  base-image minor/major bumps. The project stays on Django 5.2 LTS and Python 3.13 on
  purpose. On 2026-10-15 Dependabot opened PR #3, widening the pin to Django 6.1; it was
  closed by the ignore rule. Upgrade those deliberately, in their own PR.
- **On 2026-10-15 PR #2 moved Actions** to `checkout@v7`, `setup-uv@v7` and `gitleaks@v3`.

## Open items
- [x] Push the repo and confirm CI is green (done 2026-10-15, commit `ee7172f`).
- [x] Wire up `FLY_API_TOKEN` and `FLY_DEPLOY_ENABLED` (done 2026-10-15).
- [ ] **Rotate `FLY_API_TOKEN` before 2027-10-15**, when it expires.
  List and revoke tokens with `fly tokens list -a aleksei-ticket-tracker`.
