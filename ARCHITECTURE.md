# InsightKartta Architecture

This document describes the system architecture, data flow, and design decisions behind InsightKartta.

---

## 🧠 High-Level Architecture

```
          ┌───────────────┐
          │ External APIs │
          │ (PXWeb)       │
          └───────┬───────┘
                  │
          ┌───────▼───────┐
          │ Ingestion     │
          └───────┬───────┘
                  │
          ┌───────▼───────┐
          │ Transformation│
          └───────┬───────┘
                  │
          ┌───────▼───────┐
          │ Enrichment    │
          └───────┬───────┘
                  │
          ┌───────▼───────┐
          │ Analysis      │
          └───────┬───────┘
                  │
          ┌───────▼───────┐
          │ FastAPI       │
          └───────┬───────┘
                  │
          ┌───────▼───────┐
          │ React Frontend│
          └───────────────┘
```

---

## 🔄 Data Flow

### 1. Ingestion Layer

* Fetches data from Statistics Finland PXWeb APIs
* Stores raw responses (JSON)
* Designed to be extensible for additional APIs

---

### 2. Transformation Layer

#### PXWebTransformer

* Converts PXWeb format into tabular structure
* Extracts:

  * Dimensions (e.g. region, year)
  * Metrics (e.g. unemployment rate)

#### Dataset-Specific Cleaning

* Normalizes schema:

  * `Alue → region`
  * `Vuosi → year`
* Converts types (e.g. year → int)

---

### 3. Enrichment Layer

* Adds semantic meaning to raw data
* (Currently done inside dataset-specific transforamtion)
* Example:

  * `region_code → region_name`

Uses:

```
data/region_mapping.csv
```

Key responsibilities:

* Mapping codes to human-readable values
* Filtering unsupported regions
* Data validation (detect missing mappings)

---

### 4. Analysis Layer

* Modular analysis engine
* Each analysis:

  * Receives DataFrame
  * Produces structured insights

Example:

* Trend detection
* Statistical summaries

---

### 5. API Layer (FastAPI)

* Serves processed data and analysis results
* Endpoints:

  * `/unemployment`
* Handles:

  * Serialization
  * Data cleaning for JSON compatibility

---

### 6. Frontend Layer (React)

#### Responsibilities:

* Fetch data from API
* Render:

  * Charts (Recharts)
  * Map (React Leaflet)

#### Map Integration:

* GeoJSON (Finland regions)
* Dynamic styling based on data
* Time slider for temporal exploration

---

## 🧱 Key Design Decisions

### 1. Separation of Concerns

* Each layer has a single responsibility
* Improves maintainability and extensibility

---

### 2. Mapping as Data (Not Code)

* Region mappings stored in CSV
* Avoids hardcoding
* Enables easy updates and auditing

---

### 3. Generic Transformer

* PXWebTransformer is dataset-agnostic
* Enables reuse across multiple datasets

---

### 4. Explicit Data Validation

* Missing mappings are logged
* Invalid data is filtered out

---

## ⚠️ Known Challenges

* Region codes differ across datasets
* Mapping must be maintained manually or derived from metadata
* GeoJSON uses names, APIs use codes → requires mapping layer

---

## 🚀 Future Architecture Improvements

* Introduce pipeline orchestration (e.g. DAG-style execution)
* Add caching layer for API responses
* Introduce database (PostgreSQL)
* Add data validation framework
* Support multiple datasets dynamically

---

## 🧠 Summary

InsightKartta is designed as a modular data platform:

* Data pipeline → clean, structured data
* Analysis layer → insights
* API → delivery
* Frontend → exploration

This architecture ensures scalability, maintainability, and extensibility for future development.

---
