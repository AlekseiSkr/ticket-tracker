# .github/: GitHub automation

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `.github/` in https://github.com/AlekseiSkr/ticket-tracker |
| **Cost**     | $0 (Actions is free on public repos) |
| **Depends on** | [../docs/features/ci-cd.md](../docs/features/ci-cd.md) |

## What
The GitHub-side configuration: CI/CD workflows and Dependabot.

## Why
CI and dependency updates live with the code they check, so they're versioned and reviewable.

**Rejected:** configuring CI in a UI (Fly's GitHub integration, Render's auto-deploy).

## How it's set up
| Path | Role |
|---|---|
| `workflows/` | CI and deploy (see [workflows/README.md](workflows/README.md)). |
| `dependabot.yml` | Weekly grouped updates for uv, Actions and the Docker base image. **Ignores** Django and django-stubs minor/major (we stay on 5.2 LTS) and Python base-image minor/major (we stay on 3.13). |

Repo settings outside git, enabled on 2026-10-15 via the API: secret scanning, push
protection, Dependabot alerts.

## Who owns what
- **Repo admin:** Aleksei.
- **Actions secrets** (`FLY_API_TOKEN`, once created) live in repo Settings → Secrets.

## Gotchas
- **Dependabot only opens patch PRs for Django.** Upgrading the Django minor version is a
  deliberate, separate change.

## Open items
None.
