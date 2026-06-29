# Steady Mind — 穩心

.PHONY: help sync audit push ingest query serve dev mlx-check mlx-download mlx-path embed-download clean-models

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VENV := $(ROOT).venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "穩心 Steady Mind Commands:"
	@echo "  make ingest   - Build vector index from books/ + wiki/ + raw/"
	@echo "  make query    - Test RAG retrieval (MSG='...')"
	@echo "  make serve    - Start FastAPI backend on :8000"
	@echo "  make dev      - Start backend + frontend"
	@echo "  make mlx-check - Verify MLX model loads locally"
	@echo "  make embed-download - Download embedding model to data/models/embeddings/"
	@echo "  make clean-models  - Prune unused model files (add HF_CACHE=1 for ~/.cache)"
	@echo ""
	@echo "Research Commands:"
	@echo "  make sync     - Compile wiki/ from raw/"
	@echo "  make audit    - Wiki lint/audit"
	@echo "  make push     - Commit and push"

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -r app/backend/requirements-dev.txt

ingest: $(VENV)/bin/activate
	cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/ingest.py

query: $(VENV)/bin/activate
	cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/query.py --msg "$(MSG)"

mlx-check: $(VENV)/bin/activate
	cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/mlx_check.py

mlx-download: $(VENV)/bin/activate
	cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/download_mlx_model.py

mlx-path: $(VENV)/bin/activate
	cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) -c "from config import resolve_mlx_model_path; print(resolve_mlx_model_path())"

embed-download: $(VENV)/bin/activate
	cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/download_embed_model.py --force

serve: $(VENV)/bin/activate
	cd $(ROOT)/app/backend && $(PY) -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

dev: $(VENV)/bin/activate
	@echo "Starting backend :8000 and frontend :5173..."
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 1
	@trap 'kill 0' EXIT; \
	cd $(ROOT)/app/backend && $(PY) -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 & \
	BACKEND_PID=$$!; \
	for i in 1 2 3 4 5 6 7 8 9 10; do \
	  curl -sf http://127.0.0.1:8000/api/health >/dev/null && break; \
	  sleep 1; \
	done; \
	if ! curl -sf http://127.0.0.1:8000/api/health >/dev/null; then \
	  echo "ERROR: backend failed to start on :8000. Run: make serve"; \
	  kill $$BACKEND_PID 2>/dev/null || true; \
	  exit 1; \
	fi; \
	echo "Backend ready."; \
	cd $(ROOT)/app/frontend && npm run dev & \
	wait

sync:
	@echo "update wiki/ based on raw/ and AGENTS.md"

audit:
	@echo "Review the entire wiki/ directory. Complete the audit defined in AGENTS.md."

push:
	git add .
	git commit -m "research update: $$(date +'%Y-%m-%d')"
	git push
