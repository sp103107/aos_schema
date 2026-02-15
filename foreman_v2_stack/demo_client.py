from __future__ import annotations

import json
from typing import Any, Dict

import httpx


def build_sample_payload() -> Dict[str, Any]:
    return {
        "envelope_version": "aos.master.envelope.v5_1",
        "envelope_kind": "task_request",
        "request_id": "urn:aos:req:demo.client",
        "created_at": "2026-02-15T19:10:00Z",
        "invocation_type": "api_call",
        "platform_capabilities": {
            "artifact_generation": True,
            "file_generation": True,
            "file_download": False,
            "search_allowed": False,
        },
        "execution_hint": {"trust_level": "medium"},
        "task": {"objective": "Generate MVP planning artifact"},
        "embedded_master_meta": {
            "declared_capabilities": {
                "session": ["workflow"],
                "governance": ["judge_required"],
                "execution": ["execute"],
                "tasks": ["planning"],
                "agents": ["foreman"],
                "outputs": ["schema"],
                "memory": ["working_set"],
                "audit": ["schema_validation"],
            },
            "session": {
                "session_id": "urn:aos:session:demo.client",
                "session_type": "workflow",
                "created_at": "2026-02-15T19:10:00Z",
            },
            "governance": {
                "judge_required": True,
                "human_in_loop": False,
                "halt_on_violation": True,
                "deterministic_required": False,
                "refusal_allowed": True,
            },
            "execution": {
                "mode": "execute",
                "step_gated": False,
                "simulation": False,
                "replay_mode": False,
            },
            "tasks": {
                "tasks": [
                    {
                        "task_id": "urn:aos:task:demo.plan",
                        "task_type": "planning",
                        "description": "Create a demo plan",
                        "depends_on": [],
                    }
                ]
            },
            "agents": {
                "agents": [
                    {
                        "agent_id": "urn:aos:agent:foreman.demo",
                        "roles": ["foreman"],
                        "allowed_task_types": ["planning"],
                    }
                ]
            },
            "outputs": {
                "artifacts": [
                    {
                        "artifact_id": "urn:aos:artifact:demo.seed",
                        "artifact_type": "schema",
                        "description": "seed",
                        "hash_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        "produced_by_task_id": "urn:aos:task:demo.plan",
                        "schema_id": "https://aos.dev/schemas/master/aos.master.meta.v5_1.schema.json",
                    }
                ]
            },
            "memory": {
                "allowed_tiers": ["working_set"],
                "writes_must_be_declared": True,
            },
            "audit": {
                "record_episode": True,
                "exportable_logs": True,
                "schema_validation_required": True,
            },
        },
    }


def main() -> None:
    payload = build_sample_payload()

    print("=== Input Envelope ===")
    print(json.dumps(payload, indent=2))

    response = httpx.post("http://localhost:8000/chat", json=payload, timeout=30.0)
    print(f"\nHTTP {response.status_code}")

    try:
        result = response.json()
    except ValueError:
        print(response.text)
        return

    print("\n=== Result Envelope ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
