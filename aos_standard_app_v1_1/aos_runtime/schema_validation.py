from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from jsonschema import Draft7Validator

JsonDict = Dict[str, Any]


class SchemaValidationError(ValueError):
    pass


@lru_cache(maxsize=256)
def load_schema(schema_path: str) -> JsonDict:
    p = Path(schema_path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SchemaValidationError(f"Schema is not a JSON object: {schema_path}")
    return data


@lru_cache(maxsize=256)
def get_validator(schema_path: str) -> Draft7Validator:
    schema = load_schema(schema_path)
    return Draft7Validator(schema)


def validate(instance: JsonDict, schema_path: str) -> None:
    validator = get_validator(schema_path)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        lines: List[str] = []
        for e in errors[:25]:
            path = ".".join(str(p) for p in e.path) if e.path else "(root)"
            lines.append(f"{path}: {e.message}")
        raise SchemaValidationError("Schema validation failed:\n- " + "\n- ".join(lines))
