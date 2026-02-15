from pathlib import Path
from typing import Optional


def resolve(uri: str, mounts_file: Optional[Path] = None) -> Path:
    if uri.startswith("file://"):
        return Path(uri[7:]).resolve()
    # Minimal placeholder; extend with aos:// and hub://
    return Path(uri).resolve()
