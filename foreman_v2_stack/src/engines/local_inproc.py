from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.interfaces.engine import BaseTaskEngine


class LocalTaskEngine(BaseTaskEngine):
    """MVP in-process task engine.

    This class is the local execution boundary and can later be swapped with
    remote engine adapters while preserving the BaseTaskEngine contract.
    """

    EXPECTED_ENVELOPE_VERSION = "aos.master.envelope.v5_1"

    def _iso_now(self) -> str:
        return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _build_planning_artifact(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id", "urn:aos:task:unknown")
        return {
            "artifact_id": f"urn:aos:artifact:{task_id.split(':')[-1]}.plan.md",
            "artifact_type": "doc_md",
            "title": "Task Plan",
            "content": (
                f"# Task Plan\n\n"
                f"- Task ID: `{task_id}`\n"
                f"- Description: {task.get('description', 'n/a')}\n"
                f"- Next Step: execute downstream generation/validation tasks.\n"
            ),
            "produced_by_task_id": task_id,
        }

    def _build_generation_artifact(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id", "urn:aos:task:unknown")
        title = task.get("description", "Generated Document")
        return {
            "artifact_id": f"urn:aos:artifact:{task_id.split(':')[-1]}.generated.md",
            "artifact_type": "doc_md",
            "title": title,
            "content": (
                f"# {title}\n\n"
                "This is an MVP generated markdown artifact from the in-process "
                "Foreman task runner.\n"
            ),
            "produced_by_task_id": task_id,
        }

    def _run_tasks(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        embedded_meta = envelope.get("embedded_master_meta")
        if not isinstance(embedded_meta, dict):
            raise ValueError("embedded_master_meta must be an object")

        tasks_obj = embedded_meta.get("tasks")
        if not isinstance(tasks_obj, dict):
            raise ValueError("embedded_master_meta.tasks must be an object")

        tasks = tasks_obj.get("tasks")
        if not isinstance(tasks, list):
            raise ValueError("embedded_master_meta.tasks.tasks must be a list")

        artifacts: List[Dict[str, Any]] = []
        unsupported: List[Dict[str, Any]] = []

        for task in tasks:
            if not isinstance(task, dict):
                continue
            task_type = task.get("task_type")
            if task_type == "planning":
                artifacts.append(self._build_planning_artifact(task))
            elif task_type in {"generation", "presentation"}:
                artifacts.append(self._build_generation_artifact(task))
            else:
                unsupported.append(
                    {
                        "task_id": task.get("task_id"),
                        "task_type": task_type,
                        "reason": "unsupported_task_type",
                    }
                )

        status = "completed" if not unsupported else "completed_with_warnings"
        return {
            "status": status,
            "artifacts": artifacts,
            "unsupported_tasks": unsupported,
        }

    def submit_task(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        envelope_version = envelope.get("envelope_version")
        if envelope_version != self.EXPECTED_ENVELOPE_VERSION:
            raise ValueError(
                "unsupported_envelope_version: "
                f"expected '{self.EXPECTED_ENVELOPE_VERSION}', got '{envelope_version}'"
            )

        print("[LocalTaskEngine] submitted envelope:")
        print(json.dumps(envelope, indent=2, sort_keys=True))

        result = self._run_tasks(envelope)

        result_envelope: Dict[str, Any] = {
            "envelope_version": self.EXPECTED_ENVELOPE_VERSION,
            "envelope_kind": "task_result",
            "request_id": envelope.get("request_id", "urn:aos:req:local-inproc"),
            "created_at": self._iso_now(),
            "invocation_type": envelope.get("invocation_type", "api_call"),
            "platform_capabilities": envelope.get("platform_capabilities", {}),
            "execution_hint": envelope.get("execution_hint", {"trust_level": "medium"}),
            "embedded_master_meta": envelope.get("embedded_master_meta", {}),
            "result": result,
        }

        if "temporal" in envelope:
            result_envelope["temporal"] = envelope["temporal"]

        return result_envelope
