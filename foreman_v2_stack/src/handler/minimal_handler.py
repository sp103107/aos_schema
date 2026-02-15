#!/usr/bin/env python3
"""
Minimal MCP-first Handler Stub (Standalone Agent)
-------------------------------------------------
Loads `registry/atoms_registry.jsonl` and exposes a minimal process() entry
that would be wired to the Message Bus via MCP in production.

This is a skeleton for integration; extend with your MCP server adapter.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterable


ALLOWED_PACKET_KEYS = {"source_atom", "target_atom", "payload", "protocol"}


def load_atoms_registry(registry_path: Path) -> Iterable[Dict[str, Any]]:
    with open(registry_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _reject_unknown_packet_keys(packet: Dict[str, Any]) -> Dict[str, Any] | None:
    unknown_keys = sorted(set(packet.keys()) - ALLOWED_PACKET_KEYS)
    if not unknown_keys:
        return None
    return {
        "status": "error",
        "error": "unknown_packet_keys",
        "details": {"unknown_keys": unknown_keys, "allowed_keys": sorted(ALLOWED_PACKET_KEYS)},
    }


def _extract_execution_and_tasks_domains(payload: Dict[str, Any]) -> Dict[str, Any]:
    embedded_master_meta = payload.get("embedded_master_meta")
    if not isinstance(embedded_master_meta, dict):
        raise ValueError("payload.embedded_master_meta must be an object")

    execution_domain = embedded_master_meta.get("execution")
    tasks_domain = embedded_master_meta.get("tasks")

    if not isinstance(execution_domain, dict):
        raise ValueError("embedded_master_meta.execution must be an object")
    if not isinstance(tasks_domain, dict):
        raise ValueError("embedded_master_meta.tasks must be an object")

    return {
        "execution": execution_domain,
        "tasks": tasks_domain,
    }


def process_mcp_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Validate packet shape and extract master-meta execution/task domains.

    Expected keys: source_atom, target_atom, payload, protocol
    """
    if not isinstance(packet, dict):
        return {"status": "error", "error": "invalid_packet"}

    unknown_keys_error = _reject_unknown_packet_keys(packet)
    if unknown_keys_error is not None:
        return unknown_keys_error

    payload = packet.get("payload")
    if not isinstance(payload, dict):
        return {
            "status": "error",
            "error": "invalid_payload",
            "details": {"message": "packet.payload must be an object"},
        }

    try:
        extracted_domains = _extract_execution_and_tasks_domains(payload)
    except ValueError as exc:
        return {
            "status": "error",
            "error": "invalid_embedded_master_meta",
            "details": {"message": str(exc)},
        }

    return {
        "status": "ok",
        "target_atom": packet.get("target_atom"),
        "domains": extracted_domains,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    registry = repo_root / "registry" / "atoms_registry.jsonl"
    atoms = list(load_atoms_registry(registry))
    print(
        f"Loaded {len(atoms)} atoms from {registry}"
    )


if __name__ == "__main__":
    main()
