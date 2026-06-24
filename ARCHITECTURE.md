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
- `GenericAnalysis` in `backend/pipelines/analysis/generic.py`: runs for every StatFin dataset. Filters to the national aggregate row (`region_code == "SSS"`), then computes trend, average, and peak year on the `value` column. Uses the dataset's `metadata.label` for human-readable insight text. Its output is still produced by `run_analysis.py` and still served in the `analysis` field of `GET /{dataset_name}` — but **the main dashboard frontend no longer reads it** (see "Dashboard insights are computed client-side" below). It is kept because it is still a generic, free output of the config-driven pipeline and may be useful to other consumers later; it is not actively wired into any current UI.
- Dataset-specific analysis modules: only needed when a dataset genuinely requires logic that `GenericAnalysis` cannot provide.
- `generate_region_insights.py`: an elections-specific script that derives **every consecutive pair of election years** present in the data (currently `[(2012, 2017), (2017, 2021), (2021, 2025)]`) and produces two outputs covering all of them:
  1. Per-municipality JSON files at `backend/data/analysis/region_insights/<region_code>.json` — each containing a `periods` array (most recent period first), where every entry has its own `election_summary`, `party_changes`, `indicators`, and `indicator_relationships` for that specific period.
  2. A national-level cross-municipality correlation file at `backend/data/analysis/election_indicator_correlations.json` — keyed by each period's end year (e.g. `"2017"`, `"2021"`, `"2025"`), each containing the Pearson correlation between that period's indicator change and each major party's vote share change, across all municipalities.
- `relationship_calculator.py` in `backend/services/`: computes the data for both outputs above, called once per period (baselines and correlations are period-specific, not global). Key functions:
  - `compute_indicator_baselines()`: for each indicator and a given `(start_year, end_year)` period, computes the mean and std dev of change across all KU... municipalities (not the SSS national total — see note below).
  - `calculate_indicator_relationships()`: per-region comparison against those baselines, producing `relative_to_national` classification (above_average / similar / below_average).
  - `calculate_national_correlations()`: cross-municipality Pearson r between indicator change and party vote share change for all major parties, for one explicit `(election_year, previous_election_year)` pair.
- `election_change_calculator.py` in `backend/services/`: `calculate_party_changes(region_df, start_year, end_year)` joins each party's latest-period row to its previous-period row. It joins on **`party_code`**, not `party_raw`/`party_name` — see the data quality note below.
- Analysis results saved under `backend/data/analysis/`

Important note on national baseline:
The SSS row (national aggregate) is used for rate-based indicators in `GenericAnalysis`. For the `indicator_relationships` comparison, the baseline is the **mean of KU... municipality changes**, not the SSS row. The SSS row for absolute-count indicators like population represents Finland's total population change, which is not a meaningful per-municipality reference.

Data quality note — join election rows on `party_code`, not `party_raw`:
The English `party_raw` label for the same party has been re-translated between some election cycles (e.g. "Green League" in 2012/2017 became "The Greens" in 2021/2025), while `party_code` (e.g. `VIHR`) stays stable. `calculate_party_changes` originally joined on `party_raw`, which made every relabeled party look like it went from 0 votes to its full total whenever a comparison period crossed a relabeling boundary. Once period comparisons were extended back to 2012–2017 and 2017–2021, this became visibly wrong and was fixed by joining on `party_code` instead. Do not reintroduce a join on `party_raw`/`party_name`.

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
- `InsightsPanel`: styled card with a region-name heading and icon-led insight rows. **Computed entirely client-side** by `frontend/src/utils/insights.js`, from whichever region's time series (`chartData`) and dataset (`meta.label`/`meta.unit`) are currently on screen — not from the backend's `GenericAnalysis` output. Insights produced: trend (first→last value), peak, trough, and a comparison against the national figure for the same year (percentage-point difference for `%`-unit datasets, or "share of Finland's total" for absolute-count datasets like population — see the note in section 3.3 about why these two need different wording). This guarantees the panel's numbers can never drift from the chart, which they could when the panel showed precomputed national-only `GenericAnalysis` text regardless of the selected region.
- `RegionSearch`: typeahead in the top bar. Each result row has two independently clickable parts: a pin-icon button that selects the region on the dashboard (updates the chart/insights and tells `MapView` to style and open the popup for that region, via a `focusRegion` prop — same effect as clicking it on the map), and the rest of the row (text + chevron), which is a normal `<Link>` to that region's full insights page. The dropdown is rendered with a z-index above Leaflet's own panes/controls (which go up to `z-index: 1000`) so it isn't visually clipped by the map.
- `MapView`: also closes any open Leaflet popup whenever the dataset's `data` changes (a small `PopupCloser` child using `useMap()`), so switching datasets never leaves a stale region popup on screen next to insights that have already reset to national.
- Both `RegionSearch` and `MapView` need the municipality boundaries (`kunnat.geojson`, ~700KB), and used to each fetch+parse it independently. They now share one fetch via `frontend/src/hooks/useKunnatGeoJson.js` (a module-level cached promise) — this isn't just an efficiency cleanup; the duplicate fetch was the underlying cause of a real intermittent e2e failure (see §14).

