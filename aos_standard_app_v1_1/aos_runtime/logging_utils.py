from __future__ import annotations

import json
import logging
from typing import Any, Dict


def configure_logging(level: str = "INFO") -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def log_json(logger: logging.Logger, msg: str, payload: Dict[str, Any]) -> None:
    logger.info("%s %s", msg, json.dumps(payload, ensure_ascii=False, sort_keys=True))
