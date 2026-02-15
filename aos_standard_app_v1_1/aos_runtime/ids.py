from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def sha256_json(obj: Dict[str, Any]) -> str:
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
