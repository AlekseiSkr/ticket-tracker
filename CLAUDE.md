# Working on this repo

- **Write all code with the `/ponytail:ponytail` skill:** the smallest complete change, no
  speculative abstractions or options, every non-trivial piece of logic with a test.
- **Run everything through Docker:** `docker compose exec web <cmd>` (pytest, ruff, mypy,
  manage.py). The host Python is not used.
- **Start in a folder by reading its `README.md`.** Every directory that holds code or
  config has one (template: `docs/_template.md`), except `.github/`: GitHub would show a
  `.github/README.md` as the repository's front page.
  - **New directory:** add its README and list it in the directory index in
    `docs/README.md`.
  - **Changed what's in a directory:** update that README in the same commit, including its
  `Status` and `Updated` fields.
- **Every new feature or external service ships with a doc** in `docs/features/`, also
  copied from `docs/_template.md` and listed in the feature index in `docs/README.md`.
- **No AI attribution in git.** Commits and PRs go out under the owner's identity only:
  no `Co-Authored-By: Claude` trailer, no Claude author, no "Generated with Claude Code"
  line.
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
