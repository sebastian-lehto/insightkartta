# InsightKartta

**Live**: [insightkartta.vercel.app](https://insightkartta.vercel.app) (frontend on Vercel; backend on Render — see [Deployment](#deployment))

InsightKartta is a full-stack, config-driven data analysis application for exploring Finnish regional statistics from Statistics Finland (StatFin / PXWeb) alongside municipal election data.

The project is designed as a portfolio-quality software engineering project. It includes:

- a reusable ingestion pipeline for PXWeb datasets
- a generic transformation pipeline driven by dataset config
- a generic analysis layer (`GenericAnalysis`) that runs automatically for all configured datasets
- a parallel elections pipeline for HTML-scraped party vote data
- election–indicator relationship analysis with per-region and national-level outputs
- a FastAPI backend serving normalized data, metadata, analysis, and insights
- a React frontend with charts, choropleth maps, dataset switching, and a dedicated region insights page

---

## Current status

### StatFin pipeline (config-driven)

Implemented and operational:

- config-driven dataset registry in `backend/pipelines/config/datasets.yaml`
- generic PXWeb ingestion (dimensions, rename, type coercion, value normalization, region mapping join)
- `GenericAnalysis` runs automatically for every dataset: trend, average, and peak year on the national aggregate
- YAML-anchor-based area code reuse to avoid repeating large selection lists
- Makefile for pipeline orchestration (`make pipeline`, `make reset`, `make reset-all`)

Active datasets:

| Dataset | Description |
|---|---|
| `unemployment` | Municipal unemployment rate (%) |
| `education_upper_secondary` | Share with upper secondary education (%) |
| `education_tertiary` | Share with tertiary education (%) |
| `population` | Municipal population (persons) |

### Elections pipeline (custom)

Implemented and operational:

- HTML scraper for vaalit.fi election results (2012, 2017, 2021, 2025)
- Party-level vote share normalization to processed CSV
- Per-municipality insight JSON generation, covering **every consecutive election period** (2012→2017, 2017→2021, 2021→2025), each with:
  - party vote share changes between that period's two elections
  - StatFin indicator changes over that election period
  - indicator-vs-national comparison (above / similar / below average) using mean of municipalities as the reference
- National-level Pearson correlation between indicator changes and party vote share changes across all 292 municipalities, for every period

### API

Five endpoints:

| Endpoint | Returns |
|---|---|
| `GET /health` | Health check |
| `GET /datasets` | List of all configured datasets with metadata |
| `GET /{dataset_name}` | Processed data + metadata + GenericAnalysis results |
| `GET /regions/{region}/insights` | Per-municipality insight JSON covering all available election periods |
| `GET /elections/correlations` | National indicator–party vote correlation table, keyed by period |

### Frontend

- Dataset selector and line chart for region-over-time trends
- Year slider and choropleth map with per-dataset color bins
- Region search with two distinct actions per result: a pin icon selects the region on the dashboard map/chart, while the rest of the row opens its full insights page
- `InsightsPanel`: styled card computed **client-side** from whichever region/dataset is currently selected (trend, peak, trough, and a national comparison) — so it always matches the chart next to it, instead of always showing the national figures
- Region insights page (`/region/:regionCode`) with four sections:
  1. Region name and an election-period switcher (2012→2017, 2017→2021, 2021→2025), with the active period clearly emphasized
  2. Socioeconomic context grid: 4 indicator cards with change + national comparison, for the selected period
  3. Party vote shift bar chart (vote share change in pp, green/red per bar), for the selected period
  4. National correlation table: Pearson r between indicators and party vote shifts, for the selected period

---

## Core design principles

- **Config-driven first**: new StatFin datasets are added through `datasets.yaml`, not new code
- **Normalize early**: all processed data converges to `year`, `value`, `region_code`, `region_name`
- **Keep the frontend generic**: the frontend visualizes metadata and normalized data, not dataset-specific column names
- **Elections are an explicit exception**: the elections pipeline uses custom scraping and cannot follow the config-driven pattern; it is not a model to replicate for new StatFin datasets
- **Metadata matters**: every dataset requires `label`, `unit`, and `visualization.map.bins` (exactly 5 values)

---

## Repository structure

```text
insightkartta/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── services/
│   │   │   ├── dataset_service.py
│   │   │   └── insight_service.py
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── conftest.py              ← swaps data paths to fixtures/, clears load_config cache
│   │   ├── fixtures/                ← tiny hand-built datasets.yaml + processed/analysis JSON
│   │   ├── test_election_change_calculator.py
│   │   ├── test_relationship_calculator.py
│   │   ├── test_generate_region_insights.py
│   │   └── test_api.py
│   │
│   ├── data/
│   │   ├── region_mapping.csv       ← tracked in git (reference data)
│   │   ├── party_mapping.csv        ← tracked in git (reference data)
│   │   ├── raw/                     ← tracked in git (lets the Docker build run without network access — see Deployment)
│   │   ├── processed/               ← NOT in git (reproduced by transformation)
│   │   └── analysis/                ← NOT in git (reproduced by analysis scripts)
│   │
│   ├── pipelines/
│   │   ├── config/
│   │   │   └── datasets.yaml
│   │   ├── ingestion/
│   │   ├── transformation/
│   │   │   ├── transform_runner.py
│   │   │   ├── steps/
│   │   │   └── elections/
│   │   │       └── normalize_party_votes.py
│   │   └── analysis/
│   │       ├── generic.py           ← GenericAnalysis (runs for all StatFin datasets)
│   │       ├── generate_region_insights.py
│   │       ├── run_analysis.py
│   │       └── run_transformation.py
│   │
│   └── services/
│       ├── election_change_calculator.py
│       ├── indicator_change_calculator.py
│       └── relationship_calculator.py   ← baselines, per-region relationships, national correlations
│
├── frontend/
│   ├── public/
│   │   ├── kunnat.geojson
│   │   └── maakunnat.geojson
│   ├── vercel.json                  ← SPA rewrite (BrowserRouter routes need this on Vercel)
│   ├── .env.example                 ← documents VITE_API_BASE_URL
│   └── src/
│       ├── components/
│       │   ├── InsightsPanel.jsx    ← computed client-side, see utils/insights.js
│       │   ├── RegionSearch.jsx     ← pin = select on map, row = navigate to region page
│       │   ├── MapView.jsx
│       │   ├── insights/
│       │   │   ├── RegionHeader.jsx     ← now an election-period switcher
│       │   │   ├── IndicatorGrid.jsx
│       │   │   ├── IndicatorCard.jsx
│       │   │   ├── PartyChangeChart.jsx
│       │   │   └── CorrelationTable.jsx
│       │   └── ...
│       ├── hooks/
│       │   └── useKunnatGeoJson.js  ← shared kunnat.geojson fetch (RegionSearch + MapView)
│       ├── utils/
│       │   ├── mapScale.js
│       │   └── insights.js          ← main-dashboard insight computation
│       ├── test/
│       │   └── setup.js             ← jest-dom matchers, RTL cleanup, React global
│       ├── api.js                   ← baseURL from VITE_API_BASE_URL
│       └── App.jsx
│
├── frontend/e2e/                    ← Playwright specs (run against the real dev servers)
├── frontend/playwright.config.js    ← workers: 1 (suite shares one dev server, see Testing)
│
├── Dockerfile                       ← backend deploy image (Render), see Deployment
├── .dockerignore
├── backend/.env.example             ← documents ALLOWED_ORIGINS
├── Makefile
├── README.md
├── ARCHITECTURE.md
├── CONTEXT.md
└── INSTRUCTIONS.md
```

---

## Running the project

Run all commands from the WSL terminal. From PowerShell use `wsl make <target>`.

### Setup (first time)

```bash
make venv          # create .venv, install backend deps + test deps from pyproject.toml
cd frontend && npm install
npx playwright install   # one-time e2e browser download (frontend/)
```

### StatFin pipeline

```bash
make pipeline      # transform + analysis (standard re-run from existing raw data)
make ingest        # fetch fresh data from the StatFin API
```

### Elections pipeline

```bash
make elections-ingest      # scrape HTML from vaalit.fi
make elections-transform   # parse HTML → processed CSV
make region-insights       # build per-municipality JSONs + national correlations
```

### Full reset (clean everything and re-run from raw data)

```bash
make reset-all     # clean + transform + elections-transform + analysis + region-insights
```

### Dev servers

```bash
make server        # FastAPI with --reload on http://127.0.0.1:8000
make frontend      # Vite dev server (from frontend/)
make serve         # production server: no --reload, binds $PORT (used by the Dockerfile)
```

---

## Testing

| Layer | Stack | What it covers |
|---|---|---|
| Backend unit/integration | pytest + httpx (`backend/tests/`) | Pure calculator logic (`relationship_calculator.py`, `election_change_calculator.py`), period derivation, and `/datasets`, `/{dataset_name}`, `/regions/{region}/insights`, `/elections/correlations` contracts via FastAPI's `TestClient` against a fixture data tree — never the real `backend/data/`. |
| Frontend unit/component | Vitest + Testing Library (`frontend/src/**/*.test.{js,jsx}`) | Pure functions (`utils/insights.js`, `utils/mapScale.js`, extracted chart helpers) and `RegionSearch`'s pin-vs-row click split. |
| End-to-end | Playwright (`frontend/e2e/`) | Golden-path flows against the real dev servers and real data: the search pin/row split, a region's map popup opening and closing on dataset switch, and the region page's period switcher updating every section together. |

```bash
make test-backend      # pytest
make test-frontend     # vitest
make test-e2e          # playwright (boots both dev servers itself)
make test              # backend + frontend
```

Backend tests run against `backend/tests/fixtures/` (a small hand-built `datasets.yaml` + processed/analysis JSON), swapped in via `conftest.py` monkeypatching the services' path constants — real `backend/data/` is never touched or required. E2E tests run against whatever is actually in `backend/data/` at the time, since they're exercising the real app end to end. `playwright.config.js` deliberately runs with `workers: 1` — the whole suite shares one dev-server pair, and concurrent test pages against it caused real intermittent failures, not just slower ones.

---

## Config-driven dataset model

Each StatFin dataset entry in `datasets.yaml` must include:

```yaml
- name: some_dataset
  source: statfi
  endpoint: some/path.px
  payload:
    query: []
    response:
      format: json-stat2
  transformation:
    dimensions:
      region: Alue
      year: Vuosi
    rename:
      source_column: cleaned_name
    types:
      year: int
    value_column: cleaned_name
    filters: []
    join:
      region_mapping: true
  metadata:
    label: "Human-readable label"
    unit: "%"
    visualization:
      map:
        bins: [10, 20, 30, 40, 50]   # exactly 5 values required
```

Adding a dataset to this file automatically gives it ingestion, transformation, `GenericAnalysis`, API exposure, and inclusion as an indicator in the election relationship analysis.

---

## Analysis outputs

| File | Produced by | Description |
|---|---|---|
| `backend/data/analysis/<dataset>.json` | `make analysis` | GenericAnalysis trend/average/peak for each StatFin dataset (national only; served via the API but no longer read by the dashboard frontend, which computes its own region-aware insights client-side) |
| `backend/data/analysis/region_insights/<code>.json` | `make region-insights` | Per-municipality insight JSON — a `periods` array (most recent first), one entry per consecutive election period, each with party changes, indicator changes, and national comparisons |
| `backend/data/analysis/election_indicator_correlations.json` | `make region-insights` | Pearson r between indicator changes and party vote share changes across all municipalities, keyed by each period's end year |

---

## Deployment

Split deployment: **Vercel** (frontend, static) + **Render** (backend, Docker), each connected via native GitHub git integration — push to `main` auto-deploys both, every PR gets a Vercel preview. CI (`ci.yml`) is the correctness gate in front of this, enforced via branch protection on `main`.

**Frontend (Vercel)**: root directory `frontend`, env var `VITE_API_BASE_URL` pointing at the Render backend. `frontend/vercel.json` rewrites all paths to `index.html`, which client-side-routed apps (`BrowserRouter`) need on static hosting — without it, a direct navigation to `/region/:regionCode` 404s.

**Backend (Render)**: Docker-based web service built from the root-level `Dockerfile`, env var `ALLOWED_ORIGINS` pointing at the Vercel frontend. The build runs `make pipeline-all` against the already-committed `backend/data/raw/` (see the repository structure note above) — no network access to StatFin or vaalit.fi needed at build time — then starts the API with `make serve` (binds `$PORT`, no `--reload`). Render's free tier sleeps on inactivity, so the first request after a while can take up to ~60s; the dashboard shows an explicit loading state for this rather than rendering empty panels.

To deploy your own copy: fork the repo, import it on [vercel.com](https://vercel.com) (root directory `frontend`) and create a Docker web service on [render.com](https://render.com) (root directory left blank — the `Dockerfile` is at the repo root), then set the two env vars above to point at each other's deployed URL.

---

## Documentation

- `ARCHITECTURE.md` — system design, data flow, and architectural decisions
- `CONTEXT.md` — project memory for future LLM/chatbot sessions; read before resuming work
- `INSTRUCTIONS.md` — explicit rules to avoid repeated mistakes; read before making changes
