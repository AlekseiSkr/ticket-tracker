# Runbook

What to do when production misbehaves, and the routine operations. Production is the Fly app
`aleksei-ticket-tracker` (https://aleksei-ticket-tracker.fly.dev/). Every command below
assumes `-a aleksei-ticket-tracker`, or a shell in the repo folder where `fly.toml` names
the app. Credentials live in Fly secrets and the password manager, never here.

## The site is down or slow: first checks
1. **`curl https://aleksei-ticket-tracker.fly.dev/healthz`.** No answer means the process or
   machine is down; go to step 2. `{"status": "ok"}` means the app is up.
2. **`fly status`.** If the machine is `stopped`, run `fly machine start <id>`. A trial
   account stops idle machines on its own; adding a card to the Fly account ends that.
3. **`curl …/readyz`.** A 503 means the database is unreachable. Open the Neon console:
   - compute suspended because the month's CU-hours ran out: wait for the reset or upgrade
     the plan ([database.md](features/database.md));
   - endpoint or password changed: update the `DATABASE_URL` secret.
4. **Sentry,** project `ticket-tracker`: the stack trace, the URL and the release of every
   unhandled error. **`fly logs`** shows the live gunicorn output.
5. **Memory:** the machine has 512 MB. An out-of-memory kill shows in `fly logs`. The fix is
   `fly scale memory 1024`.

## Deploy and roll back
- **Deploy:** merge to `main`. CI runs, and a green run deploys. Migrations run in the
  `release_command` first; a failing migration aborts the release and the old one keeps
  serving. Manual deploy: `fly deploy --ha=false`.
- **Roll back:** `fly releases --image` lists the past image refs. Deploy a known-good one
  with `fly deploy --image <ref> --ha=false`. Migrations don't roll back: if the bad release
  changed the schema, write a migration that reverts it and deploy that instead.

## Routine operations
| Task | Command |
|---|---|
| Reset demo data | `fly ssh console -C "python manage.py seed_demo --reset"` (about 30 s; real accounts are kept) |
| Re-create reviewer accounts or reset their passwords | Change the `DEMO_*_PASSWORD` secrets with `fly secrets set`, then `fly ssh console -C "python manage.py seed_users"` |
| Unblock a login after 10 failed attempts | Wait 15 minutes, or `fly machine restart <id>` (the counter is in memory) |
| Create a superuser | `fly ssh console --pty -C "python manage.py createsuperuser"` |
| Turn the AI assistant off | `fly secrets unset GROQ_API_KEY`. The panel then answers with each field's help text. |
| Rotate `DJANGO_SECRET_KEY` | `fly secrets set DJANGO_SECRET_KEY=…`. Everyone is logged out. |
| Rotate the R2 keys | Create a new token in Cloudflare R2, set `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY`, then delete the old token |

## Symptoms and causes
- **A page loads but buttons or dropdowns do nothing:** the Content Security Policy probably
  blocked a script. The browser console names the blocked source. The policy is `CSP` in
  `core/middleware.py`.
- **Attachments give 403 or "expired":** download links are valid for 60 s. Reload the
  ticket page to get a fresh link.
- **"That request was too large" (400) on save:** the upload was over 11 MB.
- **The assistant answers "couldn't answer just now":** Groq timed out or rate-limited the
  app. It recovers on its own; Groq's status page says more.
