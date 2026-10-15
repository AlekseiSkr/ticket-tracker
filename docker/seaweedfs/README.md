# docker/seaweedfs/: local S3 emulator config

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | `docker/seaweedfs/s3.json`, mounted at `/etc/seaweedfs/s3.json` in the `storage` service (chrislusf/seaweedfs:4.48) |
| **Cost**     | $0 |
| **Depends on** | [../../docs/features/file-storage.md](../../docs/features/file-storage.md) |

## What
SeaweedFS S3 identity config. It defines one identity, `local`/`local`, with full rights on
every bucket.

## Why
With no identities configured, SeaweedFS lets anyone read objects without a signature. With
one identity, unsigned requests get **403**, the same as Cloudflare R2's private bucket, so
code that forgets to presign fails locally first. Verified on 2026-10-15: signed fetch 200,
unsigned 403.

**Rejected:**
- MinIO: community edition archived in 2026.
- Anonymous mode: hides presigning bugs.

## How it's set up
`docker-compose.yml` passes `-s3.config=/etc/seaweedfs/s3.json`. The app uses the matching
`S3_ACCESS_KEY_ID=local` and `S3_SECRET_ACCESS_KEY=local` from `.env`.

## Who owns what
The `local`/`local` keys are public placeholders for a localhost-only container, not
secrets. Real R2 keys never go here.

## Gotchas
- **Changing this file needs `docker compose up -d storage`** (a restart) to take effect.

## Open items
None.
