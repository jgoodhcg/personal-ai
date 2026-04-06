# Decision: Self-Hosted Media And Documents Stack Selection

**Status:** accepted  
**Date:** 2026-04-02

## Context

This decision is derived from two archived planning threads:

- `retrospect/data/chats/695de83e-d788-832b-b5c3-90aef8e1a714_openai_2026-01-07_nextcloud-on-old-laptop.md`
- `retrospect/data/chats/695f3e39-e55c-8328-ba54-ad81f5519d0f_openai_2026-01-08_media-archive-critique.md`

Those threads converged on a consistent shape:

- Keep the server local-network-only.
- Keep the filesystem as the source of truth.
- Do not ask a web photo app to be a serious curation tool.
- Keep Nextcloud small and boring.
- Defer phone auto-upload and other convenience layers until they are clearly worth the operational cost.

## Decision

Use this stack now:

- **PhotoPrism** for photo/video browsing, search, faces, albums, and archive discovery
- **digiKam** on the workstation for rapid keyboard-driven photo curation
- **Nextcloud** for documents and light file sync only
- **Samba** for direct workstation access to the photo archive
- **restic -> DigitalOcean Spaces** for encrypted off-site backup

Defer these until they become real pain points:

- **Immich**
  - Add only if manual phone ingest becomes too annoying and true auto-upload becomes a hard requirement.
- **Jellyfin / Audiobookshelf / Kavita**
  - Add only when non-photo media serving becomes an actual execution priority.
- **Tailscale / public access / remote sharing**
  - Keep the first version local-only.

## Why This Is The Best Plan

- It solves the actual hard problem: rapid intentional curation.
- It keeps the server simple while moving the high-friction tagging workflow to the workstation.
- It avoids treating Nextcloud as a photo product, which was a repeated source of dissatisfaction.
- It preserves portability with plain folders and sidecar metadata.
- It leaves a clean upgrade path for Immich later without forcing it into phase 1.

## Project Plan

### Phase 1: Foundation

- Use the old laptop as a headless Ubuntu Server host on wired Ethernet.
- Mount the external SSD at `/mnt/data` with ext4.
- Assign a static LAN IP.
- Disable lid-close sleep and keep the machine recoverable with plain SSH access.
- Keep all services local-network-only.

### Phase 2: Backup Before Data Load

- Install and configure `restic`.
- Back up `/mnt/data` to DigitalOcean Spaces with encryption and retention.
- Exclude `projects/` and `exports/` from primary backups if they remain disposable.
- Add a daily systemd timer.
- Perform a restore test before loading the full archive.

### Phase 3: Storage Layout And Access

Create this baseline structure:

```text
/mnt/data/
├── photos/
│   └── originals/
├── documents/
├── projects/
└── exports/
```

Rules:

- `photos/originals` is append-only in practice.
- `projects` is for active creative work.
- `exports` is disposable output.
- `documents` is the only directory Nextcloud should own.

Set up Samba for the photo tree so the workstation can mount it directly.

### Phase 4: Photo Workflow

- Run **PhotoPrism** against `/mnt/data/photos/originals` in read-only mode.
- Use **manual ingest** at first:
  - phone via cable
  - camera via SD card
- Ingest into source-based folders rather than premature taxonomy.
- Use **digiKam** on the workstation for high-speed tagging, rating, and curation.
- Configure digiKam to write XMP sidecars; keep its database on the workstation SSD, not on the server share.
- Reindex PhotoPrism after tagging sessions.

Success condition:

- You can ingest a sample set, tag quickly in digiKam, and see those results reflected in PhotoPrism without metadata confusion.

### Phase 5: Documents

- Run **Nextcloud** only for `/mnt/data/documents`.
- Do not use Nextcloud for the photo archive.
- Keep Nextcloud scoped to document sync, light sharing, and collaboration.
- If Nextcloud becomes the highest-maintenance part of the system, reevaluate it before expanding its role.

### Phase 6: Validation And Operating Cadence

Before calling the system stable:

- Test a restic restore of one document and one photo directory.
- Test a full ingest -> tag -> reindex -> browse loop.
- Test workstation SMB performance on a realistic sample set.
- Test one Nextcloud sync flow end to end.

Ongoing cadence:

- Weekly: verify backups ran
- Monthly: check disk usage and service health
- Quarterly: perform a restore test
- Annually: verify selective checksums for irreplaceable originals

## Selective Integrity Plan

Do not build a heavy checksum regime.

Do this instead:

- Generate `SHA256SUMS` once at ingest for:
  - `photos/originals`
  - irreplaceable videos
- Store the checksum files alongside those directories.
- Verify them annually or after any suspected disk issue.

This adds integrity confidence without adding a new always-on subsystem.

## Known Risks And Mitigations

### SMB curation will not feel as fast as local disk

Mitigation:

- Test early with a realistic batch.
- If it becomes annoying, stage working sets locally on the workstation and sync sidecars back.

### PhotoPrism reindexing adds manual friction

Mitigation:

- Accept it in phase 1.
- Automate only after the manual cadence becomes clearly annoying.

### Nextcloud may be the least satisfying part of the system

Mitigation:

- Keep it scoped to documents only.
- Do not let it expand back into being the universal platform.

### Old laptop performance will sag under overlapping work

Mitigation:

- Avoid running heavy ingest, PhotoPrism indexing, and backups at the same time.
- Prefer calm scheduling over constant background activity.

## Explicit Non-Goals For Phase 1

- No public exposure
- No reverse proxy
- No Tailscale requirement
- No Immich
- No always-on phone sync
- No full media streaming stack
- No premature folder taxonomy refactor
- No dedupe crusade

## Consequences

- The first version is intentionally a little manual.
- The system is biased toward durability and clarity over polish.
- If future needs change, the first addition should be **Immich**, not a broader redesign.

See authoritative matrix: `.decisions/self-hosted-media-documents-stack-selection.json`.
