#!/usr/bin/env python3
from typing import Any, Dict


class Router:
    def __init__(self, backend: str = "bus") -> None:
        self.backend = backend

    def route(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "backend": self.backend, "packet_echo": bool(packet)}


if __name__ == "__main__":
    print("Router stub ready (use env ROUTER_BACKEND=bus|nats|redis)")
