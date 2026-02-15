from __future__ import annotations

from typing import Any, Dict

from aos_runtime.base_agent import AgentSchemas, BaseAgent

JsonDict = Dict[str, Any]


class ForemanAgent:
    role = "Foreman"

    def run(self, request: JsonDict) -> JsonDict:
        objective = request["objective"]
        max_steps = request["constraints"].get("max_steps", 50)

        return {
            "status": "SUCCESS",
            "planning_summary": f"Planned objective: {objective}",
            "plan": {
                "steps": [
                    {
                        "step_id": "step_001",
                        "title": "Plan skeleton",
                        "description": "Generate a deterministic plan and delegations.",
                        "owner_role": "Foreman",
                        "depends_on": [],
                        "status": "done",
                        "acceptance_criteria": [
                            "Plan is schema-valid.",
                            "Steps are deterministic."
                        ],
                        "artifacts_expected": []
                    }
                ][:max_steps]
            },
            "delegations": [],
            "risks": [],
            "notes": "",
            "metrics": {"max_steps": max_steps}
        }


def build_runtime(schemas: AgentSchemas) -> BaseAgent:
    return BaseAgent(ForemanAgent(), schemas)
