from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from .base_agent import AgentSchemas, BaseAgent
from .envelope import normalize_envelope, validate_envelope
from .io_utils import read_json, write_json
from .registry import find_vport, load_entrypoint, load_registry

JsonDict = Dict[str, Any]


def run_envelope(
    envelope: JsonDict,
    registry_path: str = "registry/vports.registry.v1.jsonl",
    logs_dir: str = "run_logs",
) -> Tuple[JsonDict, JsonDict]:
    envelope = normalize_envelope(envelope)
    validate_envelope(envelope)

    registry = load_registry(registry_path)
    vport = envelope["transport"]["vport"]
    rec = find_vport(registry, vport)

    build_fn = load_entrypoint(rec.entrypoint)

    schemas = AgentSchemas(
        input_schema_path=rec.input_schema_path,
        output_schema_path=rec.output_schema_path,
    )

    agent_runtime: BaseAgent = build_fn(schemas)  # type: ignore

    # Build a role-specific request object:
    role = envelope["target"]["role"]
    inputs = envelope["payload"]["inputs"] or {}
    constraints = envelope["payload"]["constraints"] or {}

    # Each wrapper expects its own schema contract, so we map accordingly:
    if role == "Foreman":
        request = {
            "task_id": envelope["id"],
            "objective": inputs.get("objective", ""),
            "intent": inputs.get("intent", "plan"),
            "constraints": constraints if constraints else {"deterministic": True},
            "inputs": inputs,
            "context_snapshot": envelope,
            "requested_outputs": inputs.get("requested_outputs", []),
            "routing_hints": inputs.get("routing_hints", {}),
            "trace": envelope.get("trace", {}),
        }
    elif role == "Librarian":
        request = {
            "task_id": envelope["id"],
            "query": inputs.get("query", ""),
            "intent": inputs.get("intent", "lookup"),
            "context_snapshot": envelope,
            "sources": inputs.get("sources", []),
            "filters": inputs.get("filters", {}),
            "output_format": inputs.get("output_format", "bullets"),
            "max_results": inputs.get("max_results", 10),
            "trace": envelope.get("trace", {}),
        }
    elif role == "Sorcerer":
        request = {
            "task_id": envelope["id"],
            "objective": inputs.get("objective", ""),
            "materials": inputs.get("materials", {}),
            "intent": inputs.get("intent", "draft"),
            "context_snapshot": envelope,
            "style_profile": inputs.get("style_profile", {}),
            "constraints": constraints,
            "trace": envelope.get("trace", {}),
        }
    elif role == "Judge":
        request = {
            "task_id": envelope["id"],
            "subject": inputs.get("subject", ""),
            "evaluation_type": inputs.get("evaluation_type", "quality_review"),
            "payload": inputs.get("payload", {}),
            "context_snapshot": envelope,
            "strictness": inputs.get("strictness", "high"),
            "expected_schema": inputs.get("expected_schema", ""),
            "notes": inputs.get("notes", ""),
            "trace": envelope.get("trace", {}),
        }
    elif role == "Messenger":
        request = {
            "task_id": envelope["id"],
            "message": inputs.get("message", ""),
            "targets": inputs.get("targets", []),
            "channels": inputs.get("channels", ["console"]),
            "context_snapshot": envelope,
            "formatting": inputs.get("formatting", {}),
            "attachments": inputs.get("attachments", []),
            "trace": envelope.get("trace", {}),
        }
    else:
        raise ValueError(f"Unsupported role: {role}")

    response, run_record = agent_runtime.handle(request)

    # persist logs deterministically
    out_dir = Path(logs_dir) / envelope["id"]
    write_json(out_dir / "envelope.json", envelope)
    write_json(out_dir / "response.json", response)
    write_json(out_dir / "run_record.json", run_record)

    return response, run_record


def run_envelope_file(
    envelope_path: str,
    registry_path: str = "registry/vports.registry.v1.jsonl",
    logs_dir: str = "run_logs",
) -> Tuple[JsonDict, JsonDict]:
    raw = read_json(envelope_path)
    # Accept either a plain envelope, or a bundle: {"envelope": {...}, "agent_profiles": {...}}
    if isinstance(raw, dict) and "envelope" in raw and isinstance(raw.get("envelope"), dict):
        bundle = raw
        env = bundle["envelope"]
        # Persist agent_profiles alongside logs for audit/debug (runner does not enforce profiles in v1).
        try:
            agent_profiles = bundle.get("agent_profiles")
            if agent_profiles is not None:
                logs_path = Path(logs_dir)
                logs_path.mkdir(parents=True, exist_ok=True)
                write_json(logs_path / "agent_profiles.json", agent_profiles)
        except Exception:
            pass
    else:
        env = raw
    return run_envelope(env, registry_path=registry_path, logs_dir=logs_dir)
