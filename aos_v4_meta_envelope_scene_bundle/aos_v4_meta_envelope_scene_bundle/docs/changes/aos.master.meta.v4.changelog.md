# AoS Master Meta v4 Changelog

## What changed
- Added a top-level `runtime` configuration block aligned to `declared_capabilities.runtime`.
- Clarified schema descriptions: declared capabilities are supported superset; config blocks are enabled/selected subset.
- Clarified execution semantics (base lifecycle mode vs feature flags) and session semantics (run modality vs supported features).
- Added `multi_stage_dag` to `task_type` to match declared task capabilities.
- Aligned audit naming with capability values via alias fields and added `lint_enforced`.
- Constrained `outputs.artifacts[].artifact_type` to known types with `custom:` support.
- `declared_capabilities.runtime` is now optional; runtime may be environment-owned.
- Added conditional requirement: if root `runtime` is present, `declared_capabilities.runtime` must be declared.
- Strengthened runtime conditional: when `runtime` is present, `declared_capabilities.runtime` must be non-empty.
- Added `examples/aos.master.meta.v4.example.runtime_enabled.json`.
- Added `examples/aos.master.meta.v4.example.runtime_invalid_missing_declared.json` (invalid); validate manually with `python tools/validate_schema.py --example examples/aos.master.meta.v4.example.runtime_invalid_missing_declared.json` and expect a validation error.

## Why
- Remove ambiguity about runtime configuration placement.
- Reduce drift between declared capabilities and enabled configuration fields.
- Ensure task, audit, and output types are realizable in instances.

## Migration notes
- Existing v4 instances remain valid; aliases in `audit` are optional.
- New instances should use `custom:` prefix for non-standard `artifact_type` values.
- `runtime` is optional, but recommended when `declared_capabilities.runtime` is present.

## Audit alias precedence
- Canonical fields: `record_episode`, `schema_validation_required`.
- Alias fields: `episode_recorded`, `schema_validation`.
- Rule: runtime should normalize aliases into canonical fields; canonical wins on conflict.

## Validation
- Install dev dependency: `pip install -r requirements-dev.txt`
- Run: `python tools/validate_schema.py`
