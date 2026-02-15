from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class VPortRecord:
    vport: str
    role: str
    agent_urn: str
    input_schema_path: str
    output_schema_path: str
    entrypoint: str  # "module.submodule:function"


def _parse_jsonl(path: Path) -> List[JsonDict]:
    rows: List[JsonDict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def load_registry(registry_jsonl_path: str | Path) -> List[VPortRecord]:
    p = Path(registry_jsonl_path)
    rows = _parse_jsonl(p)
    out: List[VPortRecord] = []
    for r in rows:
        out.append(VPortRecord(
            vport=r["vport"],
            role=r["role"],
            agent_urn=r["agent_urn"],
            input_schema_path=r["input_schema_path"],
            output_schema_path=r["output_schema_path"],
            entrypoint=r["entrypoint"],
        ))
    return out


def find_vport(registry: List[VPortRecord], vport: str) -> VPortRecord:
    for rec in registry:
        if rec.vport == vport:
            return rec
    raise KeyError(f"Unknown vPort: {vport}")


def load_entrypoint(entrypoint: str):
    """Import entrypoint like 'agents.foreman.agent:build_runtime'"""
    if ":" not in entrypoint:
        raise ValueError(f"Invalid entrypoint (missing ':'): {entrypoint}")
    mod_name, fn_name = entrypoint.split(":", 1)
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, fn_name)
    return fn
