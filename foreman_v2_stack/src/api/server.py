from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, WebSocket
from jsonschema import Draft202012Validator, RefResolver

from src.engines.local_inproc import LocalTaskEngine
from src.interfaces.engine import BaseTaskEngine

app = FastAPI(title="Foreman v2 Agent API")

DEFAULT_ENVELOPE_VERSION = "aos.master.envelope.v5_1"
LEGACY_ENVELOPE_VERSIONS = {
    "aos.master.envelope.v5",
    "aos.master.envelope.v4",
}

ENGINE: BaseTaskEngine | None = None


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _legacy_schemas_enabled() -> bool:
    return _is_truthy(os.getenv("AOS_ALLOW_LEGACY_SCHEMAS"))


def _packet_mode_enabled() -> bool:
    # If true, /chat returns an MCP packet instead of executing the local engine.
    return _is_truthy(os.getenv("AOS_FOREMAN_PACKET_MODE"))


def _prune_unresolvable_master_refs(
    envelope_schema: Dict[str, Any],
    available_master_ids: set[str],
    allowed_master_ids: set[str],
) -> Dict[str, Any]:
    schema_copy = deepcopy(envelope_schema)
    embedded_master_meta = (
        schema_copy.get("properties", {})
        .get("embedded_master_meta", {})
    )
    one_of = embedded_master_meta.get("oneOf")
    if isinstance(one_of, list):
        filtered = [
            entry
            for entry in one_of
            if isinstance(entry, dict)
            and isinstance(entry.get("$ref"), str)
            and entry["$ref"] in available_master_ids
            and entry["$ref"] in allowed_master_ids
        ]
        if filtered:
            embedded_master_meta["oneOf"] = filtered
    return schema_copy


def _build_envelope_validators() -> Dict[str, Draft202012Validator]:
    repo_root = Path(__file__).resolve().parents[3]
    schema_root = (
        repo_root
        / "aos_v4_meta_envelope_scene_bundle"
        / "aos_v4_meta_envelope_scene_bundle"
        / "schemas"
    )

    master_schemas = {
        "v5_1": _load_json(schema_root / "master" / "aos.master.meta.v5_1.schema.json"),
        "v5": _load_json(schema_root / "master" / "aos.master.meta.v5.schema.json"),
        "v4": _load_json(schema_root / "master" / "aos.master.meta.v4.schema.json"),
    }
    master_ids = {name: schema["$id"] for name, schema in master_schemas.items()}
    master_store = {schema["$id"]: schema for schema in master_schemas.values()}
    available_master_ids = set(master_store.keys())

    envelope_schemas = {
        "aos.master.envelope.v5_1": _load_json(
            schema_root / "envelope" / "aos.master.envelope.v5_1.schema.json"
        ),
        "aos.master.envelope.v5": _load_json(
            schema_root / "envelope" / "aos.master.envelope.v5.schema.json"
        ),
        "aos.master.envelope.v4": _load_json(
            schema_root / "envelope" / "aos.master.envelope.v4.schema.json"
        ),
    }

    allowed_master_map = {
        "aos.master.envelope.v5_1": {master_ids["v5_1"]},
        "aos.master.envelope.v5": {master_ids["v5"], master_ids["v4"]},
        "aos.master.envelope.v4": {master_ids["v4"]},
    }

    validators: Dict[str, Draft202012Validator] = {}
    for envelope_version, envelope_schema in envelope_schemas.items():
        normalized_envelope = _prune_unresolvable_master_refs(
            envelope_schema,
            available_master_ids,
            allowed_master_map.get(envelope_version, available_master_ids),
        )
        resolver = RefResolver.from_schema(
            normalized_envelope,
            store=master_store,
        )
        validators[envelope_version] = Draft202012Validator(
            normalized_envelope,
            resolver=resolver,
        )
    return validators


ENVELOPE_VALIDATORS = _build_envelope_validators()


def _raise_validation_error(
    *,
    error: str,
    message: str,
    path: list[str | int] | None = None,
    schema_path: list[str | int] | None = None,
    validator: str | None = None,
) -> None:
    raise HTTPException(
        status_code=400,
        detail={
            "error": error,
            "message": message,
            "path": path or [],
            "schema_path": schema_path or [],
            "validator": validator,
        },
    )


