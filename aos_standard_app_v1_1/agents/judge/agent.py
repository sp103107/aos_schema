from __future__ import annotations

from typing import Any, Dict

from aos_runtime.base_agent import AgentSchemas, BaseAgent

JsonDict = Dict[str, Any]


class JudgeAgent:
    role = "Judge"

    def run(self, request: JsonDict) -> JsonDict:
        evaluation_type = request["evaluation_type"]
        subject = request["subject"]

        return {
            "status": "SUCCESS",
            "verdict": "APPROVED",
            "reasoning_summary": f"Stub judge approved subject='{subject}' with evaluation_type='{evaluation_type}'.",
            "issues": [],
            "citations": [],
            "notes": "",
            "metrics": {"issues": 0}
        }


def build_runtime(schemas: AgentSchemas) -> BaseAgent:
    return BaseAgent(JudgeAgent(), schemas)
