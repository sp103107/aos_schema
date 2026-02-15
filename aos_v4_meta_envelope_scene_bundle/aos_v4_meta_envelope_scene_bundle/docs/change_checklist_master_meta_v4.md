# Change Checklist — Master Meta v4 (Production)

## A) Structural changes checklist (schema author)
- [ ] New `$id` is v4: `https://aos.dev/schemas/master/aos.master.meta.v4.schema.json`
- [ ] `additionalProperties: false` preserved at every object layer
- [ ] All capability enums are typed (`type: "string"`) via `$defs`
- [ ] Governance requires: `halt_on_violation`, `deterministic_required`, `refusal_allowed`
- [ ] Execution requires: `step_gated`, `simulation`, `replay_mode`
- [ ] Memory uses tiers: `working_set | ledger | long_term`
- [ ] `$defs` exist for: `agent_role`, `task_type`, `forbidden_action`, `memory_tier`

## B) Compatibility checklist (must_not_break)
- [ ] v3 schema remains available and unchanged (do not overwrite)
- [ ] Migration note: v3 `memory.allowed` → v4 `memory.allowed_tiers`
- [ ] Any new required booleans have explicit values in all v4 instances

## C) Judge validation checklist (gate)
- [ ] Valid Draft 2020-12 JSON Schema
- [ ] No accidental additionalProperties loosened
- [ ] Governance/execution flags are coherent (no contradictions)
- [ ] Memory tier naming is internally consistent

## D) Recorder checklist (ledger + checkpoint)
- [ ] Ledger event types recorded:
  - [ ] NODE_PLANNED
  - [ ] NODE_EXECUTED
  - [ ] VALIDATION_RESULT
  - [ ] CHECKPOINT_CREATED
  - [ ] SAVE_STATE_WRITTEN
- [ ] Checkpoint anchors:
  - [ ] schema hash
  - [ ] artifact refs
  - [ ] tip hash
