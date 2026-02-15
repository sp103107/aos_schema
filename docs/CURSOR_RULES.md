# Cursor Rules (AoS Tools Bootstrap v1)

created_at: 2025-12-20T19:53:22Z
registry_sha256: 84c6740f9e3eb61a0b57a306af5658b9c7064837e5c118437f389ce808884fd9
repo_root: /mnt/data/aos_tools_bootstrap_v1

## Absolute Rules (non-negotiable)

- **Schema-first.** If a field is not defined by an applicable JSON Schema under `schemas_locked/`, it **must not** be invented.
- **No silent drift.** If requirements conflict, stop and write a `blocked` roadmap entry with the conflict.
- **All actions are logged.** Every atomic change-set must append:
  1) one record to `roadmap/template_ledger.jsonl`
  2) one record to `roadmap/roadmap.jsonl` (status change) and possibly `roadmap/done.jsonl` when completed
- **Mobile-callable by design.** Every tool must have at least one of:
  - an **MCP tool-server interface** OR
  - a **vPort handler** callable by the hub router OR
  - a minimal **HTTP** endpoint callable from a phone (curl / fetch)
- **Determinism preference.** Prefer pure functions, explicit inputs/outputs, stable filenames, and sha256 manifests.

## Required Contracts

### MCP Packet Contract
Request fields:
- vport, action, payload, timestamp, callback_id, compliance_metadata

Response fields:
- success, data? / error?, compliance_metadata

### File/Path Naming
- Roadmap stages: `STAGE_###`
- Episodes (optional): `episodes/episode_####.json`
- Tools: `tools/<tool_name>/...`
- Registries: `registry/*.jsonl`

## What to do when adding a tool

1) Create tool folder under `tools/<name>/`
2) Add `tools/<name>/tool_manifest.json` (inputs/outputs, entrypoint, interfaces)
3) Register in `registry/tools_catalog.jsonl` (must validate against `schemas_locked/tool_record.v1.schema.json`)
4) If vPort: register in `registry/vport_registry.jsonl`
5) Append ledger entry describing all files created/modified and why.



## v2 Unify/Batch Workflow

- Drop your historical tool folders under `inbox/`.
- Run: `python scripts/unify_tools.py --scan-root inbox --batch-size 25`
- Review outputs under `state/review_report.json` and `registry/*.proposed.jsonl`.
- Do NOT apply until you approve batch plan. To apply: `--apply`.
