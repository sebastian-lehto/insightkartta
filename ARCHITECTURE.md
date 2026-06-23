# InsightKartta Architecture

This document explains the current intended architecture of InsightKartta, why certain design decisions were made, and how data flows through the system.

---

## 1. Architecture overview

InsightKartta is a layered, config-driven system.

```text
Statistics Finland PXWeb API          vaalit.fi HTML
          ↓                                  ↓
     Ingestion layer               Custom elections fetcher
          ↓                                  ↓
        Raw JSON                     Raw HTML + manifests
          ↓                                  ↓
   Transformation layer            Custom elections parser
          ↓                                  ↓
   Normalized processed CSV        Elections processed CSV
          ↓                                  ↓
     Analysis layer               generate_region_insights.py
          ↓                                  ↓
   Analysis JSON results          Per-region insight JSON
          ↓                                  ↓
                        FastAPI API
                             ↓
                       React frontend
```

The important architectural choice is that new StatFin datasets should be added mostly through configuration, not through repeated custom code. The elections pipeline is an explicit exception — HTML scraping requires a custom path — but even it feeds into the same processed CSV format and data directory conventions.

---

## 2. Main architectural goals

The architecture is designed to optimize for:

- extensibility
- clarity
- debuggability
- separation of concerns
- frontend genericity
- portfolio quality

---

## 3. Backend layers

## 3.1 Ingestion

Purpose:
- fetch raw datasets from StatFin PXWeb
- store immutable raw responses for reproducibility

Key characteristics:
- reads from `backend/pipelines/config/datasets.yaml`
- loops over all configured datasets
- uses source-specific client implementations
- stores raw responses under `backend/data/raw/<dataset>/`
- keeps timestamped history of raw files

Typical flow:
1. load dataset registry from config
2. fetch dataset using configured endpoint and payload
3. store wrapped raw JSON

Design note:
The ingestion layer should not know how the dataset will later be visualized.

Elections exception:
The elections dataset uses a separate custom fetcher (`fetch_municipal_elections.py`) that scrapes HTML from `tulospalvelu.vaalit.fi`. It is not called by `run_ingestion.py`. This is intentional — the scraping protocol is too different from PXWeb to share infrastructure.

---

## 3.2 Transformation

Purpose:
- convert raw PXWeb responses into normalized tabular data

Current direction:
- use a generic transformer for PXWeb table-format data
- use config to describe:
  - dimensions
  - renames
  - types
  - `value_column`
  - filters
  - joins

Expected generic responsibilities:
- map raw columns such as `Alue` and `Vuosi` into internal names
- rename configured source fields
- coerce types (for example `year -> int`)
- normalize the selected metric into a standard `value` column
- apply configured filters
- apply joins such as region mapping

All processed output — both StatFin and elections — uses the same column set: `year`, `value`, `region_code`, `region_name`. The `region_code` name is canonical across all datasets.

Dataset-specific transformation modules:
- should exist only when a dataset truly requires custom logic
- should not be the default path

Elections exception:
The elections dataset uses a fully custom transformation script (`normalize_party_votes.py`) because the input is scraped HTML with party-level rows rather than a PXWeb table. It produces a processed CSV in the same directory convention (`backend/data/processed/municipal_elections_party_votes/latest.csv`) but with additional columns specific to party data.

---

## 3.3 Analysis

Purpose:
- generate reusable insights from processed datasets

Structure:
- `GenericAnalysis` in `backend/pipelines/analysis/generic.py`: runs for every StatFin dataset. Filters to the national aggregate row (`region_code == "SSS"`), then computes trend, average, and peak year on the `value` column. Uses the dataset's `metadata.label` for human-readable insight text.
- Dataset-specific analysis modules: only needed when a dataset genuinely requires logic that `GenericAnalysis` cannot provide.
- `generate_region_insights.py`: an elections-specific script that produces two outputs:
  1. Per-municipality JSON files at `backend/data/analysis/region_insights/<region_code>.json` — each containing party change data, raw indicator changes (`indicators`), and indicator-vs-national context (`indicator_relationships`).
  2. A national-level cross-municipality correlation file at `backend/data/analysis/election_indicator_correlations.json` — Pearson correlation between each indicator's change and each major party's vote share change, across all municipalities.
