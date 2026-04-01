# InsightKartta Project Context

This file exists to give a future LLM/chatbot enough context to continue the project effectively without re-deriving decisions from scratch.

Use this file as project memory.

---

## 1. Project identity

Project name:
- InsightKartta

Purpose:
- a portfolio-quality software engineering project
- analyzes Finnish statistics from Statistics Finland
- intended to demonstrate architecture, data engineering, backend, frontend, and interactive visualization skills
- not intended to be just a plotting exercise

Main design philosophy:
- config-driven
- extensible
- normalize datasets into a shared frontend-friendly shape
- preserve a clear project structure and explicit decisions

---

## 2. Current high-level architecture

Layers:
1. ingestion
2. transformation
3. analysis
4. FastAPI backend
5. React frontend

The system is intended to work like this:

1. datasets are declared in `backend/pipelines/config/datasets.yaml`
2. ingestion fetches raw StatFin data into `backend/data/raw`
3. transformation reads the latest raw file, applies generic config-driven steps, and writes `backend/data/processed/<dataset>/latest.csv`
4. analysis reads processed data and writes JSON analysis output under `backend/data/analysis`
5. FastAPI serves datasets generically
6. React frontend renders chart + map + insights using normalized data and metadata

---

## 3. Important current directory picture

The repo structure currently revolves around:

```text
backend/
  app/
    api/
      routes.py
    services/
      dataset_service.py
    utils/
      serialization.py
    main.py

  data/
    raw/
    processed/
    analysis/
    region_mapping.csv

  pipelines/
    config/
      datasets.yaml
    ingestion/
    transformation/
      transform_runner.py
      steps/
    analysis/
      engine.py
      run_analysis.py
      unemployment/
        analysis.py

frontend/
  public/
    kunnat.geojson
    maakunnat.geojson

  src/
    components/
    utils/
    api.js
    App.jsx
```

The exact file layout may shift slightly, but the above is the intended mental model.

---

## 4. Core backend decisions already made

### 4.1 Config-driven datasets
A dataset should be addable mainly by editing `backend/pipelines/config/datasets.yaml`.

This is a deliberate architectural priority.

### 4.2 Generic transformation over custom cleaning
At first there were dataset-specific transformation modules such as `unemployment.py`. Over time it became clear that many of them mostly:
- renamed `Alue -> region`
- renamed `Vuosi -> year`
- renamed one metric
- cast `year` to int

Conclusion:
- these should be handled generically in config
- dataset-specific modules should only remain when a dataset genuinely needs custom logic

### 4.3 Unified frontend contract
The frontend should work against a normalized row shape:

```json
{
  "region_name": "Helsinki",
  "year": 2024,
  "value": 12.3
}
```

`region` code may still exist in backend data, but the frontend is moving toward using `region_name` only.

### 4.4 CSV for processed data
Processed storage used to be parquet. It was changed to CSV.

Current recommendation:
- CSV is acceptable for now
- parquet can return later if it becomes clearly beneficial

FastAPI and analysis code must not assume parquet anymore.

### 4.5 Metadata is required
Datasets need metadata for the frontend:
- label
- unit
- visualization bins

Without this, the frontend becomes brittle or visually misleading.

---

## 5. Current frontend decisions already made

### 5.1 Frontend should be generic
Avoid dataset-specific frontend logic like:
- `analysis.UnemploymentAnalysis`
- `dataKey="unemployment_rate"`
- hardcoded `/unemployment` assumptions

Instead:
- dataset list comes from `/datasets`
- selected dataset comes from `/{dataset_name}`
- chart should use `value`
- title/units should come from `meta`

### 5.2 Use `region_name` in the frontend
The UI currently uses `region_name` instead of `region` code because the GeoJSON is name-based.

This simplification was intentional:
- chart selection uses `region_name`
- map matching uses `region_name`

Long-term, geography handling may become more formal through metadata.

### 5.3 Map bins must be dataset-aware
The original hardcoded unemployment bins caused education maps to have no variation because all values were above the upper threshold.

Decision:
- make map bins configurable through metadata
- frontend color scale and legend should read bins from `meta.visualization.map.bins`
- fallback to automatic bins only if metadata is missing

### 5.4 GeoJSON lifecycle gotchas already encountered
React Leaflet `onEachFeature` does not automatically refresh when state changes.

Known fixes:
- use a changing `key` on the `GeoJSON` component
- do not mount the layer before data is ready

This matters for tooltips and year-based updates.

