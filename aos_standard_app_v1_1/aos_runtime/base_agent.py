from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Protocol, Tuple

from .ids import sha256_json
from .schema_validation import validate, SchemaValidationError

JsonDict = Dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AgentSchemas:
    input_schema_path: str
    output_schema_path: str


class AgentImpl(Protocol):
    role: str

    def run(self, request: JsonDict) -> JsonDict:
        ...


class BaseAgent:
    """
    The one true runtime handler.

    Enforces:
      - input validation
      - output validation
      - deterministic run_record
      - timing + hashes
    """

    def __init__(self, impl: AgentImpl, schemas: AgentSchemas) -> None:
        self.impl = impl
        self.schemas = schemas

    def handle(self, request: JsonDict) -> Tuple[JsonDict, JsonDict]:
        t0 = time.time()
        validate(request, self.schemas.input_schema_path)

        started_at = utc_now_iso()
        in_hash = sha256_json(request)

        response = self.impl.run(request)

        validate(response, self.schemas.output_schema_path)
        ended_at = utc_now_iso()
        dt_ms = int((time.time() - t0) * 1000)

        out_hash = sha256_json(response)

        run_record = {
            "task_id": request.get("task_id"),
            "role": getattr(self.impl, "role", "UNKNOWN"),
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_ms": dt_ms,
            "input_schema_path": self.schemas.input_schema_path,
            "output_schema_path": self.schemas.output_schema_path,
            "input_sha256": in_hash,
            "output_sha256": out_hash,
            "status": response.get("status"),
        }
        return response, run_record
