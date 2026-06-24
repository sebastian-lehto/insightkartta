# InsightKartta Instructions

This file exists to prevent repeated mistakes, avoid unnecessary delays, and preserve the intended architecture.

Read this before adding or changing datasets, backend pipeline logic, API behavior, or frontend visualizations.

---

## 1. General rules

1. Preserve the config-driven architecture for StatFin datasets.
2. Prefer generic pipeline steps over dataset-specific code.
3. Do not introduce one-off hacks into the frontend if the problem belongs in the backend or config.
4. Keep the frontend generic.
5. Keep metadata complete and explicit.
6. Be careful with geography level alignment.
7. Do not reintroduce outdated assumptions such as parquet-only paths or single-dataset endpoints.
8. The elections pipeline is an explicit exception to the config-driven pattern. Treat it as such, not as a model to replicate for future StatFin datasets.

---

## 2. Before adding a new StatFin dataset

Before implementing a new dataset, verify all of the following:

- the StatFin endpoint is correct
- the PXWeb payload actually works
- the geography level is understood
- the metric to normalize into `value` is identified
- the frontend label and unit are known (no leading space in unit)
- the map bins are at least initially defined (exactly 5 values)

Do not proceed with a partial dataset definition if these basics are unknown.

---

## 3. Every StatFin dataset entry in `datasets.yaml` must include

At minimum:

- `name`
- `source`
- `endpoint`
- `payload`
- `transformation`
- `metadata`

### Required transformation sub-sections

Always remember to include:

- `dimensions`
- `rename`
- `types`
- `value_column`
- `filters`
- `join`

Even if some are empty.

### Required metadata

Always remember to include:

- `label`
- `unit` — no leading space
- `visualization.map.bins` — exactly 5 values

Do not omit visualization metadata just because the dataset ingests successfully.

---

## 4. Mandatory dataset checklist

When adding a StatFin dataset, confirm:

### Payload
- the query actually returns the intended data
- if area selection is needed, it is provided
- do not assume empty query works correctly just because it returns something

### Transformation
- `dimensions.region` points to the correct source column
- `dimensions.year` points to the correct source column
- `rename` includes the metric that should become `value`
- `value_column` refers to the renamed metric, not the raw one
- `types.year: int` is present if year exists
- `join.region_mapping: true` is included if the frontend needs `region_name`

### Metadata
- label is human-readable
- unit is correct and has no leading space
- bins have exactly 5 values that make sense for the value range

### After adding
- run `run_ingestion.py` to fetch raw data
- run `run_transformation.py` to produce processed CSV
- run `run_analysis.py` to produce analysis JSON — this is required for the API `analysis` field to be populated
- restart the API server (config is cached at startup)

---

## 5. Things to remember about transformation

1. New StatFin datasets should need as little custom code as possible.
2. If a dataset only needs:
   - `Alue -> region`
   - `Vuosi -> year`
   - one metric rename
   - `year -> int`
   then do not create a dataset-specific cleaning module.
3. Prefer the generic config-driven transformation flow.
4. Keep dataset-specific transformation files only for genuinely unusual cases.

### Important
Remember to add the `rename` section and `value_column` section with the right values. This has already caused failures.

### Elections exception
The elections pipeline has its own transformation script (`normalize_party_votes.py`) because the input is HTML, not PXWeb JSON. Its output still uses `region_code` as the canonical column name and is stored in the same processed directory convention.

---

## 6. Things to remember about metadata

Metadata is not optional.

Always remember to add all necessary metadata.

At minimum:
- `label`
- `unit` — no leading space before the unit string
- `visualization.map.bins` — exactly 5 values

Without metadata:
- chart titles become weak or wrong
- units disappear or display incorrectly
- map colors and legend become misleading or useless

The colour scale uses all 5 bin thresholds to produce 6 colour bands. Fewer than 5 values will silently drop the top band(s).

---

## 7. Things to remember about geography

This project depends heavily on matching data geography to GeoJSON geography.

