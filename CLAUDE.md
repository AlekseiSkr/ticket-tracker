# Working on this repo

- **Run everything through Docker:** `docker compose exec web <cmd>` (pytest, ruff, mypy,
  manage.py). The host Python is not used.
- **Every new feature ships with a doc** in `docs/features/`, copied from
  `docs/_template.md`. When reality changes, update the doc's `Status` and `Updated` fields,
  and add it to the index in `docs/README.md`.
- **Never commit secrets.** Docs say where a credential lives, never its value. Use absolute
  dates (YYYY-MM-DD). Record the rejected option in every decision.
- **Configuration comes from env vars via `config/env.py`.** Never add a silent fallback
  (no SQLite, no local-disk media).
- **Business rules live on the models** (`tickets/models.py`). Admin actions call the model
  methods, never `queryset.update()`.
- **Hiding a field from a role** means removing it everywhere: fields, list display, filters,
  search, autocomplete, error messages and the AI context.
- **Before finishing a change:** `pytest`, `ruff check .`, `ruff format --check .` and
  `mypy .` all pass.
- **The plan and its phases** are in `docs/plan.md`.
