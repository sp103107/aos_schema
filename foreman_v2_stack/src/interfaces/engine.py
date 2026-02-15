from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTaskEngine(ABC):
    """Contract for task-execution backends used by Foreman API.

    Implementations can run in-process (local MVP) or remote (Redis/NATS workers)
    as long as they expose the same submit interface.
    """

    @abstractmethod
    def submit_task(self, envelope: Dict[str, Any]) -> str:
        """Submit an AoS envelope for execution.

        Returns:
            task_id: canonical AoS task identifier.
        """
        raise NotImplementedError
