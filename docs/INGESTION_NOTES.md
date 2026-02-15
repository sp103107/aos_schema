# AoS Schema Repo Ingestion Notes (Initial Pass)

## Priority file reviewed first
- `aos_v4_meta_envelope_scene_bundle/aos_v4_meta_envelope_scene_bundle/schemas/master/aos.master.meta.v5_1.schema.json`

## What this schema establishes
- JSON Schema draft `2020-12` contract for the AoS master meta object.
- Canonical v5.1 identifier: `https://aos.dev/schemas/master/aos.master.meta.v5_1.schema.json`.
- Required top-level capability and control domains:
  - `declared_capabilities`
  - `session`
  - `governance`
  - `execution`
  - `tasks`
  - `agents`
  - `outputs`
  - `memory`
  - `audit`

## Key v5.1 signals captured during ingestion
- Determinism/compliance hardening is explicit in the schema description.
- `allOf` condition adds coupling between top-level `runtime` presence and `declared_capabilities.runtime` minimum declaration.
- Shared enums under `$defs` provide stable role/capability vocabularies (task types, agent roles, runtime/audit features).
- `additionalProperties: false` is used broadly, indicating strict schema surface control.

## Foundational follow-on ingestion completed

### Envelope contract
- File reviewed: `aos_v4_meta_envelope_scene_bundle/aos_v4_meta_envelope_scene_bundle/schemas/envelope/aos.master.envelope.v5_1.schema.json`
- Enforces strict top-level envelope structure with `additionalProperties: false` and required core ingress fields:
  - `envelope_version`
  - `envelope_kind`
  - `invocation_type`
  - `platform_capabilities`
  - `execution_hint`
  - `embedded_master_meta`
- Encodes platform/tooling capability surface under nested strict objects (`platform_capabilities`, `tooling`, `connectors`).
- Contains conditional semantics:
  - if `envelope_kind == task_request`, `task` is required
  - if `envelope_kind == task_result`, `result` is required
- Supports migration while preferring v5.1 through `embedded_master_meta.oneOf` (v5.1, v5, v4).

### Temporal contract (scene)
- File reviewed: `aos_v4_meta_envelope_scene_bundle/aos_v4_meta_envelope_scene_bundle/schemas/temporal/aos.scene.v5_1.schema.json`
- Defines an audit-grade strict scene envelope with required lifecycle and execution anchors:
  - `scene_id`, `scene_version`, `episode_id`, `phase`, `started_at`, `scene_status`, `task_nodes`, `memory_checkpoint`
- Binds deterministic replay and integrity via hash/canonicalization definitions (`hash_binding`, `canonicalization`, `sha256`).
- Enforces strict task-node shape (`$defs.node`) with conditional execution evidence:
  - if node `status == executed`, require `start_event_id` and `end_event_id`
- Enforces strict memory hashchain checkpoint metadata and optional signatures.
- Includes terminal-status guardrail: if `completed_at` exists, `scene_status` must be one of `completed|failed|halted`.

## Operational implication for Foreman environment
- With meta + envelope + temporal schemas ingested, Foreman runtime should treat v5.1 payloads as strict contracts, not permissive dictionaries.
- Any parser path that silently accepts unknown keys now risks drift from the canonical AoS contracts.

## Notes
- This file is an operator-facing snapshot to anchor ongoing normalization/standardization work.
