# Foreman v2 Stack Alignment Gaps vs AoS v5.1 Strict Schemas

## Scope
This review checks how current `foreman_v2_stack` runtime logic parses task/execution domains relative to:
- Master meta v5.1 (`aos.master.meta.v5_1.schema.json`)
- Envelope v5.1 (`aos.master.envelope.v5_1.schema.json`)
- Scene v5.1 (`aos.scene.v5_1.schema.json`)

## Files inspected
- `src/api/server.py`
- `src/handler/minimal_handler.py`
- `src/router/mcp_router.py`

## Current Foreman behavior (as implemented)

### 1) API ingress is schema-agnostic
- `/chat` accepts `payload: Dict[str, Any]` and only maps generic keys (`source`, `target`, `data`) into an MCP packet.
- No validation exists for AoS envelope fields such as `envelope_kind`, `execution_hint`, or `embedded_master_meta`.

### 2) MCP handler is permissive and echo-oriented
- `process_mcp_packet()` only verifies packet is a dict and then echoes payload keys.
- It does not parse or validate:
  - `execution` domain content from master meta
  - `tasks` domain content from master meta
  - envelope or scene lifecycle fields

### 3) Router layer has no domain enforcement
- `Router.route()` returns a generic success response with packet presence.
- No schema version checks, no domain extraction, no strict-key filtering.

## Gaps against v5.1 strictness (`additionalProperties: false`)

### Gap A — Unknown-key acceptance across all runtime entry points
- v5.1 meta/envelope/scene contracts are strict at top level and many nested objects.
- Foreman currently accepts arbitrary dictionaries and forwards them without rejecting unknown properties.
- Risk: invalid payloads pass silently, then fail later (or never) creating audit drift.

### Gap B — No required-field enforcement for task/execution domains
- Master meta v5.1 requires both `execution` and `tasks` sections and constrained nested structures.
- Foreman code does not assert required fields or parse these domains at all.
- Risk: task/execution policy may be missing while runtime still responds `status: ok`.

### Gap C — No conditional semantics enforcement
- Envelope v5.1 conditional requirements (`task_request -> task`, `task_result -> result`) are not enforced.
- Scene v5.1 conditional requirements (`executed node -> start/end event IDs`, `completed_at -> terminal scene_status`) are not enforced.
- Risk: lifecycle invariants can be violated undetected.

### Gap D — No version-aware schema resolution
- Envelope allows embedded v5.1/v5/v4 meta via `oneOf`, but Foreman currently does not inspect or branch by schema version.
- Risk: migrations and compatibility paths cannot be safely governed.

### Gap E — No guardrails around strict nested capability maps
- Objects like `platform_capabilities`, `execution_hint`, `memory_checkpoint.hashchain`, and `task_nodes[*]` have constrained property sets.
- Foreman does not normalize/whitelist keys before routing.
- Risk: typo keys or out-of-contract extensions are silently propagated.

## Recommended remediation plan (implementation-ready)
1. Add JSON Schema validation middleware at API ingress for envelope v5.1 and scene v5.1 payload paths.
2. Add explicit master-meta parser to extract and validate `execution` + `tasks` domains before routing.
3. Reject unknown keys at ingress by validating against canonical schemas (no permissive pass-through).
4. Add version gate:
   - accept v5.1 by default
   - allow v5/v4 only when migration mode is enabled
5. Add unit tests for negative strictness cases:
   - unknown top-level key
   - unknown nested key under execution/task nodes
   - missing conditional-required fields.

## Priority
- **P0**: ingress schema validation + required domain extraction (`execution`, `tasks`)
- **P1**: conditional rule enforcement + version gate
- **P2**: richer diagnostics and policy telemetry for rejected payloads
