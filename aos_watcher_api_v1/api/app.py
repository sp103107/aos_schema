"""
AoS API v1 (optional)
- Accepts envelope or bundle JSON
- Saves it into inbox/ so the watcher executes it
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, UploadFile, Body, HTTPException
from fastapi.responses import JSONResponse, FileResponse

APP_ROOT = Path(os.environ.get("AOS_WATCHER_ROOT", ".")).resolve()
INBOX = APP_ROOT / "inbox"
OUTBOX = APP_ROOT / "outbox"
DONE = APP_ROOT / "done"
FAILED = APP_ROOT / "failed"
LOGS = APP_ROOT / "logs"

for p in [INBOX, OUTBOX, DONE, FAILED, LOGS]:
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AoS Envelope API", version="1.0.0")


def _safe_id(s: str) -> str:
    return "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in s)[:120] or "item"


def _derive_id(obj: Any) -> str:
    if isinstance(obj, dict):
        env = obj.get("envelope", obj)
        if isinstance(env, dict):
            tid = env.get("id") or env.get("task_id")
            if tid:
                return _safe_id(str(tid))
    return _safe_id(str(uuid.uuid4()))


def _status_for(file_id: str) -> Dict[str, Any]:
    # Extremely simple status lookup based on presence in folders
    inbox = list(INBOX.glob(f"*{file_id}*.json"))
    processing = list((APP_ROOT / "processing").glob(f"*{file_id}*.json")) if (APP_ROOT / "processing").exists() else []
    done = list(DONE.glob(f"*{file_id}*.json"))
    failed = list(FAILED.glob(f"*{file_id}*.json"))

    state = "unknown"
    if inbox:
        state = "queued"
    if processing:
        state = "processing"
    if done:
        state = "done"
    if failed:
        state = "failed"

    # Find most recent output
    outputs = sorted(OUTBOX.glob(f"*{file_id}*.out.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    logs = sorted(LOGS.glob(f"*{file_id}*.log.txt"), key=lambda p: p.stat().st_mtime, reverse=True)

    return {
        "id": file_id,
        "state": state,
        "inbox_files": [p.name for p in inbox],
        "done_files": [p.name for p in done],
        "failed_files": [p.name for p in failed],
        "latest_output": outputs[0].name if outputs else None,
        "latest_log": logs[0].name if logs else None,
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/submit")
async def submit_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    raw = await file.read()
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON")

    file_id = _derive_id(obj)
    dest = INBOX / f"aos_{file_id}_{uuid.uuid4().hex[:8]}.json"
    dest.write_bytes(raw)
    return JSONResponse({"accepted": True, "id": file_id, "filename": dest.name})


@app.post("/submit_json")
def submit_json(payload: Dict[str, Any] = Body(...)):
    file_id = _derive_id(payload)
    dest = INBOX / f"aos_{file_id}_{uuid.uuid4().hex[:8]}.json"
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return JSONResponse({"accepted": True, "id": file_id, "filename": dest.name})


@app.get("/status/{file_id}")
def status(file_id: str):
    return JSONResponse(_status_for(_safe_id(file_id)))


@app.get("/result/{file_id}")
def result(file_id: str):
    file_id = _safe_id(file_id)
    outputs = sorted(OUTBOX.glob(f"*{file_id}*.out.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not outputs:
        raise HTTPException(status_code=404, detail="No output found yet")
    return FileResponse(str(outputs[0]), media_type="application/json", filename=outputs[0].name)


@app.get("/log/{file_id}")
def log(file_id: str):
    file_id = _safe_id(file_id)
    logs = sorted(LOGS.glob(f"*{file_id}*.log.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not logs:
        raise HTTPException(status_code=404, detail="No log found yet")
    return FileResponse(str(logs[0]), media_type="text/plain", filename=logs[0].name)
