@echo off
if not defined ROUTER_BACKEND set ROUTER_BACKEND=bus
python src/router/mcp_router.py
