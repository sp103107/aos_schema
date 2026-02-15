# Episode: Master Meta v3 → v4 Upgrade

- **episode_id:** `urn:aos:episode:master_meta_upgrade_v4`
- **created_at:** 2026-02-13T02:24:20Z
- **goal:** Upgrade `aos.master.meta.v3` to `aos.master.meta.v4` with stronger determinism + enforceable governance/execution fields.

## Change Episode Flow

```mermaid
flowchart TD
  A[Episode: master_meta_upgrade_v4] --> B[Scene 1: Diff v3 vs v4 requirements]
  B --> C[Scene 2: Add $defs vocab + type:string for enums]
  C --> D[Scene 3: Expand governance + execution fields]
  D --> E[Scene 4: Normalize memory tiers + write rules]
  E --> F[Scene 5: Validate schema (Draft 2020-12)]
  F --> G[Gate: Judge approve/deny]
  G --> H[Checkpoint: ledger tip hash + artifacts]
```