Always verify:
- whether the dataset is municipality-level or region-level
- whether the selected GeoJSON is `kunnat.geojson` or `maakunnat.geojson`
- whether `region_name` matches GeoJSON property names exactly

The frontend map currently hardcodes `kunnat.geojson` and `feature.properties.Kunta`. If you add a region-level dataset, the map will render incorrectly without additional metadata-driven geography selection.

If the geography does not match:
- the map may render with no colors
- tooltips may say `No data`
- clicks may not update the chart correctly

Do not treat this as a minor detail.

---

## 8. Frontend rules

1. The frontend should use `value`, not dataset-specific metric names.
2. The frontend should use `meta.label` and `meta.unit`.
3. The frontend should prefer `region_name` over `region_code`.
4. The frontend should not hardcode dataset names.
5. The frontend should get the dataset list from `/datasets`.

### Map and colour scale rules
- Do not hardcode bins for any specific dataset.
- Use `meta.visualization.map.bins` for the colour scale.
- Both `MapView` and `MapLegend` must use `getColor` from `mapScale.js` with the same `bins` array.
- There is no `colorScale.js`. Do not create a second colour utility.
- Keep legend and colour scale in sync by using the same function and same bins.
- Do not mount Leaflet layers before data is ready.
- If tooltips fail to update, remember that `GeoJSON` may need a changing `key`.

### Main-dashboard insights rule
- `InsightsPanel` must compute its text from whatever region/dataset is currently rendered (`frontend/src/utils/insights.js`, given the same `chartData` the chart uses), never from the backend's `GenericAnalysis`/`analysis` field. That field is always national; the chart is whatever region is selected. Wiring the panel to it reintroduces a real bug where the panel's numbers silently stop matching the chart.
- When adding a comparison against a national figure, branch on `unit`: a `%`-unit dataset can use a percentage-point difference ("above/below the national rate"); an absolute-count dataset (e.g. `persons`) cannot — the national row there is a sum, not an average, so express it as a share of the total instead ("accounted for X% of Finland's total").

### Region search rule
- `RegionSearch` dropdown rows must keep two separate click targets: the pin icon selects the region on the dashboard map/chart without navigating; the rest of the row (and Enter) navigates to the region's insights page. Do not merge these into a single handler.
- The search dropdown must render above Leaflet's panes/controls (`z-index: 1500` vs Leaflet's max of `1000`). If the dropdown ever appears to render "under" the map again, check the z-index first.

---

## 9. Backend rules

1. The API should be generic.
2. Do not add old-style dataset-specific endpoints unless absolutely necessary.
3. Processed data loading uses the current CSV-based structure.
4. Do not reintroduce hardcoded parquet assumptions.
5. Keep service logic generic and dataset-driven.
6. Unknown dataset names must return HTTP 404, not 500.
7. Missing region insight files must return HTTP 404, not 500.
8. Config is cached at startup — restart the server after changing `datasets.yaml`.

---

## 10. Config rules

### Use YAML anchors for shared large lists
Do not add custom config-loader complexity just to reuse area code lists.

Preferred approach:
- define shared area lists with YAML anchors
- reuse them with aliases inside `datasets.yaml`

Do not build a custom resolver.

### `bins` must have exactly 5 values
The colour scale uses thresholds at indices 0–4. Providing fewer values silently drops the upper colour bands.

---

## 11. Analysis rules