def _enforce_version_gate(payload: Dict[str, Any]) -> Draft202012Validator:
    envelope_version = payload.get("envelope_version")
    if not isinstance(envelope_version, str):
        _raise_validation_error(
            error="invalid_envelope_version",
            message="envelope_version must be provided as a string.",
            path=["envelope_version"],
            validator="type",
        )

    if envelope_version == DEFAULT_ENVELOPE_VERSION:
        return ENVELOPE_VALIDATORS[DEFAULT_ENVELOPE_VERSION]

    if envelope_version in LEGACY_ENVELOPE_VERSIONS:
        if not _legacy_schemas_enabled():
            _raise_validation_error(
                error="legacy_schemas_disabled",
                message=(
                    f"Legacy envelope version '{envelope_version}' is disabled. "
                    "Set AOS_ALLOW_LEGACY_SCHEMAS=true to enable v5/v4 support."
                ),
                path=["envelope_version"],
                validator="version_gate",
            )
        return ENVELOPE_VALIDATORS[envelope_version]

    _raise_validation_error(
        error="unsupported_envelope_version",
        message=(
            f"Unsupported envelope_version '{envelope_version}'. "
            f"Allowed: {DEFAULT_ENVELOPE_VERSION}"
            " (plus v5/v4 when AOS_ALLOW_LEGACY_SCHEMAS=true)."
        ),
        path=["envelope_version"],
        validator="enum",
    )


def _enforce_conditional_envelope_requirements(payload: Dict[str, Any]) -> None:
    envelope_kind = payload.get("envelope_kind")

    if envelope_kind == "task_request":
        task = payload.get("task")
        if task is None or not isinstance(task, dict):
            _raise_validation_error(
                error="conditional_requirement_failed",
                message="envelope_kind=task_request requires a non-null task object.",
                path=["task"],
                schema_path=["allOf", "task_request", "required", "task"],
                validator="conditional",
            )

    if envelope_kind == "task_result":
        result = payload.get("result")
        if result is None or not isinstance(result, dict):
            _raise_validation_error(
                error="conditional_requirement_failed",
                message="envelope_kind=task_result requires a non-null result object.",
                path=["result"],
                schema_path=["allOf", "task_result", "required", "result"],
                validator="conditional",
            )


def validate_envelope_payload(payload: Dict[str, Any]) -> None:
    validator = _enforce_version_gate(payload)

    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        first_error = errors[0]
        _raise_validation_error(
            error="invalid_envelope_payload",
            message=first_error.message,
            path=list(first_error.path),
            schema_path=[str(part) for part in first_error.schema_path],
            validator=first_error.validator,
        )

    _enforce_conditional_envelope_requirements(payload)


def to_mcp(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Keep this lightweight; the real MCP envelope builder can live elsewhere.
    return {
        "source_atom": payload.get("request_id", "api"),
        "target_atom": "foreman",
        "payload": payload,
        "protocol": "MCP_PACKET_VPORT",
    }


@app.on_event("startup")
async def on_startup() -> None:
    global ENGINE
    ENGINE = LocalTaskEngine()


def _require_engine() -> BaseTaskEngine:
    if ENGINE is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "engine_not_ready",
                "message": "Task engine is not initialized.",
            },
        )
    return ENGINE


@app.post("/chat")
async def chat(request_data: Dict[str, Any]) -> Dict[str, Any]:
    validate_envelope_payload(request_data)

    if _packet_mode_enabled():
        return {"status": "ok", "mode": "packet", "packet": to_mcp(request_data)}

    engine = _require_engine()
    try:
        result_envelope = engine.submit_task(request_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "engine_submission_error",
                "message": str(exc),
            },
        ) from exc

    if not isinstance(result_envelope, dict):
        raise HTTPException(
            status_code=500,
            detail={
                "error": "invalid_engine_result",
                "message": "Engine must return a result envelope object.",
            },
        )

    return result_envelope


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    await ws.send_json({"status": "connected"})
