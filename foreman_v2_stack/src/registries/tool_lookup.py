from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ToolRecord:
    """Typed view over a tool record from registry/tools_catalog.jsonl."""

    id: str
    type: str
    created_at: str
    name: str
    kind: str
    entrypoint: str
    capabilities: List[str]
    interfaces: Dict[str, Any]
    versioning: Dict[str, str]
    status: str

    @staticmethod
    def from_dict(raw: Dict[str, Any]) -> "ToolRecord":
        required_fields = [
            "id",
            "type",
            "created_at",
            "name",
            "kind",
            "entrypoint",
            "capabilities",
            "interfaces",
            "versioning",
            "status",
        ]
        missing = [field for field in required_fields if field not in raw]
        if missing:
            raise ValueError(f"missing required fields: {missing}")

        capabilities = raw.get("capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(item, str) for item in capabilities):
            raise ValueError("capabilities must be a list of strings")

        interfaces = raw.get("interfaces")
        versioning = raw.get("versioning")
        if not isinstance(interfaces, dict):
            raise ValueError("interfaces must be an object")
        if not isinstance(versioning, dict):
            raise ValueError("versioning must be an object")

        return ToolRecord(
            id=str(raw["id"]),
            type=str(raw["type"]),
            created_at=str(raw["created_at"]),
            name=str(raw["name"]),
            kind=str(raw["kind"]),
            entrypoint=str(raw["entrypoint"]),
            capabilities=[str(item) for item in capabilities],
            interfaces=interfaces,
            versioning={str(k): str(v) for k, v in versioning.items()},
            status=str(raw["status"]),
        )


class ToolRegistry:
    """Tool catalog adapter for capability lookup by task type."""

    @staticmethod
    def _find_repo_root(start: Path) -> Path:
        for candidate in (start, *start.parents):
            if (candidate / ".git").exists() or (
                (candidate / "foreman_v2_stack").exists()
                and (candidate / "registry" / "tools_catalog.jsonl").exists()
            ):
                return candidate
        raise RuntimeError("Unable to locate repository root from tool_lookup.py path")

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        if registry_path is None:
            repo_root = self._find_repo_root(Path(__file__).resolve())
            registry_path = repo_root / "registry" / "tools_catalog.jsonl"

        self.registry_path = registry_path
        self.records: List[ToolRecord] = []
        self.task_type_index: Dict[str, ToolRecord] = {}
        self.load_errors: List[str] = []

        self._load_registry()

    def _index_task_types(self, record: ToolRecord) -> None:
        for capability in record.capabilities:
            tokens: List[str] = [capability]
            if capability.startswith("task_type:"):
                tokens.append(capability.split(":", 1)[1])
            if capability.startswith("task:"):
                tokens.append(capability.split(":", 1)[1])

            for token in tokens:
                key = token.strip().lower()
                if key and key not in self.task_type_index:
                    self.task_type_index[key] = record

    def _load_registry(self) -> None:
        if not self.registry_path.exists():
            self.load_errors.append(f"registry_not_found:{self.registry_path}")
            return

        try:
            with open(self.registry_path, "r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError as exc:
                        self.load_errors.append(
                            f"invalid_json line={line_number} error={exc.msg}"
                        )
                        continue

                    # Skip metadata rows and non-tool records.
                    if raw.get("type") != "aos.tool_record":
                        continue

                    try:
                        record = ToolRecord.from_dict(raw)
                    except ValueError as exc:
                        self.load_errors.append(
                            f"invalid_tool_record line={line_number} error={exc}"
                        )
                        continue

                    self.records.append(record)
                    self._index_task_types(record)
        except OSError as exc:
            self.load_errors.append(f"registry_read_error:{exc}")

    def resolve_tool(self, task_type: str) -> Optional[ToolRecord]:
        lookup = task_type.strip().lower()
        if not lookup:
            return None
        return self.task_type_index.get(lookup)
