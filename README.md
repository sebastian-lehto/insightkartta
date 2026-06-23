# InsightKartta

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
- Per-municipality insight JSON generation covering:
  - party vote share changes between elections
  - StatFin indicator changes over each election period
  - indicator-vs-national comparison (above / similar / below average) using mean of municipalities as the reference
- National-level Pearson correlation between indicator changes and party vote share changes across all 292 municipalities

### API

Five endpoints:

| Endpoint | Returns |
|---|---|
| `GET /health` | Health check |
| `GET /datasets` | List of all configured datasets with metadata |
| `GET /{dataset_name}` | Processed data + metadata + GenericAnalysis results |
| `GET /regions/{region}/insights` | Per-municipality election + indicator insight JSON |
| `GET /elections/correlations` | National indicator–party vote correlation table |

### Frontend

- Dataset selector and line chart for region-over-time trends
- Year slider and choropleth map with per-dataset color bins
- `InsightsPanel`: styled card showing national trend and peak insights for the current dataset
- Region insights page (`/region/:regionCode`) with four sections:
  1. Region name and election period
  2. Socioeconomic context grid: 4 indicator cards with change + national comparison
  3. Party vote shift bar chart (vote share change in pp, green/red per bar)
  4. National correlation table: Pearson r between indicators and party vote shifts

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
│   ├── data/
│   │   ├── region_mapping.csv       ← tracked in git (reference data)
│   │   ├── party_mapping.csv        ← tracked in git (reference data)
│   │   ├── raw/                     ← NOT in git (reproduced by ingestion)
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
│   └── src/
│       ├── components/
│       │   ├── insights/
│       │   │   ├── RegionHeader.jsx
│       │   │   ├── IndicatorGrid.jsx
│       │   │   ├── IndicatorCard.jsx
│       │   │   ├── PartyChangeChart.jsx
│       │   │   └── CorrelationTable.jsx
│       │   └── ...
│       ├── utils/
│       │   └── mapScale.js
│       ├── api.js
│       └── App.jsx
│
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
make venv          # create .venv and install backend dependencies
cd frontend && npm install
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
```

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
| `backend/data/analysis/<dataset>.json` | `make analysis` | GenericAnalysis trend/average/peak for each StatFin dataset |
| `backend/data/analysis/region_insights/<code>.json` | `make region-insights` | Per-municipality insight JSON with party changes, indicator changes, and national comparisons |
| `backend/data/analysis/election_indicator_correlations.json` | `make region-insights` | Pearson r between indicator changes and party vote share changes across all municipalities |

---

## Documentation

- `ARCHITECTURE.md` — system design, data flow, and architectural decisions
- `CONTEXT.md` — project memory for future LLM/chatbot sessions; read before resuming work
- `INSTRUCTIONS.md` — explicit rules to avoid repeated mistakes; read before making changes
