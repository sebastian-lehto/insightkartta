# InsightKartta

InsightKartta is a full-stack, config-driven data analysis application for exploring Finnish regional statistics from Statistics Finland (StatFin / PXWeb).

The project is designed as a portfolio-quality software engineering project rather than a one-off notebook. It includes:

- a reusable ingestion pipeline for PXWeb datasets
- a generic transformation pipeline driven by dataset config
- an analysis layer for reusable insight generation
- a FastAPI backend that serves normalized data and metadata
- a React frontend with charts, maps, and dataset switching

The long-term goal is to support multiple datasets such as unemployment, education, and population while keeping the frontend generic and the backend extensible.

---

## Current status

Implemented so far:

- Statistics Finland ingestion pipeline
- config-driven dataset registry in `backend/pipelines/config/datasets.yaml`
- generic PXWeb table-format transformer
- generic transformation flow with:
  - standard dimensions (`region`, `year`)
  - renaming from config
  - type coercion from config
  - normalization to a unified `value` field
  - optional joins such as region mapping
- region mapping support via `backend/data/region_mapping.csv`
- analysis framework and dataset-specific analysis for unemployment
- FastAPI backend serving processed data, metadata, and analysis
- React frontend with:
  - dataset selector
  - line chart
  - time slider
  - choropleth map
  - insights panel
- metadata-driven visualization, including map bins
- YAML-anchor-based reuse in `datasets.yaml` to avoid repeating area code lists

---

## Why this project exists

This project is intended to demonstrate:

- data engineering skills
- backend architecture and API design
- frontend state management and interactive data visualization
- config-driven software design
- ability to grow a project incrementally without losing structure

The emphasis is on producing meaningful insights from public statistics, not just charts.

---

## Core design principles

- **Config-driven first**  
  New datasets should be added primarily through `backend/pipelines/config/datasets.yaml`.

- **Normalize early**  
  Different source datasets should converge to a common shape:
  - `region`
  - `region_name`
  - `year`
  - `value`

- **Keep the frontend generic**  
  The frontend should visualize normalized data and metadata, not dataset-specific column names.

- **Prefer reusable pipeline steps over per-dataset code**  
  Dataset-specific transformation modules should only exist when a dataset truly needs custom logic.

- **Metadata matters**  
  Every dataset should provide enough metadata for the frontend to render meaningful labels, units, and visualization ranges.

---

## Repository structure

This reflects the intended and current working structure.

```text
insightkartta/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── services/
│   │   │   └── dataset_service.py
│   │   ├── utils/
│   │   │   └── serialization.py
│   │   └── main.py
│   │
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   ├── analysis/
│   │   └── region_mapping.csv
│   │
│   └── pipelines/
│       ├── config/
│       │   └── datasets.yaml
│       ├── ingestion/
│       ├── transformation/
│       │   ├── transform_runner.py
│       │   └── steps/
│       └── analysis/
│           ├── engine.py
│           ├── run_analysis.py
│           └── unemployment/
│               └── analysis.py
│
├── frontend/
│   ├── public/
│   │   ├── kunnat.geojson
│   │   └── maakunnat.geojson
│   └── src/
│       ├── components/
│       ├── utils/
│       ├── api.js
│       └── App.jsx
│
├── README.md
├── ARCHITECTURE.md
├── CONTEXT.md
└── INSTRUCTIONS.md
```

---

## Config-driven dataset model

Datasets are registered in:

```text
backend/pipelines/config/datasets.yaml
```

Each dataset should define at least:

- `name`
- `source`
- `endpoint`
- `payload`
- `transformation`
- `metadata`

### Example dataset shape

```yaml
datasets:
  - name: unemployment
    source: statfi
    endpoint: tyokay/statfin_tyokay_pxt_115x.px

    payload:
      query: []
      response:
        format: json-stat2

    transformation:
      dimensions:
        region: Alue
        year: Vuosi

      rename:
        tyottomyysaste: unemployment_rate

      types:
        year: int

      value_column: unemployment_rate

      filters: []

      join:
        region_mapping: true

    metadata:
      label: "Unemployment Rate"
      unit: "%"
      visualization:
        map:
          bins: [4, 6, 8, 10, 15]
```

