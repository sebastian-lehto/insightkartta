.PHONY: help venv \
        ingest transform analysis \
        elections-ingest elections-transform region-insights \
        pipeline pipeline-all elections-pipeline \
        clean-processed clean-analysis clean-insights clean \
        reset reset-all \
        server frontend serve \
        test test-backend test-frontend test-e2e

# Use .venv if it exists, otherwise fall back to python3.exe (Windows Python via
# WSL interop — the environment where project packages are currently installed).
# Override at any time: make pipeline PYTHON=/path/to/python
ifneq ($(wildcard .venv/bin/python3),)
  PYTHON ?= .venv/bin/python3
else
  PYTHON ?= python3.exe
endif

# ─── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "InsightKartta pipeline commands"
	@echo "Run from the WSL terminal (not PowerShell). From PowerShell: wsl make <target>"
	@echo ""
	@echo "  Setup:"
	@echo "    make venv              create .venv and install backend dependencies"
	@echo ""
	@echo "  StatFin pipeline (driven by datasets.yaml):"
	@echo "    make pipeline          transform + analysis  ← standard re-run"
	@echo "    make transform         transformation only"
	@echo "    make analysis          analysis only"
	@echo "    make ingest            fetch fresh StatFin data from the API"
	@echo ""
	@echo "  Elections pipeline (custom path, scripts run in order):"
	@echo "    make elections-ingest      scrape HTML from vaalit.fi"
	@echo "    make elections-transform   parse HTML → processed CSV"
	@echo "    make region-insights       build per-municipality insight JSON"
	@echo "    make elections-pipeline    elections-transform + region-insights"
	@echo ""
	@echo "  Combined:"
	@echo "    make pipeline-all      StatFin pipeline + region-insights"
	@echo ""
	@echo "  Clean (leaves raw data and reference CSVs untouched):"
	@echo "    make clean             delete all processed CSVs + analysis JSON"
	@echo "    make clean-processed   delete processed CSVs only"
	@echo "    make clean-analysis    delete per-dataset analysis JSON only"
	@echo "    make clean-insights    delete per-municipality region insight JSON only"
	@echo ""
	@echo "  Reset (clean then re-run from existing raw data):"
	@echo "    make reset             clean + pipeline"
	@echo "    make reset-all         clean + pipeline-all"
	@echo ""
	@echo "  Dev servers:"
	@echo "    make server            start FastAPI with --reload"
	@echo "    make frontend          start Vite dev server"
	@echo "    make serve             start FastAPI for production (no --reload, binds \$$PORT)"
	@echo ""
	@echo "  Tests:"
	@echo "    make test              backend + frontend tests"
	@echo "    make test-backend      pytest (backend/tests/)"
	@echo "    make test-frontend     vitest (frontend/)"
	@echo "    make test-e2e          playwright (e2e/)"
	@echo ""
	@echo "  Python in use: $(PYTHON)"
	@echo "  Override:      make pipeline PYTHON=/path/to/python"
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────

venv:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[test]"
	@echo ""
	@echo "venv ready. Future 'make' calls will use .venv/bin/python3 automatically."
	@echo "To activate in your shell: source .venv/bin/activate"

# ─── StatFin pipeline ─────────────────────────────────────────────────────────

ingest:
	$(PYTHON) -m backend.pipelines.run_ingestion

transform:
	$(PYTHON) -m backend.pipelines.run_transformation

analysis:
	$(PYTHON) -m backend.pipelines.run_analysis

pipeline: transform analysis

# ─── Elections pipeline ───────────────────────────────────────────────────────

elections-ingest:
	$(PYTHON) -m backend.pipelines.ingestion.fetch_municipal_elections

elections-transform:
	$(PYTHON) -m backend.pipelines.transformation.elections.normalize_party_votes

region-insights:
	$(PYTHON) -m backend.pipelines.analysis.generate_region_insights

elections-pipeline: elections-transform region-insights

# ─── Combined ─────────────────────────────────────────────────────────────────

pipeline-all: transform elections-transform analysis region-insights

# ─── Clean ────────────────────────────────────────────────────────────────────

clean-processed:
	@echo "→ Deleting processed CSVs..."
	@rm -rf backend/data/processed/
	@echo "  done."

clean-analysis:
	@echo "→ Deleting per-dataset analysis JSON..."
	@find backend/data/analysis -maxdepth 1 -name "*.json" -delete 2>/dev/null || true
	@echo "  done."

clean-insights:
	@echo "→ Deleting region insight JSON..."
	@rm -rf backend/data/analysis/region_insights/
	@echo "  done."

clean: clean-processed clean-analysis clean-insights

# ─── Reset ────────────────────────────────────────────────────────────────────

reset: clean pipeline

reset-all: clean pipeline-all

# ─── Dev servers ──────────────────────────────────────────────────────────────

server:
	$(PYTHON) -m uvicorn backend.app.main:app --reload

frontend:
	cd frontend && npm run dev

# Production server (used by the Dockerfile): no --reload, binds the port the
# host platform assigns via $PORT (e.g. Render), falling back to 8000 locally.
serve:
	$(PYTHON) -m uvicorn backend.app.main:app --host 0.0.0.0 --port $${PORT:-8000}

# ─── Tests ────────────────────────────────────────────────────────────────────

test-backend:
	$(PYTHON) -m pytest backend/tests/

test-frontend:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

test: test-backend test-frontend