### Region insights page (`/region/:regionCode`)
Navigated to from the Leaflet map popup or `RegionSearch` (same tab — no `target="_blank"`). The API returns **all available election periods** for the region in one response (`insight.periods`, most recent first); the page keeps a `periodIndex` state and re-derives every section below from `periods[periodIndex]` client-side — there is no per-period API call.

Four sections:
1. **Header** (`RegionHeader`): region name, plus a prominent period switcher — one pill per available period (currently 2012→2017, 2017→2021, 2021→2025), the active one filled solid in the accent colour. This is the page's explicit "what am I looking at" affordance; clicking a pill re-renders everything below for that period.
2. **Socioeconomic context** (`IndicatorGrid` + `IndicatorCard`): 4-column responsive grid. Each card merges the selected period's `indicators` (raw change) and `indicator_relationships` (national context). Shows the data period, absolute change, and a `relative_to_national` badge (above/similar/below) using neutral colours — no red/green judgment since direction is indicator-dependent.
3. **Party vote shifts** (`PartyChangeChart`): bar chart of the selected period's `vote_share_change_pct` (percentage points, not raw vote count), green for gains, red for losses, `party_code` on axis, full `party_name` in tooltip.
4. **National correlations** (`CorrelationTable`): table of Pearson r between indicator changes and party vote share changes across all 292 municipalities, for the selected period. Fetched once from `GET /elections/correlations` (which now returns all periods, keyed by end year); the component picks the entry matching the page's selected period (`selectedEndYear` prop), falling back to the latest available if that period isn't present. Absent silently if the endpoint returns 404.

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
- re-running `make ingest` or `make elections-ingest` to refresh raw data writes new timestamped files into `backend/data/raw/`, but `.gitignore` lists that directory — so the new files won't be picked up by a plain `git add`. The existing raw files are tracked anyway (see §15's note on this), so this only bites if you refresh the data and expect the new raw snapshot to be committed automatically; it won't be without `git add -f`.

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
- a parallel elections pipeline that handles HTML scraping and party-level data, now comparing every available consecutive election period rather than only the latest
- a generic API with proper error handling
- metadata-driven frontend rendering with a consistent colour scale
- dashboard insights computed client-side from whatever is currently on screen, so they cannot drift from the chart they sit next to
- automated test coverage at three layers (backend unit/integration, frontend unit/component, end-to-end) targeting the logic that has actually broken before
- a split production deployment (Vercel frontend + Render backend, §15) that mirrors the same separation-of-concerns principle at the infra level, gated by the same CI suite via branch protection on `main`

That direction should be preserved. New StatFin datasets should strengthen the config-driven pattern. The elections pipeline is a known explicit exception.

---

## 14. Testing

Three layers, each chosen to match what's actually risky rather than for blanket coverage:

