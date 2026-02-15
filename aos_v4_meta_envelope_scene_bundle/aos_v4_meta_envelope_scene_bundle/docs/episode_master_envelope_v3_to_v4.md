# Episode: Master Envelope v3 → v4 Upgrade

- **episode_id:** `urn:aos:episode:master_envelope_upgrade_v4`
- **created_at:** 2026-02-13T02:28:58Z
- **goal:** Upgrade `aos.master.envelope.v3` to `aos.master.envelope.v4` with explicit envelope identity, optional temporal binding, and richer platform/tooling declarations.

```mermaid
flowchart TD
  A[Episode: master_envelope_upgrade_v4] --> B[Scene: Author envelope v4 schema]
  B --> C[Scene: Validate schema (Draft 2020-12)]
  C --> D[Gate: Judge approve/deny]
  D --> E[Checkpoint: ledger tip hash + artifacts]
```
