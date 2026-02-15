from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

JsonDict = Dict[str, Any]


def read_json(path: str | Path) -> JsonDict:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {p}")
    return data


def write_json(path: str | Path, data: JsonDict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