- **Backend (pytest + httpx, `backend/tests/`)**: pure-function unit tests for `relationship_calculator.py` and `election_change_calculator.py` (the two modules that produced real bugs this project has already had — see §3.3's data-quality notes), plus FastAPI `TestClient` contract tests for all four endpoints against a fixture data tree (`backend/tests/fixtures/`), not real `backend/data/`. `conftest.py` monkeypatches each service's path constants (`dataset_service.CONFIG_PATH`/`PROCESSED_BASE`/`ANALYSIS_BASE`, `insight_service.ANALYSIS_ROOT`/`CORRELATIONS_PATH`) to point at the fixtures and clears `load_config`'s `@lru_cache` before and after, since that cache otherwise leaks state between tests.
- **Frontend (Vitest + Testing Library, colocated `*.test.{js,jsx}` files)**: pure-function tests for `utils/insights.js` and `utils/mapScale.js`, plus a component test for `RegionSearch`'s pin-vs-row click split (§4's "two distinct parts" behavior) using `@testing-library/user-event` and a `MemoryRouter`. `DataChart.jsx`'s y-axis formatter and `PartyChangeChart.jsx`'s sort/tick-formatting logic were each pulled out into small named, exported functions specifically so they could be unit tested without mounting Recharts (which doesn't render meaningfully under jsdom) — a deliberate, behavior-preserving testability refactor, not a design change.
- **End-to-end (Playwright, `frontend/e2e/`)**: drives the real Vite + FastAPI dev servers (via `playwright.config.js`'s `webServer`, which reuses `make server`/`npm run dev` rather than duplicating their startup logic) against whatever data is actually in `backend/data/`. Covers three golden paths: the search pin/row split, a map popup opening via the search pin and closing when the dataset switches, and the region page's period switcher updating every section together.

The e2e layer caught three real bugs during implementation, all fixed in production code (not worked around in the tests):
- `App.jsx`'s initial dataset-load effect unconditionally reset `selectedRegion` to the dataset's default once the request resolved — so picking a region via the search pin while that first load was still in flight got silently clobbered back to national. Fixed with a ref that only protects the *first* load.
- `MapView.jsx`'s `focusRegion` effect only ran once per focus request, so using the search pin before the map had finished mounting found nothing in `layersByNameRef` and silently did nothing. Fixed by also depending on `data`/`year`/`geoData` so it retries — but that alone introduced a second bug (re-opening a popup on every subsequent dataset switch, fighting `PopupCloser`), fixed by an `appliedFocusTokenRef` guard so a given focus request is only ever applied once.
- `map-popup.spec.js` failed intermittently in CI (passed on a bare re-run with no code change) — not a timing fluke. Root cause was two-fold: `RegionSearch` and `MapView` each independently fetched+parsed `kunnat.geojson` (fixed by the shared `useKunnatGeoJson` hook, see §4), and `playwright.config.js` had no `workers` override, so Playwright defaulted to ~half the CPU count (2 on GitHub's 4-vCPU runners) — meaning concurrent test pages contended for the single dev server/backend `webServer` instance the whole suite shares. Confirmed locally: with 2+ workers the popup could fail to appear even with a 15s timeout; with `workers: 1` it was instant and 100% reliable across dozens of repeated runs. Fixed by setting `workers: 1` — not by raising the timeout, which would have masked the real contention.

---

## 15. Deployment

The app is deployed as two genuinely separate services rather than one combined container — the deployment-level expression of the same "separation of concerns" goal in §2.

**Frontend — Vercel.** Static build of the Vite app (`frontend/`, root directory set to `frontend` in Vercel's project settings) served from Vercel's edge CDN, connected via Vercel's native GitHub integration: every push to `main` deploys to production, every PR gets its own preview URL and a status check on the PR. No GitHub Actions deploy job — the platform's own git integration is the deploy mechanism, CI (`ci.yml`) stays the correctness gate in front of it (branch protection on `main` requires `backend`/`frontend`/`e2e` to pass before merge).

Two things were specifically needed beyond a default Vite deploy:
- `frontend/src/api.js` reads `import.meta.env.VITE_API_BASE_URL` (falling back to `http://127.0.0.1:8000` for local dev) instead of a hardcoded localhost URL. Set in Vercel's project environment variables to the Render backend's public URL.
- `frontend/vercel.json` rewrites every path to `/index.html`. Without it, direct navigation to a client-side route like `/region/KU148` (a refresh, or a shared link) hit Vercel's static file server, which has no actual file at that path and returned a literal 404 — `BrowserRouter` (used in `main.jsx`) only resolves that path in client-side JS, after `index.html` has already loaded. This is a standard requirement for any `BrowserRouter`-based SPA on a static host, not InsightKartta-specific.

**Backend — Render.** A Dockerized web service built from the root-level `Dockerfile`, connected via Render's native GitHub integration (auto-deploys on push to `main`). The Dockerfile:
1. installs only the production dependencies from `pyproject.toml` (not the `test` extras)
2. copies in `backend/` (including `backend/data/raw/`, see the note below) and runs `make pipeline-all` — transform + elections-transform + analysis + region-insights, producing `backend/data/processed/` and `backend/data/analysis/` inside the image at build time
3. starts the API via a new `make serve` Makefile target (`uvicorn ... --host 0.0.0.0 --port $PORT`, no `--reload`) — distinct from `make server`, which stays the dev-only `--reload` target on a fixed port 8000

`backend/app/main.py`'s CORS origin list is now read from `ALLOWED_ORIGINS` (comma-separated env var, defaulting to `http://localhost:5173` for local dev) instead of being hardcoded, set on Render to the Vercel production URL.

**Why the Docker build needs no network access**, despite raw data nominally being "regenerated at build time": `backend/data/raw/` (StatFin JSON responses and all scraped election HTML, ~49MB) is actually committed to git, even though `.gitignore` lists that path. The ignore rule predates those files being committed (or they were force-added at some point) and was never retroactively cleaned up with `git rm --cached`; either way, `git ls-files backend/data/raw` confirms thousands of tracked files there today. This was discovered, not designed — but it's now treated as the deliberate state: `make pipeline-all` (transform/analysis/region-insights only, no `ingest`/`elections-ingest`) only ever reads already-present raw data, so the Render build has no dependency on StatFin's API or vaalit.fi being reachable at build time. Validated by running the exact Dockerfile steps (`pip install .` into a clean venv, then `make pipeline-all PYTHON=python3`, then `make serve`) outside Docker and confirming the API served real data. The corollary — re-running `make ingest`/`make elections-ingest` produces new raw files that `.gitignore` will silently exclude from `git add` — is noted in §11.

**Cold start.** Render's free tier sleeps the backend after inactivity; the first request after that can take up to ~60 seconds. `App.jsx` tracks `datasetsLoading`/`datasetsError` around its initial `fetchDatasets()` call and renders an explicit spinner + "Waking up the server…" message (and a distinct "Couldn't reach the server" message on failure) instead of rendering mostly-empty panels with no indication anything is happening. Vercel's CDN means the page shell itself still loads instantly even while the backend is cold — the split topology is what makes that possible, not an incidental benefit.

See `INSTRUCTIONS.md` §17 for testing rules and `CONTEXT.md` §10.16–10.19 for the full writeups of all three bugs.