---

## 6. Current dataset registry expectations

Every dataset entry in `backend/pipelines/config/datasets.yaml` should include:

- `name`
- `source`
- `endpoint`
- `payload`
- `transformation`
- `metadata`

Typical transformation block:

```yaml
transformation:
  dimensions:
    region: Alue
    year: Vuosi

  rename:
    some_source_metric: cleaned_metric_name

  types:
    year: int

  value_column: cleaned_metric_name

  filters: []

  join:
    region_mapping: true
```

Typical metadata block:

```yaml
metadata:
  label: "Human-readable label"
  unit: "%"
  visualization:
    map:
      bins: [10, 20, 30, 40, 50]
```

---

## 7. YAML anchors decision

There was a discussion about adding custom `values_ref` resolving logic in `config_loader.py` to avoid repeating large area-code lists.

Final decision:
- do **not** add extra config loader complexity for this
- instead use YAML anchors and aliases directly in `datasets.yaml`

Reason:
- simpler
- no custom logic required
- PyYAML already handles it

This is an explicit decision and should be respected unless there is a strong later need for multi-file config composition.

---

## 8. Datasets already worked on

### 8.1 Unemployment
This is the first dataset that was implemented successfully.

Important notes:
- transformation and frontend originally assumed unemployment-specific names
- this is being generalized
- analysis currently exists for unemployment

### 8.2 Education
The education work revealed several important lessons:
- PXWeb payloads can require more explicit querying than unemployment
- area selection may need to be explicit
- some dimensions that look queryable may still cause 400s depending on the table
- the geometry level may include municipalities, regions, and whole-country rows together

Specific education targets:
- share of population aged 15+ with at least upper secondary education
- share of population aged 15+ with at least tertiary education

### 8.3 Population
Population is being added mainly as a test of whether the config-driven dataset approach scales.

---

## 9. Geography and mapping decisions

This has been one of the trickiest parts of the project.

Known facts:
- StatFin area values may include `SSS`, `KU...`, `MK...`, and other aggregates
- GeoJSON files may be municipality-level or region-level
- names in GeoJSON must match `region_name` exactly for map coloring and tooltips to work

Current practical approach:
- use `region_mapping.csv`
- keep the frontend on `region_name`
- filter or align geography level as needed per dataset

This area is sensitive and easy to break.

---

## 10. Common mistakes already made

These are important because they should not be repeated.

### 10.1 Forgetting metadata
Adding a dataset without:
- `label`
- `unit`
- `visualization.map.bins`

creates frontend problems.

### 10.2 Forgetting `value_column`
If `value_column` is missing or wrong, transformation fails because normalization to `value` fails.

### 10.3 Hardcoding old dataset endpoints and names
Examples of outdated assumptions:
- `/unemployment`
- `unemployment_basic`
- parquet-only loading paths

These need to stay replaced by generic dataset-based handling.

### 10.4 Assuming the frontend should use region codes
The frontend intentionally shifted toward `region_name`. Reintroducing `region` code into frontend state is usually unnecessary unless a real need appears.

### 10.5 Overcomplicating config loading
A custom reference resolver for selections was proposed and then rejected in favor of YAML anchors.

---

## 11. Important implementation preferences

When continuing this project:

- prefer config changes over new one-off code
- prefer generic pipeline steps over custom dataset modules
- prefer metadata-driven frontend behavior
- prefer explicit documented decisions over silent assumptions
- preserve the architecture rather than bypass it for speed

---

## 12. What the next conversation should remember

If resuming work later, remember to check:

1. whether backend API is fully generic and no old unemployment-only assumptions remain
2. whether processed-data loading uses CSV paths, not parquet
3. whether every new dataset has full metadata
4. whether the transformation section includes:
   - `dimensions`
   - `rename`
   - `types`
   - `value_column`
   - `join`
5. whether frontend uses `value` and `meta`
6. whether map bins are dataset-specific
7. whether geography level matches the GeoJSON used

---

## 13. Summary for a future assistant

The most important thing to understand is this:

InsightKartta is deliberately moving toward a **config-driven multi-dataset analytics platform**.

If a future suggestion:
- adds hardcoded dataset-specific logic where config would suffice
- ignores metadata requirements
- ignores geography alignment
- reintroduces old parquet-specific paths
- or bloats the config loader unnecessarily

then that suggestion is probably going in the wrong direction.

The right direction is:
- simpler
- more generic
- more declarative
- more consistent across datasets
