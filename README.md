# AoS Tools Bootstrap (v1)

This repo bootstraps a **tools directory** for Stephen's AoS ecosystem:
- schema-locked
- JSONL-logged
- MCP/vPort/HTTP callable (mobile-first)
- Cursor-friendly traceability

## Key files
- `state/project_bootstrap.json` — single source of truth (paths, locks, rules)
- `roadmap/roadmap.jsonl` — staged work plan
- `roadmap/template_ledger.jsonl` — append-only audit trail for Cursor/agents
- `registry/tools_catalog.jsonl` — discoverable tools registry (for RAG ingestion)

## Contracts
- Schemas live in `schemas_locked/`.
- Cursor must obey `docs/CURSOR_RULES.md`.

created_at: 2025-12-20T19:53:22Z


## v2 Additions
- `scripts/unify_tools.py` scan/review + batch proposal
- `inbox/` drop-zone for your 2-year tools
- proposed registries written before apply
