# InsightKartta Instructions

This file exists to prevent repeated mistakes, avoid unnecessary delays, and preserve the intended architecture.

Read this before adding or changing datasets, backend pipeline logic, API behavior, or frontend visualizations.

---

## 1. General rules

1. Preserve the config-driven architecture.
2. Prefer generic pipeline steps over dataset-specific code.
3. Do not introduce one-off hacks into the frontend if the problem belongs in the backend or config.
4. Keep the frontend generic.
5. Keep metadata complete and explicit.
6. Be careful with geography level alignment.
7. Do not reintroduce outdated assumptions such as parquet-only paths or unemployment-only endpoints.

---

## 2. Before adding a new dataset

Before implementing a new dataset, verify all of the following:

- the StatFin endpoint is correct
- the PXWeb payload actually works
- the geography level is understood
- the metric to normalize into `value` is identified
- the frontend label and unit are known
- the map bins are at least initially defined

Do not proceed with a partial dataset definition if these basics are unknown.

---

## 3. Every dataset entry in `datasets.yaml` must include

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
- `unit`
- `visualization.map.bins`

Do not omit visualization metadata just because the dataset ingests successfully.

---

## 4. Mandatory dataset checklist

When adding a dataset, confirm:

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
- unit is correct
- bins make sense for the value range

---

## 5. Things to remember about transformation

1. New datasets should need as little custom code as possible.
2. If a dataset only needs:
   - `Alue -> region`
   - `Vuosi -> year`
   - one metric rename
   - `year -> int`
   then do not create a dataset-specific cleaning module unless there is a real need.
3. Prefer the generic config-driven transformation flow.
4. Keep dataset-specific transformation files only for genuinely unusual cases.

### Important
Remember to add the `rename` section and `value_column` section with the right values, so transformation does not fail with new datasets.

This has already caused failures.

---

## 6. Things to remember about metadata

Metadata is not optional.

Always remember to add all necessary metadata.

At minimum:
- `label`
- `unit`
- `visualization.map.bins`

Without metadata:
- chart titles become weak or wrong
- units disappear
- map colors and legend become misleading or useless

This has already caused frontend problems.

---

## 7. Things to remember about geography

This project depends heavily on matching data geography to GeoJSON geography.

Always verify:
- whether the dataset is municipality-level or region-level
- whether the selected GeoJSON is `kunnat.geojson` or `maakunnat.geojson`
- whether `region_name` matches GeoJSON property names exactly

If the geography does not match:
- the map may render with no colors
- tooltips may say `No data`
- clicks may not update the chart correctly

Do not treat this as a minor detail.

---

## 8. Frontend rules

1. The frontend should use `value`, not dataset-specific metric names.
2. The frontend should use `meta.label` and `meta.unit`.
3. The frontend should prefer `region_name` over `region` code.
4. The frontend should not hardcode dataset names.
5. The frontend should get the dataset list from `/datasets`.

### Map-specific rules
- do not hardcode unemployment bins
- use metadata-driven bins
- keep legend and color scale in sync
- do not mount Leaflet layers before data is ready
- if tooltips fail to update, remember that `GeoJSON` may need a changing `key`

---

## 9. Backend rules

1. The API should be generic.
2. Do not add old-style dataset-specific endpoints unless absolutely necessary.
3. Processed data loading should use the current CSV-based structure.
4. Do not reintroduce hardcoded parquet assumptions.
5. Keep service logic generic and dataset-driven.

---

## 10. Config rules

### Use YAML anchors for shared large lists
Do not add custom config-loader complexity just to reuse area code lists.

Preferred approach:
- define shared area lists with YAML anchors
- reuse them with aliases inside `datasets.yaml`

Do not build a custom resolver unless there is a strong future need.

---

## 11. Debugging rules

When something fails, check in this order:

1. Is the endpoint correct?
2. Does the PXWeb payload actually return the intended dimensions?
3. Does the transformed DataFrame have the columns expected by config?
4. Does `rename` match actual source column names?
5. Does `value_column` exist after renaming?
6. Is `region_mapping.csv` complete enough?
7. Does `region_name` match the GeoJSON?
8. Does metadata include bins and units?
9. Is the frontend using `value` and `meta`, not old dataset-specific fields?

This order avoids wasting time.

---

## 12. Things not to forget when resuming later

When resuming after a break, explicitly re-check:

- CSV vs parquet assumptions
- current backend structure
- whether API routes are generic
- whether frontend dataset switching still uses metadata correctly
- whether new datasets have full transformation and metadata blocks
- whether map legend/color scale are dataset-aware

---

## 13. Preferred development direction

Good direction:
- more generic
- more declarative
- more metadata-driven
- less repetition
- fewer one-off exceptions

Bad direction:
- hardcoding special cases into the frontend
- adding custom loaders when YAML can already solve the problem
- adding dataset-specific cleaning for trivial rename/type tasks
- skipping metadata because “it works for now”
- ignoring geography mismatches

---

## 14. Final reminder

The project should feel like a coherent data platform.

Before merging any change, ask:

- does this reduce or increase repetition?
- does this preserve the generic frontend contract?
- does this preserve the config-driven backend?
- does this make adding the next dataset easier or harder?

If it makes the next dataset harder, it is probably the wrong change.
