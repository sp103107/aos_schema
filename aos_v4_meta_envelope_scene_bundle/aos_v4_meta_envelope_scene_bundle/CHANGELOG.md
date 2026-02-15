# CHANGELOG — AoS v4 Bundle (Meta + Envelope + Scene)

## 2026-02-13T03:35:00Z
- Added v5.1 schemas:
  - `schemas/master/aos.master.meta.v5_1.schema.json`
  - `schemas/envelope/aos.master.envelope.v5_1.schema.json`
  - `schemas/temporal/aos.scene.v5_1.schema.json`
- Added v5.1 examples:
  - `examples/aos.master.envelope.v5_1.task_request.example.json`
- Added schema-pack manifest v1.1 with optional trace fields:
  - `schemas/aos.schema_pack.manifest.v1_1.schema.json`
  - `examples/aos.schema_pack.manifest.v1_1.example.json`
- v5 preserved, v4 untouched.

## 2026-02-13T02:55:00Z
- Added v5 schemas:
  - `schemas/master/aos.master.meta.v5.schema.json`
  - `schemas/envelope/aos.master.envelope.v5.schema.json`
  - `schemas/temporal/aos.scene.v5.schema.json`
- Added schema pack artifacts:
  - `schemas/aos.schema_pack.manifest.v1.schema.json`
  - `schemas/aos.validation_report.v1.schema.json`
- Added v5 examples:
  - `examples/aos.master.envelope.v5.task_request.example.json`
  - `examples/aos.schema_pack.manifest.v1.example.json`
  - `examples/aos.validation_report.v1.example.json`
- Added validation helper: `scripts/validate_all.py`

## 2026-02-13T02:28:58Z
- Added `aos.master.envelope.v4.schema.json`
  - Explicit `envelope_version` + `envelope_kind`
  - Optional strict `temporal` binding (season/episode/scene/phase)
  - Optional `platform_capabilities.tooling` (incl. connectors)
  - `embedded_master_meta` supports v4 (preferred) and v3 (migration) via `oneOf`
- Included previous v4 artifacts:
  - `aos.master.meta.v4.schema.json`
  - `aos.scene.v4.schema.json`
  - Filled scenes + episode docs + checklists
