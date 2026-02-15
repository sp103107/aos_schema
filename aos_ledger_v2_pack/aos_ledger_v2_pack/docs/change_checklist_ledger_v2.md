# Change Checklist — Event Ledger v2 (Production)

## A) Required contract fields
- [ ] `canonicalization.method` present and one of: `json-c14n | stable-json-stringify | custom`
- [ ] `canonicalization.profile` present (pin an exact profile string)
- [ ] `hashing.algo == sha256`
- [ ] `hashing.prev_hash_field == prev_hash`
- [ ] `hashing.event_hash_field == event_hash`
- [ ] `checkpoint.tip_event_id`, `checkpoint.tip_hash`, `checkpoint.event_count` required

## B) Hashchain rules (implementation MUST follow)
- [ ] `payload_hash` is sha256 of canonicalized payload (or canonicalized event payload subset) per your profile
- [ ] `event_hash` is sha256 of canonicalized event object **excluding** `event_hash`
- [ ] `prev_hash` for event[N] equals `event_hash` of event[N-1]
- [ ] Genesis event uses a fixed all-zero `prev_hash` (or explicit genesis rule you standardize)

## C) Replay safety
- [ ] Canonicalization profile is enforced by code (not optional)
- [ ] Tests include: same events → same hashes across runs/machines
