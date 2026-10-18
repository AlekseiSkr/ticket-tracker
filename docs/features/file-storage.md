# File storage (SeaweedFS locally, Cloudflare R2 in production)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live (local: SeaweedFS; production: R2 since 2026-10-15) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | Local: `storage` service (chrislusf/seaweedfs:4.48). Prod: Cloudflare R2 bucket `ticket-tracker-media`, EU jurisdiction |
| **Cost**     | $0 (R2 free tier: 10 GB-month, 1M Class A / 10M Class B ops, free egress) |
| **Depends on** | [configuration-and-secrets.md](configuration-and-secrets.md) |

## What
All uploaded files (comment attachments) go to one **private** S3-compatible bucket through
`config.storage.PrivateMediaStorage`, a thin subclass of django-storages' `S3Storage`.
Every file URL is presigned and expires in 60 s. Nothing is written to the container's disk:
uploads stay in memory (max 10 MB) on their way to the bucket.

## Why
- **Object storage, not disk:** Fly machines have ephemeral disks, and the brief requires it.
- **R2:** free egress, 10 GB free, and S3-compatible, so django-storages works unchanged.
- **Private and presigned:** attachments can contain customer data. `r2.dev` public URLs
  are development-only and rate-limited.
- **SeaweedFS locally:** maintained (4.48, Sep 2026), single container, real S3 API with
  auth.

**Rejected:**
- **MinIO:** community edition archived in 2026.
- **Public bucket:** leaks attachments.
- **Tigris:** kept as the fallback if R2 activation needs a card that isn't available.
- **Neon Object Storage:** its beta/GA status is unclear, and it would couple DB and storage
  failures.

## How it's set up
**Local (automatic):**
- `docker compose up` starts SeaweedFS with one identity (`local`/`local`) from
  `docker/seaweedfs/s3.json`.
- The web container runs `ensure_bucket --create`.

**Production:**
1. https://dash.cloudflare.com/sign-up: create an account.
2. Dashboard → **R2 Object Storage** → enable R2. Cloudflare may ask for a payment method
   even on the free tier.
3. **Create bucket** `ticket-tracker-media`, with **Jurisdiction: EU**. Leave public access
   **off**.
4. R2 → **Manage API tokens** → **Create API token**: permission *Object Read & Write*,
   scoped to this bucket only. Copy the Access Key ID, Secret Access Key, and the
   jurisdiction-specific S3 endpoint (`https://<account_id>.eu.r2.cloudflarestorage.com`).
5. Set the Fly secrets:
   `fly secrets set S3_ENDPOINT_URL=… S3_BUCKET=ticket-tracker-media S3_ACCESS_KEY_ID=… S3_SECRET_ACCESS_KEY=…`
   `S3_REGION=auto` and `S3_ADDRESSING_STYLE=virtual` are already in `fly.toml [env]`.
6. Smoke test: `fly ssh console -C "python manage.py ensure_bucket"` (without `--create`).

**Verified live on 2026-10-15** (bucket and token created by Aleksei in the Cloudflare
dashboard):
- `ensure_bucket`: reachable.
- Upload from the Fly machine: succeeded.
- Presigned GET: 200. The same URL after 60 s: **403** (expired). Unsigned GET: 400.
- Delete: succeeded.

**Attachments (Phase 1):**
- Keys are random (`attachments/<uuid>.<ext>`).
- Types are checked by magic bytes (PNG, JPG, PDF, UTF-8 TXT), with a 10 MB cap
  (`tickets/validators.py`).
- Downloads go through `/attachments/<comment_id>/`. It checks the user may see the ticket
  (404 otherwise), then redirects to a 60 s presigned URL that forces
  `Content-Disposition: attachment` and the right content type.

## Who owns what
- **Cloudflare account and billing:** Aleksei.
- **R2 API token:** Fly secrets + password manager. Scope it to the one bucket.

## Gotchas
- **Presigned URLs can't use R2 custom domains** (Cloudflare docs, verified 2026-10-15). They
  always point at the `r2.cloudflarestorage.com` endpoint. Maximum expiry is 7 days, and
  POST uploads aren't supported.
- **Two endpoints locally.** A presigned URL signs its host, so you can't rewrite
  `storage:8333` to `localhost:8333` afterwards. `S3_PUBLIC_ENDPOINT_URL` makes the storage
  sign with a second client pointed at the browser-facing host. Leave it unset in production.
- **EU jurisdiction buckets need the `.eu.` endpoint**
  (`https://<account_id>.eu.r2.cloudflarestorage.com`).
  - The plain endpoint returns **403 Forbidden** on every call (`HeadBucket`, `HeadObject`),
    which looks like a bad token but isn't.
  - This cost the first deploy on 2026-10-15. It was fixed by changing only
    `S3_ENDPOINT_URL`.
- **django-storages 1.14.6 lists Django only up to 5.1** in its classifiers (last release
  2025-04-02). It's verified working on 5.2.18 by `tests/test_storage.py` and a manual
  round-trip on 2026-10-15.
- **Local anonymous reads return 403** (verified), matching R2's private bucket.

## Open items
- [x] Create the R2 bucket and token (done 2026-10-15).
- [ ] Phase 1: a permission-checked `/attachments/<comment_id>/` view that redirects to a
  60 s presigned URL with `Content-Disposition: attachment`.
