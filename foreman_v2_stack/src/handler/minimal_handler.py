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


def process_mcp_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Stub: validate and echo. Replace with real MCP routing.
    Expected keys: source_atom, target_atom, payload, protocol
    """
    if not isinstance(packet, dict):
        return {"status": "error", "error": "invalid_packet"}
    return {
        "status": "ok",
        "echo": {
            "target_atom": packet.get("target_atom"),
            "payload_keys": (
                list(packet.get("payload", {}).keys())
                if isinstance(packet.get("payload"), dict)
                else None
            ),
        },
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
