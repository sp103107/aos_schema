from __future__ import annotations

from typing import Any, Dict, List

from aos_runtime.base_agent import AgentSchemas, BaseAgent

JsonDict = Dict[str, Any]


class MessengerAgent:
    role = "Messenger"

    def run(self, request: JsonDict) -> JsonDict:
        targets: List[JsonDict] = request["targets"]
        channels: List[str] = request["channels"]
        primary_channel = channels[0] if channels else "log_only"

        reports = []
        for t in targets:
            reports.append({
                "target_id": t["target_id"],
                "channel": primary_channel,
                "status": "QUEUED",
                "details": "Stub messenger queued delivery (no real IO)."
            })

        return {
            "status": "SUCCESS",
            "reasoning_summary": "Stub messenger produced delivery reports.",
            "delivery_reports": reports,
            "notes": "",
            "metrics": {"targets": len(targets)}
        }


def build_runtime(schemas: AgentSchemas) -> BaseAgent:
    return BaseAgent(MessengerAgent(), schemas)
