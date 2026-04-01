# InsightKartta Architecture

This document explains the current intended architecture of InsightKartta, why certain design decisions were made, and how data flows through the system.

---

## 1. Architecture overview

InsightKartta is a layered, config-driven system.

```text
Statistics Finland PXWeb API
          ↓
     Ingestion layer
          ↓
        Raw JSON
          ↓
   Transformation layer
          ↓
   Normalized processed CSV
          ↓
     Analysis layer
          ↓
   Analysis JSON results
          ↓
       FastAPI API
          ↓
      React frontend
```

The important architectural choice is that new datasets should be added mostly through configuration, not through repeated custom code.

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

Dataset-specific transformation modules:
- should exist only when a dataset truly requires custom logic
- should not be the default path

This is an explicit architectural decision based on the observation that many datasets only need config-driven renaming and typing.

---

## 3.3 Analysis

Purpose:
- generate reusable insights from processed datasets

Structure:
- a generic analysis engine
- dataset-specific analysis modules where needed
- analysis results saved under `backend/data/analysis/`

Important point:
Analysis should run on already normalized processed data, not on raw source-specific schemas.

---

## 3.4 API

Purpose:
- expose processed data, metadata, and analysis to the frontend

Current intended endpoints:
- `/health`
- `/datasets`
- `/{dataset_name}`

Expected response shape:

```json
{
  "data": [
    {
      "region": "KU091",
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
    "SomeAnalysis": {
      "insights": ["..."]
    }
  }
}
```

The API is intentionally generic so that the frontend does not need dataset-specific logic.

---

## 4. Frontend architecture

The frontend is built around normalized data and metadata.

Main responsibilities:
- list available datasets
- fetch one dataset at a time
- render chart
- render map
- render insights
- react to region selection and year selection

Important frontend principles:
- use `value` instead of dataset-specific metric names
- use `meta.label` and `meta.unit`
- use `region_name` for interactive selection and map matching
- avoid hardcoding dataset names where possible

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
- the dataset’s geography level must match the chosen GeoJSON
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

---

## 9. Processed storage format

Current processed format:
- CSV (`latest.csv` plus timestamped history)

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

Already relevant:
- `label`
- `unit`
- `visualization.map.bins`

Likely future metadata:
- geography level
- default national label
- chart formatting hints
- source notes

This is the right long-term direction because it keeps the frontend generic as datasets grow.

---

## 11. Current pain points

The following areas are known to be sensitive:

- geography mismatches between data and GeoJSON
- missing region mappings
- forgetting required metadata in new dataset config
- forgetting to specify `value_column`
- transformation errors when config is incomplete
- frontend breakage if metadata is missing or inconsistent
- dataset-specific assumptions creeping back into shared components

---

## 12. Architectural direction going forward

The preferred direction is:

- more config-driven transformation
- fewer dataset-specific cleaning files
- more metadata-driven frontend behavior
- clearer geography handling per dataset
- stronger validation around config completeness

The project should continue moving toward:
- less repetition
- more explicit configuration
- better defaults
- stronger consistency across datasets

---

## 13. Summary

InsightKartta is evolving into a config-driven analytics platform with:

- reusable ingestion
- generic transformation
- modular analysis
- generic API
- metadata-driven frontend rendering

That direction should be preserved. New features should strengthen this pattern rather than bypass it.
