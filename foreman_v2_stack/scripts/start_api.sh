#!/usr/bin/env bash
set -e
UVICORN_PORT=${API_PORT:-8000}
exec uvicorn src.api.server:app --host 0.0.0.0 --port ${UVICORN_PORT}
