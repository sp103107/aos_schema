# Episode: Ledger v1 → v2 Hashchain Upgrade

- **episode_id:** `urn:aos:episode:ledger_hashchain_upgrade_v2`
- **created_at:** 2026-02-13T02:32:47Z
- **goal:** Enforce deterministic ledger hashing by declaring canonicalization profile and requiring `prev_hash`/`event_hash` on every event, plus checkpoint anchoring.

```mermaid
flowchart TD
  A[Episode: ledger_hashchain_upgrade_v2] --> B[Scene: Author ledger v2 schema]
  B --> C[Scene: Validate schema (Draft 2020-12)]
  C --> D[Gate: Judge approve/deny]
  D --> E[Checkpoint: tip_event_id + tip_hash + event_count]
```
