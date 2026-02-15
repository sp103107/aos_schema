from __future__ import annotations

from typing import Any, Dict

from .schema_validation import validate

JsonDict = Dict[str, Any]


DEFAULT_ENVELOPE_SCHEMA_PATH = "schemas/envelope/aos.envelope.overlay.v1.schema.json"


def normalize_envelope(envelope: JsonDict) -> JsonDict:
    """
    Normalize alternate envelope shapes into the canonical aos.envelope.overlay.v1 shape.

    Supported alternate shape (frontend legacy):
      - agent -> target
      - mcp -> transport
      - objective (top-level) -> payload.inputs.objective
      - payload.notes -> payload.inputs.notes

    This enables backwards compatibility while keeping the schema authoritative.
    """
    if not isinstance(envelope, dict):
        return envelope

    # Already canonical
    if "target" in envelope and "transport" in envelope and "payload" in envelope:
        return envelope

    # Legacy/alt shape detection
    if "agent" not in envelope and "mcp" not in envelope:
        return envelope

    agent = envelope.get("agent") or {}
    mcp = envelope.get("mcp") or {}
    compliance = (mcp.get("compliance_metadata") or {}) if isinstance(mcp, dict) else {}

    target = {
        "role": agent.get("role") or agent.get("agent_role") or "Foreman",
        "domain": agent.get("domain") or agent.get("agent_domain") or "aos.domain.core",
        "urn": agent.get("urn") or agent.get("agent_urn") or f"urn:aos:agent:{str(agent.get('role') or 'foreman').lower()}.core",
    }

    comm = compliance.get("communication_pattern") or compliance.get("pattern") or "request_response"
    if comm not in ("request_response", "fire_and_forget", "stream"):
        comm = "request_response"

    transport = {
        "vport": (mcp.get("vport") if isinstance(mcp, dict) else None) or "router",
        "protocol_version": str(compliance.get("protocol_version") or "1.0"),
        "communication_pattern": comm,
        "callback_id": str(compliance.get("callback_id") or ""),
    }

    payload = envelope.get("payload") or {}
    inputs = payload.get("inputs") or {}
    constraints = payload.get("constraints") or {}

    # Merge top-level objective + legacy notes
    if "objective" in envelope and "objective" not in inputs:
        inputs["objective"] = envelope.get("objective") or ""
    if "notes" in payload and "notes" not in inputs:
        inputs["notes"] = payload.get("notes") or ""

    normalized: JsonDict = {k: v for k, v in envelope.items() if k not in ("agent", "mcp", "objective")}
    normalized["target"] = target
    normalized["transport"] = transport
    normalized["payload"] = {"inputs": inputs, "constraints": constraints}
    return normalized


def validate_envelope(envelope: JsonDict, schema_path: str = DEFAULT_ENVELOPE_SCHEMA_PATH) -> None:
    validate(envelope, schema_path)


def envelope_to_agent_request(envelope: JsonDict) -> JsonDict:
    """
    Map AoS envelope payload into an agent request object. Role schemas remain authoritative.

    Rule:
      - task_id = envelope.id
      - role = envelope.target.role
      - intent = payload.inputs.intent if present else role-specific default
      - context_snapshot includes project + trace + full envelope header
      - role-specific additional keys are provided inside payload.inputs
    """
    task_id = envelope["id"]
    role = envelope["target"]["role"]
    inputs = envelope["payload"]["inputs"] or {}
    constraints = envelope["payload"]["constraints"] or {}

    req: JsonDict = {
        "task_id": task_id,
        "role": role,
        "intent": inputs.get("intent", "run"),
        "context_snapshot": {
            "project": envelope.get("project", {}),
            "target": envelope.get("target", {}),
            "transport": envelope.get("transport", {}),
            "bundle_id": envelope.get("bundle_id"),
            "trace": envelope.get("trace", {}),
        },
        "trace": envelope.get("trace", {}),
    }

    # Pass through full inputs/constraints for role wrappers to consume
    req["payload"] = inputs
    req["constraints"] = constraints
    return req
