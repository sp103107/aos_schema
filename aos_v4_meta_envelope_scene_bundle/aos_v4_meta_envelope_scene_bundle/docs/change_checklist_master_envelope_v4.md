# Change Checklist — Master Envelope v4 (Production)

## A) Structural changes checklist (schema author)
- [ ] New `$id` is v4: `https://aos.dev/schemas/envelope/aos.master.envelope.v4.schema.json`
- [ ] `additionalProperties: false` preserved at every object layer
- [ ] Required identity fields added:
  - [ ] `envelope_version`
  - [ ] `envelope_kind`
- [ ] Conditional payload rules:
  - [ ] `task_request` ⇒ requires `task`
  - [ ] `task_result` ⇒ requires `result`
- [ ] Optional `temporal` block is strict and URN-patterned
- [ ] `embedded_master_meta` accepts v4 (preferred) and v3 (migration) via `oneOf`

## B) Compatibility checklist
- [ ] v3 schema remains available and unchanged
- [ ] Existing v3 envelope instances can be migrated by:
  - [ ] adding `envelope_version: aos.master.envelope.v4`
  - [ ] adding `envelope_kind`
  - [ ] optionally adding `request_id/created_at/temporal`
  - [ ] keeping `invocation_type/platform_capabilities/execution_hint/embedded_master_meta` semantics

## C) Validator/Judge checklist
- [ ] Valid Draft 2020-12 JSON Schema
- [ ] No accidental loosening of constraints
- [ ] `oneOf` meta compatibility tested against at least one v3-meta and one v4-meta instance
