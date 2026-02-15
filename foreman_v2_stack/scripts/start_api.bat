@echo off
set PORT=%API_PORT%
if not defined PORT set PORT=8000
uvicorn src.api.server:app --host 0.0.0.0 --port %PORT%
