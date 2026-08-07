
.PHONY: help sync audit push ingest query serve site books-export pdf-export

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VENV := $(ROOT)researchenv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Commands:"
	@echo "  make ingest   - Build vector index from books/ + wiki/ + notes/"
	@echo "  make query    - Test RAG retrieval (MSG='...')"
	@echo "  make serve    - Start FastAPI backend on :8000"
	@echo "  make site     - Start backend + frontend"
	@echo "  make publish  - Deploy to CF Pages (steady-mind.pages.dev)"
	@echo ""
	@echo "Research Commands:"
	@echo "  make markitdown BOOK='Think and Grow Rich' - Make markdown from a book file"
	@echo "  make books-export [BOOK='title|id'] - Export Apple Books highlights → notes/"
	@echo "  make books-export LIST=1           - List books (count, id prefix, title)"
	@echo "  make pdf-export [BOOK='title']     - Export PDF-file highlights → notes/"
	@echo "  make pdf-export LIST=1             - List PDFs with embedded highlight counts"
	@echo "  make sync: Compile notes/2026-07-31-the-power-of-charm.md per AGENTS.md"
	@echo "  make sync NOTE='…' THEMES='a' "
	@echo "  make audit                   - Print Audit prompt for wiki/"
	@echo "  make push     - Commit and push"

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -r app/backend/requirements-dev.txt

markitdown: $(VENV)/bin/activate
	cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/markitdown.py "$(BOOK)"

# Export Apple Books highlights to notes/YYYY-MM-DD-book-slug.md
# Usage: make books-export
#        make books-export BOOK='Psychology of Money'
#        make books-export BOOK=E5527B46
#        make books-export LIST=1
books-export: $(VENV)/bin/activate
	@if [ "$(LIST)" = "1" ]; then \
	  cd $(ROOT) && $(PY) scripts/books_export.py --list "$(BOOK)"; \
	else \
	  cd $(ROOT) && $(PY) scripts/books_export.py "$(BOOK)"; \
	fi

# Export highlight annotations embedded in books/*.pdf → notes/
# Usage: make pdf-export
#        make pdf-export BOOK='Seduction Bible'
#        make pdf-export LIST=1
pdf-export: $(VENV)/bin/activate
	@$(PIP) show pymupdf >/dev/null 2>&1 || $(PIP) install 'pymupdf>=1.24.0'
	@if [ "$(LIST)" = "1" ]; then \
	  cd $(ROOT) && $(PY) scripts/pdf_export.py --list "$(BOOK)"; \
	else \
	  cd $(ROOT) && $(PY) scripts/pdf_export.py "$(BOOK)"; \
	fi

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

# Optional local draft helper (agent owns compile — see AGENTS.md § Compile).
# Prefer: agent writes wiki/. Optional: one theme at a time → outputs/sync-draft/ → agent merges.
# Usage: make sync NOTE='notes/….md' THEMES='listening' DRY=1
#        make sync NOTE='notes/….md' THEMES='listening'          # write wiki/ (still prefer agent merge)
sync: $(VENV)/bin/activate
	@if [ -z "$(NOTE)" ]; then \
	  echo "Compile is agent-first (AGENTS.md). Optional local draft:"; \
	  echo "  make sync NOTE='notes/your-note.md' THEMES='one-theme' DRY=1"; \
	  echo "Then ask the agent to merge outputs/sync-draft/ into wiki/ + INDEX."; \
	  echo "Gateway: LLM_URL + LLM_MODEL from .env.development"; \
	  exit 1; \
	fi
	@if [ "$(DRY)" = "1" ]; then \
	  cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/sync_wiki.py "$(NOTE)" --themes "$(THEMES)" --dry; \
	else \
	  cd $(ROOT) && PYTHONPATH=app/backend:scripts $(PY) scripts/sync_wiki.py "$(NOTE)" --themes "$(THEMES)"; \
	fi

audit:
	@echo "=== Copy below into Cursor (Agent) and run ==="
	@echo ""
	@echo "Audit wiki/ per AGENTS.md."
	@echo "- Find orphans, missing [[pages]], contradictions, stale claims."
	@echo "- Fix when confident; otherwise flag."
	@echo "- Do not modify notes/."
	@echo "- Report what you fixed vs left open."

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
