from __future__ import annotations

import argparse
import sys

from .logging_utils import configure_logging
from .runner import run_envelope_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aos-stdapp", description="AoS Standard Application v1 - envelope runner")
    parser.add_argument("envelope", help="Path to an AoS envelope JSON file")
    parser.add_argument("--registry", default="registry/vports.registry.v1.jsonl", help="Path to vPorts registry JSONL")
    parser.add_argument("--logs-dir", default="run_logs", help="Directory to write run logs")
    parser.add_argument("--log-level", default="INFO", help="DEBUG/INFO/WARN/ERROR")

    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    run_envelope_file(args.envelope, registry_path=args.registry, logs_dir=args.logs_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
