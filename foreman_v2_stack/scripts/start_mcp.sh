#!/usr/bin/env bash
set -e
export ROUTER_BACKEND=${ROUTER_BACKEND:-bus}
exec python src/router/mcp_router.py