1. `GenericAnalysis` runs automatically for every dataset in `datasets.yaml`. Do not create a dataset-specific analysis class unless the required logic genuinely differs from trend/average/peak on the national aggregate. Its output is still served via the API but has no frontend consumer anymore (see §8's main-dashboard insights rule) — that's expected, not a bug.
2. `run_analysis.py` must be run after adding or re-running a dataset to persist analysis results. The API reads from `backend/data/analysis/<dataset>.json` and returns `null` if the file does not exist.
3. `generate_region_insights.py` is elections-specific. It reads the StatFin indicator list from `datasets.yaml` automatically — no hardcoded paths.
4. `generate_region_insights.py` derives **every consecutive pair of election years** present in the data (currently 2012→2017, 2017→2021, 2021→2025) and produces two outputs covering all of them: per-region JSON files (each with a `periods` array, most recent first) and `election_indicator_correlations.json` (keyed by each period's end year). Both are regenerated every time the script runs. Do not treat them as independent — they share the same per-period baselines computation.
5. `relationship_calculator.py` contains three functions that must stay in sync with each other, and are now called **once per period**, not once globally:
   - `compute_indicator_baselines()` — call once per `(start_year, end_year)` period before the region loop for that period; uses mean of KU... municipalities
   - `calculate_indicator_relationships()` — call per region per period with that period's precomputed baselines
   - `calculate_national_correlations()` — call once per period after the region loop
6. The national baseline for `indicator_relationships` is the **mean of KU... municipality changes**, not the SSS national aggregate. Do not change this to use the SSS row — for absolute-count indicators like population, the SSS row is the national total and renders the comparison meaningless.
7. The `GET /elections/correlations` API endpoint returns 404 if `election_indicator_correlations.json` does not exist. This is the correct behaviour — it is not an error in the API, it means `make region-insights` has not been run yet.
8. `calculate_party_changes(region_df, start_year, end_year)` in `election_change_calculator.py` joins each party's two rows on **`party_code`**, never on `party_raw`/`party_name`. Several major parties' English labels were re-translated between election cycles (e.g. "Green League" → "The Greens"); joining on the label breaks the comparison across that boundary by making the party look brand new. `party_code` is stable and unique within any region+year — always join on it.

---

## 12. Elections pipeline rules

The elections pipeline is a custom path that runs independently of the StatFin config-driven flow:

1. Run `fetch_municipal_elections.py` to scrape HTML.
2. Run `normalize_party_votes.py` to produce processed CSV.
3. Run `generate_region_insights.py` to produce, for **every** consecutive election-year pair found in the data:
   - 292 per-municipality JSON files in `backend/data/analysis/region_insights/`, each containing a `periods` array
   - `backend/data/analysis/election_indicator_correlations.json`, keyed by each period's end year

None of these are called by `run_ingestion.py`, `run_transformation.py`, or `run_analysis.py`. That is intentional.

The elections processed CSV uses `region_code` as the canonical column name, matching the StatFin convention.

Do not use the elections pipeline as a model for adding new StatFin datasets.

### Frontend rules for election insights

- Use `vote_share_change_pct` for all party comparisons, never `vote_change` (raw count).
- Display `party_code` as the axis label and `party_name` in tooltips — full Finnish party names are too long for axis labels.
- The `indicator_relationships` section of a region JSON provides the national context (above/below/similar). Use neutral colour coding — do not assign good/bad colours to direction, because the same direction has opposite implications depending on the indicator.
- The `CorrelationTable` component fetches from `GET /elections/correlations` independently and fails silently with `null` if the endpoint is not available. Do not make it a blocking dependency for the rest of the region page. It also accepts a `selectedEndYear` prop to pick the period matching whatever the rest of the region page is showing, falling back to the most recent period if that key isn't present.
- The map popup link to the region page must not use `target="_blank"`. It should open in the same tab so the back-link in `RegionPage` works correctly. The back-link must use React Router `<Link>`, not `<a href>`, to avoid a full page reload.
- `RegionPage` owns a `periodIndex` state (default `0` = most recent) and must pass `periods[periodIndex]`'s fields down to `RegionHeader`, `IndicatorGrid`, and `PartyChangeChart`, and that period's `latest_year` to `CorrelationTable` as `selectedEndYear`. There is no per-period API call — the API already returns every period in one response.

---

## 13. Debugging rules

When something fails, check in this order:

1. Is the endpoint correct?
2. Does the PXWeb payload actually return the intended dimensions?
3. Does the transformed DataFrame have the columns expected by config?
4. Does `rename` match actual source column names?
5. Does `value_column` exist after renaming?
6. Is `region_mapping.csv` complete enough?
7. Does `region_name` match the GeoJSON?
8. Does metadata include `bins` with exactly 5 values and a correct `unit` (no leading space)?
9. Is the frontend using `value` and `meta`, not old dataset-specific fields?
10. Was `run_analysis.py` run after the last transformation? (API `analysis` is `null` if the JSON file is missing.)
11. Was the server restarted after changing `datasets.yaml`? (Config is cached at startup.)
12. Was `make region-insights` run after changing `relationship_calculator.py`? (Both per-region JSONs and `election_indicator_correlations.json` must be regenerated.)
13. Does `GET /elections/correlations` return 404? If so, run `make region-insights` — the file has not been generated yet. This is not an API bug.
14. Is the `indicator_relationships` national reference using the mean of municipalities? If it looks wrong for population (every region "below average"), the SSS row has crept back in — `compute_indicator_baselines` must use `mean_municipal_change`, not `national_change`.
15. Do older election periods (2012→2017, 2017→2021) show a major party jumping from 0 votes to its full total, or vice versa? Check whether `calculate_party_changes` is joining on `party_code` (correct) — if it's joining on `party_raw`/`party_name` again, a relabeled party (e.g. VIHR) will look brand new across the relabeling boundary.
16. Does the main-dashboard `InsightsPanel`'s peak/trend text disagree with the chart right next to it? Check that it's still computing from `regionData`/`allData` via `frontend/src/utils/insights.js`, not reading `GET /{dataset_name}`'s `analysis` field (which is always national).
17. Does the region page show the wrong correlation table for the selected period, or does the search dropdown render underneath the map? Check `CorrelationTable`'s `selectedEndYear` prop and the `region-search-dropdown` z-index (must stay above Leaflet's `1000`), respectively.
18. Did a search-pin click on a freshly-loaded dashboard silently do nothing, or get reverted a moment later? Check `App.jsx`'s `isInitialDatasetLoadRef` guard and `MapView.jsx`'s `focusRegion` effect dependencies/`appliedFocusTokenRef` guard (§10.16/§10.17 in `CONTEXT.md`) — both exist specifically to prevent the initial dataset load, or a later dataset switch, from clobbering a region selection made via the search pin.
19. Does the deployed frontend show "Couldn't reach the server," or does the browser devtools console show a CORS error? Check `VITE_API_BASE_URL` in Vercel's project settings (frontend) and `ALLOWED_ORIGINS` in Render's environment settings (backend) — see §18. This is not a code bug if both env vars are correctly set; it usually means one platform's URL changed and the other wasn't updated.
20. Does a direct navigation (refresh, or a shared link) to `/region/:regionCode` 404 on the deployed Vercel site but work fine when navigated to from within the app? Check that `frontend/vercel.json`'s catch-all rewrite still exists — `BrowserRouter` only resolves that route client-side, see §18.
21. Did an e2e spec fail intermittently in CI but pass on a bare re-run with no code change? Check `frontend/playwright.config.js`'s `workers` value before assuming it's "just flaky" — see §17.10/§18 and `CONTEXT.md` §10.19. The whole suite shares one `webServer`; more than 1 worker means concurrent test pages contending for it, which has caused real (not just slow) failures before.

This order avoids wasting time.

---

## 14. Things not to forget when resuming later

When resuming after a break, explicitly re-check:

- CSV vs parquet assumptions
- current backend structure
- whether API routes are generic and return 404 correctly
- whether frontend dataset switching still uses metadata correctly
- whether new datasets have full transformation and metadata blocks with 5 bins
- whether map legend and colour scale both use `mapScale.js`
- whether `run_analysis.py` was run after the last pipeline run
- whether geography level is consistent with the GeoJSON loaded by the frontend
- whether `generate_region_insights.py` still produces a `periods` array (one entry per consecutive election-year pair) rather than a single flat period, and whether `make region-insights` was re-run after any change to `election_change_calculator.py` or `relationship_calculator.py`
- whether `make test` / `make test-e2e` still pass before considering any change to `relationship_calculator.py`, `election_change_calculator.py`, `insights.js`, `mapScale.js`, `RegionSearch.jsx`, `App.jsx`, or `MapView.jsx` complete
- whether `frontend/src/api.js`'s `VITE_API_BASE_URL` and `backend/app/main.py`'s `ALLOWED_ORIGINS` env-var wiring is still in place — see §18
- whether `frontend/vercel.json`'s SPA rewrite still exists if `frontend/` gets restructured
- whether `frontend/playwright.config.js` still has `workers: 1` — see §17.10
- whether `backend/data/raw/` is still tracked in git (the deployed backend's build depends on it not needing network access) — see §18

---

## 15. Preferred development direction

Good direction:
- more generic
- more declarative
- more metadata-driven
- less repetition
- fewer one-off exceptions

Bad direction:
- hardcoding special cases into the frontend
- adding custom loaders when YAML can already solve the problem
- adding dataset-specific analysis or cleaning for trivial rename/type tasks
- skipping metadata because "it works for now"
- ignoring geography mismatches
- adding a second colour utility alongside `mapScale.js`
- treating the elections pipeline pattern as the default for new datasets

---

## 16. Final reminder

The project should feel like a coherent data platform.

Before merging any change, ask:

- does this reduce or increase repetition?
- does this preserve the generic frontend contract?
- does this preserve the config-driven backend?
- does this make adding the next dataset easier or harder?

If it makes the next dataset harder, it is probably the wrong change.

---

## 17. Testing rules

1. Run tests with `make test-backend` (pytest), `make test-frontend` (vitest), `make test-e2e` (playwright), or `make test` for backend+frontend together.
2. Backend tests must run against `backend/tests/fixtures/`, never real `backend/data/`. Use the `api_client` fixture in `conftest.py` (it monkeypatches every service's path constants and clears `load_config`'s `@lru_cache`) rather than hitting the real data directory or skipping cache-clearing.
3. Test dependencies (`pytest`, `pytest-cov`, `httpx`) live in `pyproject.toml`'s `[project.optional-dependencies].test` group. `pyproject.toml` is the real backend dependency manifest — `make venv` installs from it. Do not reintroduce a hardcoded pip-install line in the Makefile, and do not add a separate `requirements.txt` alongside it.
4. Frontend component/unit tests are colocated as `*.test.{js,jsx}` next to the file they test. Any new test file that renders JSX must rely on `frontend/src/test/setup.js` (already wired into every test run) rather than re-solving "React is not defined" locally — adding a plain `import React from "react"` to an individual test file does not fix it in this project's toolchain.
5. Always call `afterEach(cleanup)` for component tests — already handled globally in `frontend/src/test/setup.js`, so don't add a second, file-local cleanup call; if a test file renders the same component twice and a query like `getByLabel` reports "multiple elements," check that the global setup file's `afterEach` hasn't been bypassed (e.g. a different vitest config, or `globals: true` not actually wired up the way you'd expect).
6. If logic genuinely cannot be unit tested because it's inline inside a Recharts-wrapped component (Recharts doesn't render meaningfully under jsdom), pull it into a small named, exported, behavior-preserving function next to the component (see `DataChart.jsx`'s `yFormatter`, `PartyChangeChart.jsx`'s `sortPartyChanges`/`formatPartyCodeTick`) rather than leaving it untested or attempting to test it through a full Recharts render.
7. Playwright e2e specs (`frontend/e2e/`) run against the real dev servers and real `backend/data/`, not fixtures — they're meant to catch integration-level and timing bugs that fixture-backed tests can't. `playwright.config.js`'s `webServer` entries shell out to `make server` and `npm run dev`; do not duplicate the Makefile's Python interpreter resolution logic inside the Playwright config.
8. If an e2e test is flaky and "passes with a short delay added," do not add the delay. That is almost always a real race condition in production code, not a timing quirk in the test — see `CONTEXT.md` §10.16 and §10.17 for two real examples found exactly this way (`App.jsx`'s initial-load region-selection race, `MapView.jsx`'s focusRegion-vs-PopupCloser race). Find and fix the underlying effect/state-update ordering instead.
9. Do not add Playwright/Selenium-style browser tests assuming a system-installed, version-matched Chrome/driver pair. Playwright bundles its own browser binaries (`npx playwright install`) specifically to avoid that failure mode.
10. `playwright.config.js` must keep `workers: 1`. The whole e2e suite shares a single `webServer` pair (one Vite dev server, one uvicorn process) — there are no per-worker server instances. Without `workers: 1`, Playwright's CPU-count-based default (e.g. 2 on GitHub's 4-vCPU runners) puts concurrent test pages against that single shared backend, which has caused real, intermittent CI failures (not just slower ones) — see `CONTEXT.md` §10.19. If a future change makes per-worker server instances actually possible, this rule can be revisited; until then, do not raise `workers` to "speed up" the suite.

