# foreman_v2_stack

Foreman v2 stack service exposing a FastAPI gateway that validates AoS envelope payloads before forwarding MCP packets to the handler/router layers.

## API structure

- `src/api/server.py`
  - FastAPI app entrypoint.
  - `/chat` endpoint performs strict envelope validation + version gating.
  - `/ws` websocket endpoint for lightweight connectivity checks.
- `src/handler/minimal_handler.py`
  - Validates MCP packet shape and extracts `execution` + `tasks` domains from `embedded_master_meta`.
- `src/router/mcp_router.py`
  - Router abstraction stub for backend bus integration.

## Requirements

Install runtime dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Run the server

From `foreman_v2_stack/`:

```bash
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

Then post to `/chat`:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d @../aos_v4_meta_envelope_scene_bundle/aos_v4_meta_envelope_scene_bundle/examples/aos.master.envelope.v5_1.task_request.example.json
```

## /chat endpoint contract

`POST /chat` expects an AoS envelope payload (JSON object).

Validation behavior:

1. **Version Gate**
   - Strict mode default: only `envelope_version = aos.master.envelope.v5_1` is accepted.
   - Legacy mode (optional): `aos.master.envelope.v5` and `aos.master.envelope.v4` are allowed only when:

   ```bash
   export AOS_ALLOW_LEGACY_SCHEMAS=true
   ```

2. **Schema Validation**
   - Payload is validated with JSON Schema (Draft 2020-12).
   - Unknown keys are rejected because envelope schemas are strict (`additionalProperties: false`).

3. **Conditional Rules**
   - If `envelope_kind == "task_request"`, `task` must be present and be an object.
   - If `envelope_kind == "task_result"`, `result` must be present and be an object.

Validation failures return HTTP 400 with structured error details.

## Strict Mode summary

- Strict mode (default): v5.1 only.
- Legacy support (explicit opt-in):

```bash
export AOS_ALLOW_LEGACY_SCHEMAS=true
```

Use legacy mode only for migration workloads; disable in normal production posture.
