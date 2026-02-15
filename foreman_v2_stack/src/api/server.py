from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, WebSocket
from jsonschema import Draft202012Validator, RefResolver

app = FastAPI(title="Agent API")


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_envelope_validator() -> Draft202012Validator:
    repo_root = Path(__file__).resolve().parents[3]
    schema_root = (
        repo_root
        / "aos_v4_meta_envelope_scene_bundle"
        / "aos_v4_meta_envelope_scene_bundle"
        / "schemas"
    )

    envelope_schema = _load_json(
        schema_root / "envelope" / "aos.master.envelope.v5_1.schema.json"
    )
    master_v5_1 = _load_json(schema_root / "master" / "aos.master.meta.v5_1.schema.json")
    master_v5 = _load_json(schema_root / "master" / "aos.master.meta.v5.schema.json")
    master_v4 = _load_json(schema_root / "master" / "aos.master.meta.v4.schema.json")

    resolver = RefResolver.from_schema(
        envelope_schema,
        store={
            master_v5_1["$id"]: master_v5_1,
            master_v5["$id"]: master_v5,
            master_v4["$id"]: master_v4,
        },
    )
    return Draft202012Validator(envelope_schema, resolver=resolver)


ENVELOPE_VALIDATOR = _build_envelope_validator()


def validate_envelope_payload(payload: Dict[str, Any]) -> None:
    errors = sorted(ENVELOPE_VALIDATOR.iter_errors(payload), key=lambda err: list(err.path))
    if not errors:
        return

    first_error = errors[0]
    raise HTTPException(
        status_code=400,
        detail={
            "error": "invalid_envelope_payload",
            "message": first_error.message,
            "path": list(first_error.path),
            "schema_path": [str(part) for part in first_error.schema_path],
            "validator": first_error.validator,
        },
    )


def to_mcp(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_atom": payload.get("request_id", "api"),
        "target_atom": "foreman",
        "payload": payload,
        "protocol": "MCP_PACKET_VPORT",
    }


@app.post("/chat")
async def chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    validate_envelope_payload(payload)
    packet = to_mcp(payload)
    return {"status": "ok", "packet": packet}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    await ws.send_json({"status": "connected"})
