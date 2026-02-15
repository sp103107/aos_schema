from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

if importlib.util.find_spec("httpx") is None:
    pytest.skip("httpx is required for FastAPI TestClient", allow_module_level=True)

from fastapi.testclient import TestClient

# Ensure `src` package imports resolve when running pytest from repo root.
FOREMAN_ROOT = Path(__file__).resolve().parents[1]
if str(FOREMAN_ROOT) not in sys.path:
    sys.path.insert(0, str(FOREMAN_ROOT))

import src.api.server as server
from src.engines.local_inproc import LocalTaskEngine
from src.registries.tool_lookup import ToolRegistry


def _build_base_payload(task_type: str = "planning") -> Dict[str, Any]:
    return {
        "envelope_version": "aos.master.envelope.v5_1",
        "envelope_kind": "task_request",
        "request_id": "urn:aos:req:test.stage012",
        "created_at": "2026-02-15T19:00:00Z",
        "invocation_type": "api_call",
        "platform_capabilities": {
            "artifact_generation": True,
            "file_generation": True,
            "file_download": False,
            "search_allowed": False,
        },
        "execution_hint": {"trust_level": "medium"},
        "task": {"objective": "MVP test"},
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
                "session_id": "urn:aos:session:test.stage012",
                "session_type": "workflow",
                "created_at": "2026-02-15T19:00:00Z",
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
                        "task_id": "urn:aos:task:test.stage012",
                        "task_type": task_type,
                        "description": "test task",
                        "depends_on": [],
                    }
                ]
            },
            "agents": {
                "agents": [
                    {
                        "agent_id": "urn:aos:agent:foreman.stage012",
                        "roles": ["foreman"],
                        "allowed_task_types": ["planning", "generation", "presentation"],
                    }
                ]
            },
            "outputs": {
                "artifacts": [
                    {
                        "artifact_id": "urn:aos:artifact:test.seed",
                        "artifact_type": "schema",
                        "description": "seed",
                        "hash_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        "produced_by_task_id": "urn:aos:task:test.stage012",
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


def _build_registry_file(tmp_path: Path) -> Path:
    path = tmp_path / "tools_catalog.jsonl"
    lines = [
        json.dumps({"id": "tools_catalog.meta.v1", "type": "aos.tool_catalog_meta"}),
        json.dumps(
            {
                "id": "urn:aos:tool:planner",
                "type": "aos.tool_record",
                "created_at": "2026-02-15T19:00:00Z",
                "name": "planner",
                "kind": "python_module",
                "entrypoint": "planner.run",
                "capabilities": ["planning", "task_type:planning"],
                "interfaces": {"mcp": None, "vport": None, "http": None},
                "versioning": {"semver": "0.1.0", "api_version": "v1"},
                "status": "active",
            }
        ),
        json.dumps(
            {
                "id": "urn:aos:tool:generator",
                "type": "aos.tool_record",
                "created_at": "2026-02-15T19:00:00Z",
                "name": "generator",
                "kind": "python_module",
                "entrypoint": "generator.run",
                "capabilities": ["generation", "presentation"],
                "interfaces": {"mcp": None, "vport": None, "http": None},
                "versioning": {"semver": "0.1.0", "api_version": "v1"},
                "status": "active",
            }
        ),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_happy_path_returns_task_result_with_artifacts(tmp_path: Path) -> None:
    registry_path = _build_registry_file(tmp_path)
    server.ENGINE = LocalTaskEngine(registry=ToolRegistry(registry_path=registry_path))

    with TestClient(server.app) as client:
        server.ENGINE = LocalTaskEngine(registry=ToolRegistry(registry_path=registry_path))
        response = client.post("/chat", json=_build_base_payload(task_type="planning"))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body.get("envelope_kind") == "task_result", "Expected envelope_kind=task_result"
    assert body.get("result", {}).get("status") == "completed", "Expected result.status=completed"
    artifacts = body.get("result", {}).get("artifacts")
    assert isinstance(artifacts, list), "Expected result.artifacts to be a list"
    assert len(artifacts) > 0, "Expected at least one generated artifact"


def test_strict_mode_rejects_legacy_v4(tmp_path: Path) -> None:
    registry_path = _build_registry_file(tmp_path)
    server.ENGINE = LocalTaskEngine(registry=ToolRegistry(registry_path=registry_path))

    payload = _build_base_payload(task_type="planning")
    payload["envelope_version"] = "aos.master.envelope.v4"

    with TestClient(server.app) as client:
        server.ENGINE = LocalTaskEngine(registry=ToolRegistry(registry_path=registry_path))
        response = client.post("/chat", json=payload)

    assert response.status_code == 400, f"Expected 400 for legacy v4, got {response.status_code}"
    detail = response.json().get("detail", {})
    assert detail.get("error") == "legacy_schemas_disabled", (
        f"Expected legacy_schemas_disabled, got {detail}"
    )


def test_registry_lookup_unknown_task_type_is_graceful(tmp_path: Path) -> None:
    registry_path = _build_registry_file(tmp_path)
    server.ENGINE = LocalTaskEngine(registry=ToolRegistry(registry_path=registry_path))

    payload = _build_base_payload(task_type="unknown_magic_tool")

    with TestClient(server.app) as client:
        server.ENGINE = LocalTaskEngine(registry=ToolRegistry(registry_path=registry_path))
        response = client.post("/chat", json=payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    unsupported = body.get("result", {}).get("unsupported_tasks", [])
    assert isinstance(unsupported, list), "Expected unsupported_tasks to be a list"
    assert unsupported, "Expected at least one unsupported task entry"
    assert unsupported[0].get("reason") == "tool_not_found", (
        f"Expected reason=tool_not_found, got {unsupported[0]}"
    )