---

## 18. Deployment rules

The app is deployed split: Vercel (frontend, static) + Render (backend, Docker), each connected via native GitHub git integration (auto-deploy on push to `main`, no custom GitHub Actions deploy job). CI (`ci.yml`) stays the correctness gate via branch protection on `main` — do not bypass branch protection to "ship faster."

1. Never hardcode an API base URL or CORS origin again. `frontend/src/api.js` reads `import.meta.env.VITE_API_BASE_URL` (fallback `http://127.0.0.1:8000`); `backend/app/main.py` reads `ALLOWED_ORIGINS` (fallback `http://localhost:5173`, comma-separated for multiple origins). If either platform's URL ever changes, update the env var in that platform's dashboard — do not patch the code.
2. `frontend/vercel.json`'s catch-all rewrite (`"source": "/(.*)"` → `/index.html`) must stay in place as long as the frontend uses `BrowserRouter`. Without it, every client-side route 404s on Vercel's static host on direct navigation (refresh, shared link) even though in-app navigation works fine. Do not remove it as "unused config."
3. The root-level `Dockerfile` calls into the Makefile (`make pipeline-all PYTHON=python3`, `make serve PYTHON=python3`) rather than re-implementing pipeline or server invocation — same "don't duplicate the Makefile's logic" principle already applied to `playwright.config.js`'s `webServer`. If the Makefile's `pipeline-all` or `serve` targets change, the Dockerfile picks it up automatically; don't let the two drift by hardcoding steps in one place.
4. `make serve` (production: binds `$PORT`, no `--reload`) is distinct from `make server` (dev: fixed port 8000, `--reload`). Don't merge them — Render needs the dynamic port binding and must never run with `--reload`.
5. `backend/data/raw/` is tracked in git (run `git ls-files backend/data/raw | wc -l` to confirm — it'll be thousands of files) despite `.gitignore` listing that path. This is the current deliberate state: it's what lets the Render Docker build run `make pipeline-all` with zero network access to StatFin or vaalit.fi. Do not "clean this up" by untracking the directory without also changing the Dockerfile to call `make ingest elections-ingest pipeline-all` instead — that would make every deploy depend on live scraping access to vaalit.fi, which is slower and far more likely to fail a build.
6. Corollary to #5: if you re-run `make ingest` or `make elections-ingest` to refresh the data, the new timestamped raw files will **not** be picked up by a plain `git add` because of the `.gitignore` rule — you'd need `git add -f`, and you should consider whether old stale raw snapshots in the same directory should be removed first (the pipeline doesn't do this automatically).
7. The cold-start loading/error state in `App.jsx` (`datasetsLoading`/`datasetsError`) exists because Render's free tier sleeps after inactivity and the first request can take ~60s. Don't remove it as unnecessary UI complexity — it's specifically there for that case, not typical latency.
8. If CORS errors appear only on the deployed site (never locally), check `ALLOWED_ORIGINS` on Render matches the *current* Vercel production URL exactly (scheme + host, no trailing slash) before assuming it's a code bug.
