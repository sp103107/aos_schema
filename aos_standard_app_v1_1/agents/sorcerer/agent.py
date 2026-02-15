from __future__ import annotations

from typing import Any, Dict

from aos_runtime.base_agent import AgentSchemas, BaseAgent

JsonDict = Dict[str, Any]


class SorcererAgent:
    role = "Sorcerer"

    def run(self, request: JsonDict) -> JsonDict:
        objective = request["objective"]
        intent = request["intent"]

        return {
            "status": "SUCCESS",
            "generation_summary": f"Stub generation for intent={intent}: {objective}",
            "artifacts": [
                {
                    "artifact_id": "artifact_001",
                    "type": "text",
                    "content": f"[Stub artifact]\n{objective}",
                    "metadata": {"intent": intent}
                }
            ],
            "notes": "",
            "metrics": {"artifacts": 1}
        }


def build_runtime(schemas: AgentSchemas) -> BaseAgent:
    return BaseAgent(SorcererAgent(), schemas)