- `relationship_calculator.py` in `backend/services/`: computes the data for both new outputs. Key functions:
  - `compute_indicator_baselines()`: for each indicator, computes the mean and std dev of change across all KU... municipalities (not the SSS national total — see note below).
  - `calculate_indicator_relationships()`: per-region comparison against those baselines, producing `relative_to_national` classification (above_average / similar / below_average).
  - `calculate_national_correlations()`: cross-municipality Pearson r between indicator change and party vote share change for all major parties.
- Analysis results saved under `backend/data/analysis/`

Important note on national baseline:
The SSS row (national aggregate) is used for rate-based indicators in `GenericAnalysis`. For the `indicator_relationships` comparison, the baseline is the **mean of KU... municipality changes**, not the SSS row. The SSS row for absolute-count indicators like population represents Finland's total population change, which is not a meaningful per-municipality reference.

`run_analysis.py` reads the dataset list from `datasets.yaml` and runs `GenericAnalysis` for every entry. Adding a new dataset to config automatically produces analysis output without any code changes.

---

## 3.4 API

Purpose:
- expose processed data, metadata, and analysis to the frontend

Current endpoints:
- `GET /health`
- `GET /datasets`
- `GET /{dataset_name}`
- `GET /regions/{region}/insights`
- `GET /elections/correlations`

`/elections/correlations` returns the full contents of `election_indicator_correlations.json`, keyed by election year. Returns 404 if the file has not yet been generated (run `make region-insights`).

Expected response shape for `/{dataset_name}`:

```json
{
  "data": [
    {
      "region_code": "KU091",
      "region_name": "Helsinki",
      "year": 2024,
      "value": 12.3
    }
  ],
  "meta": {
    "label": "Unemployment Rate",
    "unit": "%",
    "visualization": {
      "map": {
        "bins": [4, 6, 8, 10, 15]
      }
    }
  },
  "analysis": {
    "GenericAnalysis": {
      "metrics": {...},
      "insights": ["..."]
    }
  }
}
```

The API is intentionally generic so that the frontend does not need dataset-specific logic.

Error handling: unknown dataset names and missing region insight files both return HTTP 404, not 500.

The dataset config is cached at process startup (`@lru_cache`) and not re-read on every request. A server restart is required to pick up config changes.

---

## 4. Frontend architecture

The frontend is built around normalized data and metadata, with two distinct views.

### Main dashboard (`/`)
- List and switch between StatFin datasets
- Line chart for selected region over time
- Year slider controlling the map
- `InsightsPanel`: styled card showing GenericAnalysis text insights (trend + peak sentences) for the current dataset

### Region insights page (`/region/:regionCode`)
Navigated to from the Leaflet map popup (same tab — no `target="_blank"`). Four sections:
1. **Header**: region name + election period from `election_summary`
2. **Socioeconomic context** (`IndicatorGrid` + `IndicatorCard`): 4-column responsive grid. Each card merges `indicators` (raw change) and `indicator_relationships` (national context). Shows the data period, absolute change, and a `relative_to_national` badge (above/similar/below) using neutral colours — no red/green judgment since direction is indicator-dependent.
3. **Party vote shifts** (`PartyChangeChart`): bar chart of `vote_share_change_pct` (percentage points, not raw vote count), green for gains, red for losses, `party_code` on axis, full `party_name` in tooltip.
4. **National correlations** (`CorrelationTable`): table of Pearson r between indicator changes and party vote share changes across all 292 municipalities. Fetched from `GET /elections/correlations`. Absent silently if endpoint returns 404.

Important frontend principles:
- use `value` instead of dataset-specific metric names
- use `meta.label` and `meta.unit`
- use `region_name` for interactive selection and map matching
- avoid hardcoding dataset names where possible
- never use `vote_change` (raw vote count) — it is meaningless cross-municipality; use `vote_share_change_pct`
- the region page back-link uses React Router `<Link>` — no full page reload, no new tab

### Color scale

All map colouring and legend colours use a single function: `getColor(value, bins)` from `frontend/src/utils/mapScale.js`. There is no other colour utility. Keeping map and legend in sync requires both to call this same function with the same `bins` array. Do not add a second colour implementation.

