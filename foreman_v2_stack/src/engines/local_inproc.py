from __future__ import annotations

import json
from typing import Any, Dict

from src.interfaces.engine import BaseTaskEngine


class LocalTaskEngine(BaseTaskEngine):
    """MVP in-process task engine.

    This class is the local execution boundary and can later be swapped with
    remote engine adapters while preserving the BaseTaskEngine contract.
    """

    EXPECTED_ENVELOPE_VERSION = "aos.master.envelope.v5_1"

    def submit_task(self, envelope: Dict[str, Any]) -> str:
        envelope_version = envelope.get("envelope_version")
        if envelope_version != self.EXPECTED_ENVELOPE_VERSION:
            raise ValueError(
                "unsupported_envelope_version: "
                f"expected '{self.EXPECTED_ENVELOPE_VERSION}', got '{envelope_version}'"
            )

        print("[LocalTaskEngine] submitted envelope:")
        print(json.dumps(envelope, indent=2, sort_keys=True))

        # Placeholder task ID for MVP scaffolding.
        return "urn:aos:task:local-123"
