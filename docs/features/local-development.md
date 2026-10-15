# Local development (Docker)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Developer machine, Docker Desktop; `docker-compose.yml` |
| **Cost**     | $0 |
| **Depends on** | [configuration-and-secrets.md](configuration-and-secrets.md), [database.md](database.md), [file-storage.md](file-storage.md) |

## What
One command starts the whole app locally: Postgres 17 (`db`), an S3-compatible store
(`storage`, SeaweedFS) and the Django dev server (`web`) with the source bind-mounted, so
edits reload automatically. Python dependencies are managed by uv, and the lockfile is
`uv.lock`.

## Why
The local stack has the same *shape* as production: real Postgres and real S3 APIs, with no
SQLite and no files on local disk. Bugs that only show up with Postgres or presigned URLs
then appear on day one, not on deploy day.

**Rejected:**
- **SQLite + local media folder:** faster to start, but it hides exactly the class of bugs
  the brief grades (managed DB, object storage, no silent fallbacks).
- **MinIO as the S3 emulator:** its community edition was archived in 2026, and Docker
  images are no longer published.
- **Running Python directly on Windows:** the Linux container matches production.

## How it's set up
1. Install Docker Desktop and start it.
2. `cp .env.example .env` (local placeholders only).
3. `docker compose up -d --build`. On start the web container runs `migrate`, creates the
   bucket (`ensure_bucket --create`), then `runserver`.
4. Create an admin user: `docker compose exec web python manage.py createsuperuser`.
5. Open http://localhost:8000/admin/.

**Everyday commands:**

| Task | Command |
|---|---|
| Tests | `docker compose exec web pytest` |
| Lint and format | `docker compose exec web ruff check . && docker compose exec web ruff format .` |
| Types | `docker compose exec web mypy .` |
| Shell | `docker compose exec web python manage.py shell` |
| Logs | `docker compose logs -f web` |
| Reset everything | `docker compose down -v` (deletes the DB and bucket volumes) |

**Adding or upgrading a dependency:** edit `pyproject.toml`, then regenerate the lock
inside Linux:
`docker run --rm -v "${PWD}:/app" -w /app python:3.13-slim sh -c "pip install -q uv==0.13.1 && uv lock"`,
then `docker compose up -d --build web`.

## Who owns what
No accounts or credentials. Every value in `.env` is a local placeholder; `.env` is
git-ignored anyway.

## Gotchas
- **Ports bind to 127.0.0.1 only:** web 8000, Postgres **5433** (not 5432, to avoid
  clashing with a locally installed Postgres), S3 8333.
- **Two S3 endpoints.** Inside Docker the app reaches storage as `storage:8333`, but your
  browser needs `localhost:8333`. `S3_PUBLIC_ENDPOINT_URL` makes presigned URLs use the
  browser-facing host (see [file-storage.md](file-storage.md)).
- **The venv lives at `/opt/venv` in the image**, not in `/app`, so the bind mount doesn't
  hide it. After changing dependencies you must rebuild the image.
- **Git Bash on Windows rewrites `/app` paths in `docker run -v`.** Prefix the command with
  `MSYS_NO_PATHCONV=1`, or run it from PowerShell.

## Open items
- [ ] Add a `seed_demo` step to the compose start-up once the seed command exists (Phase 1).
