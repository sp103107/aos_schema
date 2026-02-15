from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from aos_runtime.base_agent import AgentSchemas, BaseAgent

JsonDict = Dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LibrarianAgent:
    role = "Librarian"

    def run(self, request: JsonDict) -> JsonDict:
        query = request["query"]
        # NOTE: This is intentionally stub-only. Production deployments should wire this agent to MCP/web/RAG.
        return {
            "status": "SUCCESS",
            "reasoning_summary": f"Stub retrieval: no external calls made for query='{query}'.",
            "results": [],
            "notes": "Wire Librarian to MCP/web tools in your deployment layer.",
            "metrics": {"results_returned": 0}
        }


def build_runtime(schemas: AgentSchemas) -> BaseAgent:
    return BaseAgent(LibrarianAgent(), schemas)
