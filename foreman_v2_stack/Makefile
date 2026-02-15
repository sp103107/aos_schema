
# Makefile — Standalone Agent

.PHONY: all install run docker-build docker-run lint fmt export

all: install

install:
    python -m pip install -r requirements.txt

run:
    python src/handler/minimal_handler.py

docker-build:
    docker build -t $(shell basename $(CURDIR)):latest .

docker-run:
    docker run --rm -it -p 8000:8000 $(shell basename $(CURDIR)):latest

lint:
    python -m pip install ruff
    ruff check .

fmt:
    ruff format .

export:
    @echo "Export step handled by upstream exporter."
api-run:
	uvicorn src.api.server:app --host 0.0.0.0 --port $${API_PORT:-8000}
router-run:
	python src/router/mcp_router.py
registry-build:
	@echo 'per-stack hash registry is generated automatically'
ui-run:
	@echo 'Use scripts/start_ui.sh or scripts/start_ui.bat to launch the UI'
