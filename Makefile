# Steady Mind — 穩心

.PHONY: help sync audit push ingest query serve site

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VENV := $(ROOT).venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "穩心 Steady Mind Commands:"
	@echo "  make ingest   - Build vector index from books/ + wiki/ + raw/"
	@echo "  make query    - Test RAG retrieval (MSG='...')"
	@echo "  make serve    - Start FastAPI backend on :8000"
	@echo "  make site     - Start backend + frontend"
	@echo "  make publish  - Deploy to CF Pages (steady-mind.pages.dev)"
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

serve: $(VENV)/bin/activate
	cd $(ROOT)/app/backend && $(PY) -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

site: $(VENV)/bin/activate
	@echo "Starting backend :8000 and frontend :5173..."
	@if [ ! -d "$(ROOT)/app/frontend/node_modules" ]; then \
	  echo "Installing frontend dependencies..."; \
	  cd "$(ROOT)/app/frontend" && npm install; \
	fi
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

.PHONY: demo-build publish demo-dev

demo-build:
	cd app/frontend && npm run build:demo

# CF Pages → https://steady-mind.pages.dev
publish: demo-build
	cd workers && npm install && npm run deploy

demo-dev: demo-build
	cd workers && npm install
	cd $(ROOT) && npx wrangler pages dev app/frontend/dist --project-name=steady-mind