### YAML anchors

To avoid duplicating huge lists of StatFin area codes, shared selections should be defined once at the top of `datasets.yaml` using YAML anchors and aliases.

---

## Data flow

### 1. Ingestion
The ingestion pipeline:
- reads `datasets.yaml`
- calls the PXWeb API
- stores raw JSON responses under `backend/data/raw/<dataset>/`

### 2. Transformation
The transformation pipeline:
- loads the latest raw JSON for a dataset
- converts PXWeb table-format JSON into a DataFrame
- applies generic config-driven transformations
- optionally joins region mappings
- normalizes the chosen metric into `value`
- stores processed CSV under `backend/data/processed/<dataset>/latest.csv`

### 3. Analysis
The analysis pipeline:
- loads the latest processed dataset
- runs dataset-specific analysis classes
- stores analysis results as JSON under `backend/data/analysis/`

### 4. API
FastAPI serves:
- `/health`
- `/datasets`
- `/{dataset_name}`

Each dataset endpoint returns:
- `data`
- `meta`
- `analysis`

### 5. Frontend
The React frontend:
- loads dataset list dynamically
- fetches the selected dataset dynamically
- renders chart, map, slider, and insights using normalized data and metadata

---

## Processed data format

The current processed format is CSV.

### Why CSV is acceptable right now
- easy to inspect and debug
- easy to serve through the current backend
- fewer moving parts during active development

### Why parquet may still be introduced later
- smaller size
- faster I/O
- better typing support

Current recommendation:
- continue using CSV during active iteration
- consider parquet later if performance or file size becomes a real issue

---

## Frontend behavior

The frontend currently uses `region_name` for UI behavior and selection.

Important details:
- the chart selection is driven by `region_name`
- the map uses `region_name` because GeoJSON properties are name-based
- `region` codes may still exist in the backend and processed data, but the frontend is intentionally minimizing reliance on them

Default behavior:
- the chart should start with the whole-country selection if available
- clicking a region on the map should update the chart to that region

---

## Geographic data

The project currently works with GeoJSON files such as:
- `kunnat.geojson` for municipalities
- `maakunnat.geojson` for regions

The dataset and the chosen GeoJSON must be at the same geographic level.

This is critical:
- municipality-level data should be paired with `kunnat.geojson`
- region-level data should be paired with `maakunnat.geojson`

---

## Running the project

These are the intended commands from the project root. Adjust module names only if files are renamed.

### Backend ingestion

```bash
python -m backend.pipelines.run_ingestion
```

### Backend transformation

```bash
python -m backend.pipelines.run_transformations
```

### Backend analysis

```bash
python -m backend.pipelines.analysis.run_analysis
```

### Backend API

```bash
uvicorn backend.app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Implemented datasets

Current and planned datasets include:

- unemployment
- education: upper secondary or higher
- education: tertiary or higher
- population

The intention is to keep the frontend generic so that adding datasets mainly involves config, not frontend rewrites.

---

## Roadmap

Near-term:
- finalize additional datasets
- verify config-driven additions really work end to end
- improve map legend and color scaling per dataset
- better handling of geography level in metadata

Medium-term:
- richer analysis modules
- dataset comparison views
- stronger validation around missing metadata and transformation assumptions
- improve UI polish and interaction patterns

Long-term:
- better deployment story
- caching/versioning improvements
- optional parquet support
- more advanced geospatial analytics

---

## Documentation

Additional project documentation:

- `ARCHITECTURE.md` — technical architecture and data flow
- `CONTEXT.md` — project memory for future LLM/chatbot sessions
- `INSTRUCTIONS.md` — explicit rules to avoid repeated mistakes and delays

---

## Final note

InsightKartta is intentionally being built as a system, not a demo. The project should make it obvious that the work includes:
- architecture decisions
- config-driven extensibility
- backend and frontend integration
- data engineering discipline
- room for meaningful analysis as new datasets are added
