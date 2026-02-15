from fastapi import FastAPI, WebSocket
from typing import Any, Dict

app = FastAPI(title="Agent API")


def to_mcp(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_atom": payload.get("source", "api"),
        "target_atom": payload.get("target", "default"),
        "payload": payload.get("data", {}),
        "protocol": "MCP_PACKET_VPORT",
    }


@app.post("/chat")
async def chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    packet = to_mcp(payload)
    return {"status": "ok", "packet": packet}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    await ws.send_json({"status": "connected"})