The scale uses 5 thresholds (configured via `metadata.visualization.map.bins`) producing 6 colour bands.

---

## 5. Config-driven dataset registry

The single most important piece of backend configuration is:

```text
backend/pipelines/config/datasets.yaml
```

Each dataset entry should define:

- source and endpoint
- payload
- transformation rules
- metadata for frontend rendering

Typical structure:

```yaml
datasets:
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
        some_source_column: cleaned_metric_name

      types:
        year: int

      value_column: cleaned_metric_name

      filters: []

      join:
        region_mapping: true

    metadata:
      label: "Some label"
      unit: "%"
      visualization:
        map:
          bins: [10, 20, 30, 40, 50]
```

The elections dataset is **not** in `datasets.yaml`. It has its own pipeline and is not part of the generic config-driven flow.

---

## 6. Reuse of large area selections

To avoid repeating massive area code lists across multiple datasets, the config uses YAML anchors and aliases inside `datasets.yaml`.

This is preferred over adding custom config-reference resolution logic to Python because:
- it is simpler
- it requires no extra loader logic
- PyYAML already resolves anchors automatically

This is an explicit project decision.

---

## 7. Geographic layer alignment

A recurring challenge in the project is geography alignment.

Data may contain:
- `SSS` whole country
- `KU...` municipalities
- `MK...` regions
- other area aggregates

GeoJSON files may represent:
- municipalities (`kunnat.geojson`)
- regions (`maakunnat.geojson`)

Therefore:
- the dataset's geography level must match the chosen GeoJSON
- `region_name` must match GeoJSON property names exactly
- filters may be needed to keep only the relevant geography level

This is a central architectural concern, not a small implementation detail.

---

## 8. Region mapping

Region mapping is handled through:

```text
backend/data/region_mapping.csv
```

Purpose:
- translate area codes into human-readable names
- support frontend map and chart selection
- decouple source codes from presentation logic

Important:
- region mapping completeness is critical
- missing mappings should be logged or surfaced
- region mapping should be treated as reference data, not ad hoc logic
- `region_mapping.csv` and `party_mapping.csv` are committed to git; generated data files are not

---

## 9. Processed storage format

Current processed format:
- CSV (`latest.csv` only — no timestamped history currently produced for StatFin datasets)

Reasoning:
- easier debugging while iterating rapidly
- simple backend loading
- acceptable for current scale

Future possibility:
- parquet may be reintroduced later for performance/typing

This is currently a deliberate tradeoff, not an oversight.

---

## 10. Metadata-driven frontend behavior

The frontend should increasingly use metadata rather than hardcoded assumptions.

Already in use:
- `label`
- `unit`
- `visualization.map.bins`

Likely future metadata:
- geography level (currently hardcoded to `kunnat.geojson` and `feature.properties.Kunta`)
- default national label
- chart formatting hints
- source notes

This is the right long-term direction because it keeps the frontend generic as datasets grow.

---

## 11. Current pain points

The following areas are known to be sensitive:

- geography mismatches between data and GeoJSON — the map currently assumes municipality-level data and `kunnat.geojson`; region-level datasets would break the map without additional metadata
- missing region mappings
- forgetting required metadata in new dataset config
- forgetting to specify `value_column`
- transformation errors when config is incomplete
- frontend breakage if metadata is missing or inconsistent
- the elections pipeline is entirely outside the config-driven flow and requires manual execution of multiple scripts in sequence

---

## 12. Architectural direction going forward

The preferred direction is:

- more config-driven transformation
- fewer dataset-specific cleaning files
- more metadata-driven frontend behavior
- geography level as explicit metadata so the frontend can select the right GeoJSON automatically
- stronger validation around config completeness

The project should continue moving toward:
- less repetition
- more explicit configuration
- better defaults
- stronger consistency across datasets

---

## 13. Summary

InsightKartta is a config-driven analytics platform with:

- reusable ingestion and generic transformation for StatFin datasets
- a generic analysis engine that produces output for every configured dataset
- a parallel elections pipeline that handles HTML scraping and party-level data
- a generic API with proper error handling
- metadata-driven frontend rendering with a consistent colour scale

That direction should be preserved. New StatFin datasets should strengthen the config-driven pattern. The elections pipeline is a known explicit exception.
